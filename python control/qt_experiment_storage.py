"""Portable fallback storage backend for local experiment repositories.

The descriptor-based implementation in ``qt_experiment_workbench`` remains
the hardened macOS backend, while Windows uses its dedicated Win32 handle
backend.  This path-based Qt implementation is retained for non-production
portable CI and platforms without either native backend.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat

from PySide6.QtCore import QByteArray, QIODevice, QLockFile, QSaveFile


class PortableStorageExternalModificationError(OSError):
    pass


class PortableExperimentRepository:
    """Best-effort path-based fallback for portable CI tests."""

    LOCK_NAME = ".dclocking-experiment.lock"

    def __init__(self, max_file_bytes: int):
        self.max_file_bytes = int(max_file_bytes)
        self.root: Path | None = None
        self._root_identity: tuple[int, int] | None = None

    def close(self) -> None:
        """Match the Windows backend lifecycle; this backend owns no handles."""

    @staticmethod
    def _is_reparse_or_symlink(path: Path, info=None) -> bool:
        info = info or os.lstat(path)
        attributes = int(getattr(info, "st_file_attributes", 0))
        reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
        return stat.S_ISLNK(info.st_mode) or bool(attributes & reparse_flag)

    @staticmethod
    def _identity(info) -> tuple[int, int]:
        return int(info.st_dev), int(info.st_ino)

    def set_root(self, root) -> Path:
        requested = Path(root).expanduser()
        requested.mkdir(parents=True, exist_ok=True)
        requested_info = os.lstat(requested)
        if self._is_reparse_or_symlink(requested, requested_info):
            raise ValueError("实验仓库不能是符号链接或 Windows 重解析点")
        resolved = requested.resolve(strict=True)
        if not resolved.is_dir():
            raise ValueError("选择的位置不是文件夹")
        info = os.lstat(resolved)
        if not stat.S_ISDIR(info.st_mode) or self._is_reparse_or_symlink(resolved, info):
            raise ValueError("实验仓库必须是安全的本地目录")
        self.root = resolved
        self._root_identity = self._identity(info)
        return resolved

    def require_root(self) -> Path:
        if self.root is None or self._root_identity is None:
            raise ValueError("实验仓库尚未初始化，请先切换仓库")
        try:
            info = os.lstat(self.root)
        except OSError as exc:
            raise ValueError("当前实验仓库不可用，请重新选择仓库") from exc
        if (
            not stat.S_ISDIR(info.st_mode)
            or self._is_reparse_or_symlink(self.root, info)
            or self._identity(info) != self._root_identity
        ):
            raise ValueError("当前实验仓库不可用，请重新选择仓库")
        return self.root

    def relative_parts(self, path) -> tuple[str, ...]:
        root = self.require_root()
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

    def _validate_path(self, path, *, leaf_may_be_missing=False) -> Path:
        root = self.require_root()
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = Path(os.path.abspath(os.fspath(candidate)))
        if candidate == root:
            return root
        parts = self.relative_parts(path)
        current = root
        for index, part in enumerate(parts):
            current = current / part
            is_leaf = index == len(parts) - 1
            try:
                info = os.lstat(current)
            except FileNotFoundError:
                if is_leaf and leaf_may_be_missing:
                    return current
                raise
            if self._is_reparse_or_symlink(current, info):
                raise ValueError("实验仓库内不允许符号链接或 Windows 重解析点")
            if not is_leaf and not stat.S_ISDIR(info.st_mode):
                raise ValueError("实验文件父路径不是文件夹")
        return current

    def ensure_directory(self, name: str) -> Path:
        root = self.require_root()
        if not name or name in (".", "..") or any(mark in name for mark in ("/", "\\", "\x00")):
            raise ValueError("实验记录目录名称无效")
        target = root / name
        try:
            target.mkdir(mode=0o700)
        except FileExistsError:
            pass
        validated = self._validate_path(target)
        if not validated.is_dir():
            raise ValueError("实验记录日期路径不是安全目录")
        return validated

    @contextmanager
    def write_lock(self):
        root = self.require_root()
        lock_path = root / self.LOCK_NAME
        if lock_path.exists() or lock_path.is_symlink():
            validated = self._validate_path(lock_path)
            info = os.lstat(validated)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("实验仓库锁文件不是普通文件")
        lock = QLockFile(str(lock_path))
        lock.setStaleLockTime(30_000)
        if not lock.tryLock(0):
            raise OSError("另一个 DClocking 工作台正在保存，请稍后重试")
        try:
            # QLockFile created the path; validate it after ownership too.
            self._validate_path(lock_path)
            yield
        finally:
            lock.unlock()

    def _read_payload(self, path: Path):
        target = self._validate_path(path)
        before = os.lstat(target)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("选择的路径不是普通文件")
        if before.st_size > self.max_file_bytes:
            raise ValueError("文件超过 5 MiB，已拒绝在编辑器中打开")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        descriptor = os.open(target, flags)
        try:
            opened = os.fstat(descriptor)
            if self._identity(opened) != self._identity(before):
                raise OSError("文件在打开过程中被替换，请重试")
            chunks = []
            total = 0
            while True:
                chunk = os.read(
                    descriptor,
                    min(64 * 1024, self.max_file_bytes + 1 - total),
                )
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > self.max_file_bytes:
                    raise ValueError("文件超过 5 MiB，已拒绝在编辑器中打开")
            after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        visible = os.lstat(target)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        identity_visible = (
            visible.st_dev,
            visible.st_ino,
            visible.st_size,
            visible.st_mtime_ns,
        )
        if identity_before != identity_after or identity_after != identity_visible:
            raise OSError("文件在读取过程中被修改，请重试")
        payload = b"".join(chunks)
        snapshot = (*identity_after, hashlib.sha256(payload).hexdigest())
        return target, payload, snapshot

    def read_text(self, path, supported_suffixes):
        target = self._validate_path(path)
        if target.suffix.lower() not in supported_suffixes:
            raise ValueError("仅支持 Markdown、TXT、CSV、JSON、YAML 和日志文本")
        target, payload, snapshot = self._read_payload(target)
        if b"\x00" in payload:
            raise ValueError("检测到二进制内容，无法作为实验文本打开")
        try:
            text = payload.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("文件不是有效的 UTF-8 文本") from exc
        return target, text, snapshot

    def write_text(
        self,
        path,
        text: str,
        *,
        exclusive=False,
        expected_snapshot=None,
    ) -> Path:
        payload = text.encode("utf-8")
        if len(payload) > self.max_file_bytes:
            raise ValueError("实验记录超过 5 MiB，已拒绝保存")
        target = self._validate_path(path, leaf_may_be_missing=True)
        parent = self._validate_path(target.parent)
        if not parent.is_dir():
            raise ValueError("实验文件父路径不是文件夹")

        if exclusive and (target.exists() or target.is_symlink()):
            raise FileExistsError(str(target))
        if expected_snapshot is not None:
            try:
                _current, _payload, current_snapshot = self._read_payload(target)
            except (OSError, ValueError) as exc:
                raise PortableStorageExternalModificationError(
                    "原文件目录或内容已不可用"
                ) from exc
            if current_snapshot != expected_snapshot:
                raise PortableStorageExternalModificationError("文件已在外部修改")
        elif not exclusive and target.exists():
            info = os.lstat(self._validate_path(target))
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("目标路径不是普通文件，已拒绝覆盖")

        save_file = QSaveFile(str(target))
        save_file.setDirectWriteFallback(False)
        if not save_file.open(QIODevice.WriteOnly):
            raise OSError(save_file.errorString())
        try:
            written = save_file.write(QByteArray(payload))
            if written != len(payload):
                raise OSError(save_file.errorString() or "实验记录写入不完整")
            # Narrow the check-to-commit window while preserving the atomic
            # target replacement supplied by QSaveFile.
            if expected_snapshot is not None:
                _current, _payload, current_snapshot = self._read_payload(target)
                if current_snapshot != expected_snapshot:
                    raise PortableStorageExternalModificationError("文件已在外部修改")
            if exclusive and (target.exists() or target.is_symlink()):
                raise FileExistsError(str(target))
            if not save_file.commit():
                raise OSError(save_file.errorString() or "无法原子提交实验记录")
        except Exception:
            save_file.cancelWriting()
            raise
        return target
