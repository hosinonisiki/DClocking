"""Local experiment notebook workspace for DClocking.

The workbench deliberately treats a "repository" as a local directory.  It
does not initialize Git or perform any network operation; users keep complete
control over whether their experiment records are versioned or shared.
"""

from __future__ import annotations

import ctypes
import fcntl
import hashlib
import os
import re
import secrets
import stat
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    QByteArray,
    QDir,
    QSettings,
    QSortFilterProxyModel,
    QStandardPaths,
    Qt,
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFileSystemModel,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class _ExternalModificationError(OSError):
    def __init__(self, message, recovery_name=None):
        super().__init__(message)
        self.recovery_name = recovery_name


class _CommitUncertainError(OSError):
    def __init__(self, recovery_name):
        super().__init__("原文件回滚失败，已保留可见恢复副本")
        self.recovery_name = recovery_name


class _SafeMarkdownPreview(QTextBrowser):
    """Text-only preview that never follows links or loads local resources."""

    def loadResource(self, resource_type, name):  # noqa: N802 - Qt virtual
        return QByteArray()


class _RepositoryProxyModel(QSortFilterProxyModel):
    """Second boundary check for paths exposed by QFileSystemModel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._repository_root = None

    def set_repository_root(self, root):
        if hasattr(self, "beginFilterChange"):
            self.beginFilterChange()
            self._repository_root = Path(root) if root else None
            self.endFilterChange()
        else:
            self._repository_root = Path(root) if root else None
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):  # noqa: N802 - Qt virtual
        source = self.sourceModel()
        if source is None or self._repository_root is None:
            return False
        index = source.index(source_row, 0, source_parent)
        path = Path(source.filePath(index))
        try:
            if path.is_symlink():
                return False
            resolved = path.resolve(strict=False)
            try:
                resolved.relative_to(self._repository_root)
            except ValueError:
                # QFileSystemModel's ancestor chain must remain mappable even
                # though the view is rooted at (and cannot display above) the
                # selected repository.
                self._repository_root.relative_to(resolved)
        except (OSError, ValueError):
            return False
        return super().filterAcceptsRow(source_row, source_parent)


class ExperimentWorkbench(QDialog):
    """Non-modal editor for UTF-8 experiment notes stored in one local root."""

    SUPPORTED_SUFFIXES = {".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".log"}
    MAX_FILE_BYTES = 5 * 1024 * 1024
    SETTINGS_ROOT_KEY = "experiment_workspace/root"
    SETTINGS_SPLITTER_KEY = "experiment_workspace/splitter"

    def __init__(self, settings=None, default_root=None, parent=None):
        super().__init__(parent)
        self._settings = settings or QSettings("DClocking", "PrecisionWorkstation")
        self._default_root = Path(default_root).expanduser() if default_root else self.default_repository_path()
        self.repository_root: Path | None = None
        self._root_fd: int | None = None
        self.current_path: Path | None = None
        self._opened_snapshot = None
        self._loading_document = False
        self._dirty = False
        self._close_without_prompt = False

        self.setObjectName("experiment_workbench")
        self.setAccessibleName("实验记录工作台")
        self.setWindowTitle("实验记录工作台 · DClocking")
        self.setModal(False)
        self.setMinimumSize(980, 640)
        self.resize(1380, 820)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_header())
        root_layout.addWidget(self._build_body(), 1)
        root_layout.addWidget(self._build_status_bar())

        self.save_action = QAction("保存实验记录", self)
        self.save_action.setObjectName("experiment_save_action")
        self.save_action.setShortcut(QKeySequence.Save)
        self.save_action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self.save_action.triggered.connect(self.save_document)
        self.addAction(self.save_action)

        saved_root = self._settings.value(self.SETTINGS_ROOT_KEY, "")
        initial_root = Path(str(saved_root)).expanduser() if saved_root else self._default_root
        if not self.set_repository_root(initial_root, prompt_unsaved=False, show_errors=False):
            self.set_repository_root(self._default_root, prompt_unsaved=False)
        splitter_state = self._settings.value(self.SETTINGS_SPLITTER_KEY)
        if splitter_state:
            self.body_splitter.restoreState(splitter_state)
        self._update_document_state()

        self.setStyleSheet(
            "#experiment_header { background: #FFFFFF; border-bottom: 1px solid #D8D4CE; }"
            "#experiment_title { color: #243447; font-size: 17px; font-weight: 750; letter-spacing: 1px; }"
            "#experiment_chip { color: #8F123D; background: #F5E6EB; border: 1px solid #E5C7D2; "
            "border-radius: 9px; padding: 3px 9px; font-size: 10px; font-weight: 650; }"
            "#experiment_repo_path { color: #5F6976; font-family: Menlo; font-size: 10px; }"
            "#experiment_tree_panel, #experiment_editor_panel, #experiment_preview_panel { background: #FBFBF9; }"
            "#experiment_editor { background: #FFFFFF; color: #303438; border: 1px solid #D8D4CE; "
            "border-radius: 7px; padding: 12px; font-family: Menlo; font-size: 13px; }"
            "#experiment_preview { background: #FFFFFF; color: #303438; border: 1px solid #D8D4CE; "
            "border-radius: 7px; padding: 12px; }"
            "#experiment_status_bar { background: #F2F0ED; border-top: 1px solid #D8D4CE; }"
            "#experiment_dirty_status { color: #8F123D; font-weight: 650; }"
        )

    @staticmethod
    def default_repository_path() -> Path:
        documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        base = Path(documents) if documents else Path.home() / "Documents"
        return base / "DClocking实验记录"

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def _build_header(self):
        header = QWidget(self)
        header.setObjectName("experiment_header")
        header.setFixedHeight(88)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(10)

        identity = QVBoxLayout()
        title_row = QHBoxLayout()
        title = QLabel("EXPERIMENT RECORD WORKBENCH", header)
        title.setObjectName("experiment_title")
        chip = QLabel("LOCAL REPOSITORY · MARKDOWN", header)
        chip.setObjectName("experiment_chip")
        title_row.addWidget(title)
        title_row.addWidget(chip)
        title_row.addStretch()
        identity.addLayout(title_row)
        self.repository_label = QLabel("", header)
        self.repository_label.setObjectName("experiment_repo_path")
        self.repository_label.setAccessibleName("当前实验仓库")
        identity.addWidget(self.repository_label)
        layout.addLayout(identity, 1)

        self.switch_root_button = QPushButton("切换仓库", header)
        self.switch_root_button.setObjectName("experiment_switch_repository_button")
        self.switch_root_button.setAccessibleName("切换实验记录仓库")
        self.new_record_button = QPushButton("新建实验记录", header)
        self.new_record_button.setObjectName("experiment_new_record_button")
        self.save_button = QPushButton("保存", header)
        self.save_button.setObjectName("experiment_save_button")
        self.save_button.setProperty("variant", "primary")
        self.save_button.setAccessibleName("保存当前实验记录")
        layout.addWidget(self.switch_root_button)
        layout.addWidget(self.new_record_button)
        layout.addWidget(self.save_button)

        self.switch_root_button.clicked.connect(self.choose_repository)
        self.new_record_button.clicked.connect(self._new_record_clicked)
        self.save_button.clicked.connect(self.save_document)
        return header

    def _build_body(self):
        self.body_splitter = QSplitter(Qt.Horizontal, self)
        self.body_splitter.setObjectName("experiment_splitter")
        self.body_splitter.setChildrenCollapsible(False)

        tree_panel = QWidget(self.body_splitter)
        tree_panel.setObjectName("experiment_tree_panel")
        tree_panel.setMinimumWidth(230)
        tree_panel.setMaximumWidth(360)
        tree_layout = QVBoxLayout(tree_panel)
        tree_layout.setContentsMargins(14, 14, 10, 14)
        tree_layout.setSpacing(8)
        eyebrow = QLabel("LOCAL REPOSITORY", tree_panel)
        eyebrow.setProperty("role", "eyebrow")
        tree_layout.addWidget(eyebrow)
        tree_title = QLabel("实验文件", tree_panel)
        tree_title.setProperty("role", "sectionTitle")
        tree_layout.addWidget(tree_title)
        self.file_model = QFileSystemModel(tree_panel)
        self.file_model.setFilter(
            QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot | QDir.NoSymLinks
        )
        self.file_model.setReadOnly(True)
        self.file_model.setNameFilters([f"*{suffix}" for suffix in sorted(self.SUPPORTED_SUFFIXES)])
        self.file_model.setNameFilterDisables(False)
        self.file_proxy = _RepositoryProxyModel(tree_panel)
        self.file_proxy.setSourceModel(self.file_model)
        self.file_tree = QTreeView(tree_panel)
        self.file_tree.setObjectName("experiment_file_tree")
        self.file_tree.setAccessibleName("实验记录文件树")
        self.file_tree.setModel(self.file_proxy)
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setAnimated(True)
        for column in range(1, 4):
            self.file_tree.hideColumn(column)
        self.file_tree.doubleClicked.connect(self._tree_item_activated)
        tree_layout.addWidget(self.file_tree, 1)
        tree_hint = QLabel("双击打开文本记录。文件访问始终限制在当前仓库内。", tree_panel)
        tree_hint.setWordWrap(True)
        tree_hint.setStyleSheet("color: #72777B; font-size: 10px;")
        tree_layout.addWidget(tree_hint)

        editor_panel = QWidget(self.body_splitter)
        editor_panel.setObjectName("experiment_editor_panel")
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(10, 14, 6, 14)
        editor_layout.setSpacing(8)
        editor_header = QHBoxLayout()
        editor_title = QLabel("EDITOR / UTF-8", editor_panel)
        editor_title.setProperty("role", "eyebrow")
        self.current_file_label = QLabel("未打开文件", editor_panel)
        self.current_file_label.setStyleSheet("color: #5F6976; font-size: 11px;")
        editor_header.addWidget(editor_title)
        editor_header.addStretch()
        editor_header.addWidget(self.current_file_label)
        editor_layout.addLayout(editor_header)
        self.editor = QPlainTextEdit(editor_panel)
        self.editor.setObjectName("experiment_editor")
        self.editor.setAccessibleName("实验记录文本编辑器")
        self.editor.setPlaceholderText("新建或从左侧打开实验记录后，在这里编辑文本…")
        self.editor.setTabStopDistance(32)
        self.editor.setEnabled(False)
        self.editor.textChanged.connect(self._editor_text_changed)
        editor_layout.addWidget(self.editor, 1)

        preview_panel = QWidget(self.body_splitter)
        preview_panel.setObjectName("experiment_preview_panel")
        preview_panel.setMinimumWidth(320)
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(6, 14, 14, 14)
        preview_layout.setSpacing(8)
        preview_header = QHBoxLayout()
        preview_title = QLabel("DOCUMENT PREVIEW", preview_panel)
        preview_title.setProperty("role", "eyebrow")
        self.preview_mode_label = QLabel("MARKDOWN", preview_panel)
        self.preview_mode_label.setStyleSheet("color: #8F123D; font-size: 10px; font-weight: 650;")
        preview_header.addWidget(preview_title)
        preview_header.addStretch()
        preview_header.addWidget(self.preview_mode_label)
        preview_layout.addLayout(preview_header)
        self.preview = _SafeMarkdownPreview(preview_panel)
        self.preview.setObjectName("experiment_preview")
        self.preview.setAccessibleName("实验记录预览")
        self.preview.setOpenExternalLinks(False)
        self.preview.setOpenLinks(False)
        self.preview.setPlaceholderText("Markdown 文档将在这里实时预览")
        preview_layout.addWidget(self.preview, 1)

        self.body_splitter.addWidget(tree_panel)
        self.body_splitter.addWidget(editor_panel)
        self.body_splitter.addWidget(preview_panel)
        self.body_splitter.setStretchFactor(0, 0)
        self.body_splitter.setStretchFactor(1, 1)
        self.body_splitter.setStretchFactor(2, 1)
        self.body_splitter.setSizes([270, 610, 500])
        return self.body_splitter

    def _build_status_bar(self):
        status = QFrame(self)
        status.setObjectName("experiment_status_bar")
        status.setFixedHeight(34)
        layout = QHBoxLayout(status)
        layout.setContentsMargins(14, 0, 14, 0)
        self.document_status_label = QLabel("就绪", status)
        self.document_status_label.setObjectName("experiment_dirty_status")
        self.encoding_label = QLabel("UTF-8", status)
        self.encoding_label.setStyleSheet("color: #72777B; font-family: Menlo; font-size: 10px;")
        layout.addWidget(self.document_status_label)
        layout.addStretch()
        layout.addWidget(self.encoding_label)
        return status

    def set_repository_root(self, root, prompt_unsaved=True, show_errors=True) -> bool:
        if prompt_unsaved and not self.confirm_can_replace_document():
            return False
        new_root_fd = None
        try:
            requested = Path(root).expanduser()
            requested.mkdir(parents=True, exist_ok=True)
            resolved = requested.resolve(strict=True)
            if not resolved.is_dir():
                raise ValueError("选择的位置不是文件夹")
            before = os.stat(resolved, follow_symlinks=False)
            new_root_fd = self._open_absolute_directory_no_symlinks(resolved)
            opened = os.fstat(new_root_fd)
            visible = os.stat(resolved, follow_symlinks=False)
            identities = {
                (before.st_dev, before.st_ino),
                (opened.st_dev, opened.st_ino),
                (visible.st_dev, visible.st_ino),
            }
            if not stat.S_ISDIR(opened.st_mode) or len(identities) != 1:
                os.close(new_root_fd)
                new_root_fd = None
                raise ValueError("仓库路径在打开过程中发生变化，请重新选择")
        except (OSError, ValueError) as exc:
            if new_root_fd is not None:
                os.close(new_root_fd)
            if show_errors:
                QMessageBox.warning(self, "无法打开仓库", str(exc))
            return False

        old_root_fd = self._root_fd
        self.repository_root = resolved
        self._root_fd = new_root_fd
        if old_root_fd is not None:
            os.close(old_root_fd)
        self.current_path = None
        self._opened_snapshot = None
        self._loading_document = True
        self.editor.clear()
        self._loading_document = False
        self._dirty = False
        self.editor.setEnabled(False)
        model_index = self.file_model.setRootPath(str(resolved))
        self.file_proxy.set_repository_root(resolved)
        self.file_tree.setRootIndex(self.file_proxy.mapFromSource(model_index))
        self.repository_label.setText(str(resolved))
        self.repository_label.setToolTip(str(resolved))
        self._settings.setValue(self.SETTINGS_ROOT_KEY, str(resolved))
        self._settings.sync()
        self._update_preview()
        self._update_document_state("仓库已打开")
        return True

    @staticmethod
    def _open_absolute_directory_no_symlinks(path: Path) -> int:
        absolute = Path(path)
        if not absolute.is_absolute():
            raise ValueError("仓库路径必须是绝对路径")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(absolute.anchor, flags)
        try:
            for part in absolute.parts[1:]:
                child = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
        except Exception:
            os.close(descriptor)
            raise
        return descriptor

    def choose_repository(self):
        selected = QFileDialog.getExistingDirectory(
            self,
            "选择实验记录仓库",
            str(self.repository_root or self._default_root),
            QFileDialog.ShowDirsOnly,
        )
        if selected:
            self.set_repository_root(selected)

    def _tree_item_activated(self, index):
        source_index = self.file_proxy.mapToSource(index)
        path = Path(self.file_model.filePath(source_index))
        if path.is_file():
            self.open_document(path)

    @staticmethod
    def _safe_title(title: str) -> str:
        value = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "-", str(title or "").strip())
        value = re.sub(r"\s+", " ", value).strip(" .-")
        return value[:48] or "实验记录"

    def _new_record_clicked(self):
        title, accepted = QInputDialog.getText(self, "新建实验记录", "实验名称：")
        if accepted:
            self.create_record(title)

    def create_record(self, title, when=None) -> Path | None:
        if not self.confirm_can_replace_document():
            return None
        when = when or datetime.now()
        safe_title = self._safe_title(title)
        try:
            root = self._require_repository()
            day_dir = self._secure_day_directory(when.strftime("%Y-%m-%d"))
            base = day_dir / f"{when:%H%M}-{safe_title}.md"
            content = self._record_template(safe_title, when)
            with self._repository_write_lock():
                path = base
                ordinal = 2
                while True:
                    try:
                        self._atomic_write_text(path, content, exclusive=True)
                        break
                    except FileExistsError:
                        path = base.with_name(f"{base.stem}-{ordinal}{base.suffix}")
                        ordinal += 1
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "无法新建实验记录", str(exc))
            return None
        self.open_document(path, prompt_unsaved=False)
        return path

    @staticmethod
    def _record_template(title: str, when: datetime) -> str:
        return (
            f"# {title}\n\n"
            f"- 日期：{when:%Y-%m-%d %H:%M}\n"
            "- 实验人员：\n"
            "- 设备与配置：\n\n"
            "## 实验目的\n\n"
            "\n"
            "## 实验步骤\n\n"
            "1. \n\n"
            "## 实验数据\n\n"
            "| 序号 | 参数 | 测量值 | 单位 | 备注 |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| 1 |  |  |  |  |\n\n"
            "## 现象与分析\n\n"
            "\n"
            "## 实验结论\n\n"
        )

    def _relative_parts(self, path: Path) -> tuple[str, ...]:
        root = self._require_repository()
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = Path(os.path.abspath(os.fspath(candidate)))
        try:
            relative = candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("文件不在当前实验仓库内") from exc
        if not relative.parts or any(part in ("", ".", "..") for part in relative.parts):
            raise ValueError("实验文件路径无效")
        return relative.parts

    def _require_repository(self) -> Path:
        if self.repository_root is None:
            raise ValueError("实验仓库尚未初始化，请先切换仓库")
        if self._root_fd is None:
            raise ValueError("当前实验仓库不可用，请重新选择仓库")
        try:
            descriptor = os.fstat(self._root_fd)
            visible = os.stat(self.repository_root, follow_symlinks=False)
        except OSError as exc:
            raise ValueError("当前实验仓库不可用，请重新选择仓库") from exc
        if (
            not stat.S_ISDIR(descriptor.st_mode)
            or not stat.S_ISDIR(visible.st_mode)
            or (descriptor.st_dev, descriptor.st_ino) != (visible.st_dev, visible.st_ino)
        ):
            raise ValueError("当前实验仓库不可用，请重新选择仓库")
        return self.repository_root

    def _open_parent_fd(self, path: Path):
        parts = self._relative_parts(path)
        descriptor = os.dup(self._root_fd)
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            for part in parts[:-1]:
                child = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
        except Exception:
            os.close(descriptor)
            raise
        return descriptor, parts[-1], self.repository_root.joinpath(*parts)

    def _secure_day_directory(self, name: str) -> Path:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", name):
            raise ValueError("实验记录日期目录无效")
        return self._secure_repository_directory(name)

    def _secure_repository_directory(self, name: str) -> Path:
        if not name or name in (".", "..") or "/" in name or "\x00" in name:
            raise ValueError("实验记录目录名称无效")
        self._require_repository()
        try:
            os.mkdir(name, mode=0o700, dir_fd=self._root_fd)
        except FileExistsError:
            pass
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(name, flags, dir_fd=self._root_fd)
        try:
            if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise ValueError("实验记录日期路径不是安全目录")
        finally:
            os.close(descriptor)
        return self.repository_root / name

    @contextmanager
    def _repository_write_lock(self):
        self._require_repository()
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(
            ".dclocking-experiment.lock", flags, 0o600, dir_fd=self._root_fd
        )
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise OSError("另一个 DClocking 工作台正在保存，请稍后重试") from exc
            try:
                yield
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def _read_open_fd(self, descriptor):
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("选择的路径不是普通文件")
        if before.st_size > self.MAX_FILE_BYTES:
            raise ValueError("文件超过 5 MiB，已拒绝在编辑器中打开")
        chunks = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(64 * 1024, self.MAX_FILE_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > self.MAX_FILE_BYTES:
                raise ValueError("文件超过 5 MiB，已拒绝在编辑器中打开")
        after = os.fstat(descriptor)
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        if identity_before != identity_after:
            raise OSError("文件在读取过程中被修改，请重试")
        payload = b"".join(chunks)
        snapshot = (*identity_after, hashlib.sha256(payload).hexdigest())
        return payload, snapshot

    def _read_document(self, path: Path):
        parts = self._relative_parts(path)
        shown_path = self.repository_root.joinpath(*parts)
        if shown_path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            raise ValueError("仅支持 Markdown、TXT、CSV、JSON、YAML 和日志文本")
        parent_fd, name, shown_path = self._open_parent_fd(shown_path)
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(name, flags, dir_fd=parent_fd)
            try:
                payload, snapshot = self._read_open_fd(descriptor)
            finally:
                os.close(descriptor)
        finally:
            os.close(parent_fd)
        if b"\x00" in payload:
            raise ValueError("检测到二进制内容，无法作为实验文本打开")
        try:
            text = payload.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("文件不是有效的 UTF-8 文本") from exc
        return shown_path, text, snapshot

    def open_document(self, path, prompt_unsaved=True) -> bool:
        if prompt_unsaved and not self.confirm_can_replace_document():
            return False
        try:
            resolved, text, snapshot = self._read_document(Path(path))
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "无法打开实验文件", str(exc))
            return False
        self.current_path = resolved
        self._opened_snapshot = snapshot
        self._loading_document = True
        self.editor.setPlainText(text)
        self._loading_document = False
        self._dirty = False
        self.editor.setEnabled(True)
        self._update_preview()
        self._update_document_state("已打开")
        return True

    def _atomic_write_text(
        self,
        path: Path,
        text: str,
        *,
        exclusive=False,
        expected_snapshot=None,
    ):
        payload = text.encode("utf-8")
        if len(payload) > self.MAX_FILE_BYTES:
            raise ValueError("实验记录超过 5 MiB，已拒绝保存")
        try:
            parent_fd, name, target = self._open_parent_fd(path)
        except (OSError, ValueError) as exc:
            if expected_snapshot is not None:
                raise _ExternalModificationError("原文件目录已不可用") from exc
            raise
        temp_name = f".experiment_{secrets.token_hex(12)}.tmp"
        temp_fd = None
        published = False
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            temp_fd = os.open(temp_name, flags, 0o600, dir_fd=parent_fd)
            view = memoryview(payload)
            while view:
                written = os.write(temp_fd, view)
                if written <= 0:
                    raise OSError("实验记录写入不完整")
                view = view[written:]
            os.fsync(temp_fd)
            temp_stat = os.fstat(temp_fd)
            local_temp_snapshot = (
                temp_stat.st_dev,
                temp_stat.st_ino,
                temp_stat.st_size,
                temp_stat.st_mtime_ns,
                hashlib.sha256(payload).hexdigest(),
            )
            os.close(temp_fd)
            temp_fd = None

            if expected_snapshot is not None:
                exchanged = False
                temp_contains_local_copy = True
                try:
                    self._exchange_names(parent_fd, temp_name, name)
                    exchanged = True
                    temp_contains_local_copy = False
                    current_fd = os.open(
                        temp_name,
                        os.O_RDONLY
                        | getattr(os, "O_CLOEXEC", 0)
                        | getattr(os, "O_NOFOLLOW", 0),
                        dir_fd=parent_fd,
                    )
                    try:
                        _current_payload, current_snapshot = self._read_open_fd(current_fd)
                    finally:
                        os.close(current_fd)
                    if current_snapshot != expected_snapshot:
                        self._exchange_names(parent_fd, temp_name, name)
                        exchanged = False
                        temp_contains_local_copy = False
                        recovery_name = self._verify_or_preserve_rollback_entry(
                            parent_fd,
                            temp_name,
                            name,
                            local_temp_snapshot,
                        )
                        temp_contains_local_copy = recovery_name is None
                        raise _ExternalModificationError(
                            "文件已在外部修改",
                            recovery_name=recovery_name,
                        )
                    # Persist the exchange while temp_name still retains the
                    # previous target. If this fails, rollback remains possible.
                    os.fsync(parent_fd)
                    os.unlink(temp_name, dir_fd=parent_fd)
                    exchanged = False
                    published = True
                    return target
                except _ExternalModificationError:
                    raise
                except (OSError, ValueError, NotImplementedError) as exc:
                    if exchanged:
                        try:
                            self._exchange_names(parent_fd, temp_name, name)
                        except OSError as rollback_error:
                            recovery_name = self._publish_retained_original(
                                parent_fd, temp_name, name
                            )
                            temp_contains_local_copy = False
                            raise _CommitUncertainError(recovery_name) from rollback_error
                        else:
                            temp_contains_local_copy = False
                            recovery_name = self._verify_or_preserve_rollback_entry(
                                parent_fd,
                                temp_name,
                                name,
                                local_temp_snapshot,
                            )
                            temp_contains_local_copy = recovery_name is None
                            if recovery_name is not None:
                                raise _ExternalModificationError(
                                    "回滚期间检测到新的外部修改",
                                    recovery_name=recovery_name,
                                )
                    raise _ExternalModificationError(
                        "无法安全核验并更新原文件"
                    ) from exc
                finally:
                    if not temp_contains_local_copy:
                        published = True

            if exclusive:
                os.link(
                    temp_name,
                    name,
                    src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                os.unlink(temp_name, dir_fd=parent_fd)
            else:
                existing = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                if not stat.S_ISREG(existing.st_mode):
                    raise ValueError("目标路径不是普通文件，已拒绝覆盖")
                os.replace(
                    temp_name,
                    name,
                    src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd,
                )
            published = True
            os.fsync(parent_fd)
        finally:
            if temp_fd is not None:
                os.close(temp_fd)
            if not published:
                try:
                    os.unlink(temp_name, dir_fd=parent_fd)
                except FileNotFoundError:
                    pass
            os.close(parent_fd)
        return target

    def _verify_or_preserve_rollback_entry(
        self,
        parent_fd: int,
        temp_name: str,
        target_name: str,
        local_snapshot,
    ):
        """Return None only when temp_name is still exactly our local temp file."""
        try:
            descriptor = os.open(
                temp_name,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_fd,
            )
            try:
                _payload, snapshot = self._read_open_fd(descriptor)
            finally:
                os.close(descriptor)
        except (OSError, ValueError):
            return self._publish_retained_original(parent_fd, temp_name, target_name)
        if snapshot == local_snapshot:
            return None
        return self._publish_retained_original(parent_fd, temp_name, target_name)

    @staticmethod
    def _publish_retained_original(parent_fd: int, temp_name: str, target_name: str):
        target = Path(target_name)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base = f"{target.stem}-原版本恢复-{stamp}{target.suffix}"
        recovery_name = base
        ordinal = 2
        while True:
            try:
                os.link(
                    temp_name,
                    recovery_name,
                    src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                break
            except FileExistsError:
                recovery_name = f"{Path(base).stem}-{ordinal}{target.suffix}"
                ordinal += 1
        os.unlink(temp_name, dir_fd=parent_fd)
        os.fsync(parent_fd)
        return recovery_name

    @staticmethod
    def _exchange_names(parent_fd: int, first: str, second: str):
        """Atomically swap two directory entries without discarding either one."""
        if sys.platform != "darwin":
            raise NotImplementedError("当前系统不支持安全原位更新")
        libc = ctypes.CDLL(None, use_errno=True)
        renameatx_np = getattr(libc, "renameatx_np", None)
        if renameatx_np is None:
            raise NotImplementedError("系统缺少 renameatx_np")
        renameatx_np.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        renameatx_np.restype = ctypes.c_int
        rename_swap = 0x00000002
        result = renameatx_np(
            parent_fd,
            os.fsencode(first),
            parent_fd,
            os.fsencode(second),
            rename_swap,
        )
        if result != 0:
            error_number = ctypes.get_errno()
            raise OSError(error_number, os.strerror(error_number))

    def save_document(self) -> bool:
        if self.current_path is None:
            self._update_document_state("请先新建或打开实验记录")
            return False
        editor_text = self.editor.toPlainText()
        try:
            with self._repository_write_lock():
                target = self._atomic_write_text(
                    self.current_path,
                    editor_text,
                    expected_snapshot=self._opened_snapshot,
                )
        except _CommitUncertainError as exc:
            self._dirty = True
            self._update_document_state("保存状态需要检查")
            QMessageBox.warning(
                self,
                "保存状态需要检查",
                "系统未能自动回滚原文件。当前编辑版本已位于原文件路径，"
                f"原版本已另存为：\n{exc.recovery_name}\n\n请检查两个文件后再继续。",
            )
            return False
        except _ExternalModificationError as exc:
            recovery_note = (
                f"\n\n回滚期间出现的外部版本已另存为：{exc.recovery_name}"
                if exc.recovery_name
                else ""
            )
            answer = QMessageBox.question(
                self,
                "检测到外部修改",
                "原文件已被其他程序修改。为避免覆盖外部数据，是否将当前内容保存为冲突副本？"
                + recovery_note,
                QMessageBox.Save | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if answer != QMessageBox.Save:
                return False
            try:
                with self._repository_write_lock():
                    target = self._save_conflict_copy()
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, "保存失败", str(exc))
                return False
            self.open_document(target, prompt_unsaved=False)
            QMessageBox.information(
                self,
                "已保存冲突副本",
                f"原文件未被覆盖。当前内容已安全保存为：\n{target.name}",
            )
            return True
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return False
        try:
            resolved, disk_text, snapshot = self._read_document(target)
        except (OSError, ValueError) as exc:
            return self._recover_after_save_race(str(exc))
        if disk_text != editor_text:
            return self._recover_after_save_race("磁盘内容在保存后再次发生变化")
        self.current_path = resolved
        self._opened_snapshot = snapshot
        self._dirty = False
        self._update_document_state("已保存")
        return True

    def _recover_after_save_race(self, reason: str) -> bool:
        try:
            with self._repository_write_lock():
                target = self._save_conflict_copy()
        except (OSError, ValueError) as exc:
            self._dirty = True
            self._update_document_state("保存后校验失败")
            QMessageBox.warning(
                self,
                "保存后校验失败",
                f"{reason}\n\n当前编辑内容仍保留在窗口中，但恢复副本保存失败：{exc}",
            )
            return False
        self.open_document(target, prompt_unsaved=False)
        QMessageBox.information(
            self,
            "已保存恢复副本",
            f"{reason}\n\n当前内容已另外保存为：\n{target.name}",
        )
        return True

    def _save_conflict_copy(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base = self.current_path.with_name(
            f"{self.current_path.stem}-冲突副本-{stamp}{self.current_path.suffix}"
        )
        try:
            return self._write_numbered_conflict_copy(base)
        except (OSError, ValueError):
            recovery_dir = self._secure_repository_directory("恢复记录")
            recovery_base = recovery_dir / base.name
            return self._write_numbered_conflict_copy(recovery_base)

    def _write_numbered_conflict_copy(self, base: Path) -> Path:
        candidate = base
        ordinal = 2
        while True:
            try:
                return self._atomic_write_text(
                    candidate,
                    self.editor.toPlainText(),
                    exclusive=True,
                )
            except FileExistsError:
                candidate = base.with_name(f"{base.stem}-{ordinal}{base.suffix}")
                ordinal += 1

    def _editor_text_changed(self):
        if self._loading_document:
            return
        if self.current_path is not None:
            self._dirty = True
        self._update_preview()
        self._update_document_state()

    def _update_preview(self):
        text = self.editor.toPlainText()
        if self.current_path is not None and self.current_path.suffix.lower() == ".md":
            self.preview_mode_label.setText("MARKDOWN")
            self.preview.setMarkdown(text)
        else:
            self.preview_mode_label.setText("PLAIN TEXT")
            self.preview.setPlainText(text)

    def _update_document_state(self, message=None):
        if self.current_path is None:
            self.current_file_label.setText("未打开文件")
        else:
            try:
                shown = self.current_path.relative_to(self.repository_root).as_posix()
            except (TypeError, ValueError):
                shown = self.current_path.name
            self.current_file_label.setText(("● " if self._dirty else "") + shown)
            self.current_file_label.setToolTip(str(self.current_path))
        if message:
            status = message
        elif self._dirty:
            status = "● 有未保存修改"
        elif self.current_path is not None:
            status = "已保存"
        else:
            status = "就绪"
        self.document_status_label.setText(status)
        self.save_button.setEnabled(self.current_path is not None)

    def confirm_can_replace_document(self) -> bool:
        if not self._dirty:
            return True
        answer = QMessageBox.question(
            self,
            "保存实验记录",
            "当前实验记录尚未保存，是否先保存修改？",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if answer == QMessageBox.Save:
            return self.save_document()
        if answer == QMessageBox.Discard:
            self._discard_changes()
            return True
        return False

    def _discard_changes(self):
        if self.current_path is None:
            self._loading_document = True
            self.editor.clear()
            self._loading_document = False
            self._dirty = False
            self.editor.setEnabled(False)
            self._update_preview()
            self._update_document_state("已放弃修改")
            return
        try:
            resolved, text, snapshot = self._read_document(self.current_path)
        except (OSError, ValueError):
            self.current_path = None
            self._opened_snapshot = None
            self._loading_document = True
            self.editor.clear()
            self._loading_document = False
            self.editor.setEnabled(False)
        else:
            self.current_path = resolved
            self._opened_snapshot = snapshot
            self._loading_document = True
            self.editor.setPlainText(text)
            self._loading_document = False
            self.editor.setEnabled(True)
        self._dirty = False
        self._update_preview()
        self._update_document_state("已放弃修改")

    def close_from_parent(self) -> bool:
        if not self._close_without_prompt and not self.confirm_can_replace_document():
            return False
        self._close_without_prompt = True
        self.close()
        self._close_root_descriptor()
        return True

    def _close_root_descriptor(self):
        if self._root_fd is not None:
            os.close(self._root_fd)
            self._root_fd = None

    def _save_ui_state(self):
        self._settings.setValue(self.SETTINGS_SPLITTER_KEY, self.body_splitter.saveState())
        self._settings.sync()

    def closeEvent(self, event):
        if not self._close_without_prompt and not self.confirm_can_replace_document():
            event.ignore()
            return
        self._save_ui_state()
        event.accept()

    def __del__(self):
        try:
            self._close_root_descriptor()
        except OSError:
            pass
