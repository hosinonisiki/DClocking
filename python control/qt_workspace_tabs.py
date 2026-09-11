"""Browser-style workspace tabs with optional detached native windows."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from qt_ui_theme import apply_application_theme


class DetachableWorkspaceTabBar(QTabBar):
    """Movable tab bar that emits when a page is dragged outside its strip."""

    detach_requested = Signal(object, QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pressed_page = None
        self._press_global_pos = QPoint()
        self.setMovable(True)
        self.setExpanding(False)
        self.setElideMode(Qt.ElideRight)
        self.setUsesScrollButtons(True)

    def _page_at(self, position):
        index = self.tabAt(position)
        owner = self.parentWidget()
        if index < 0 or owner is None or not hasattr(owner, "widget"):
            return None
        return owner.widget(index)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._pressed_page = self._page_at(event.position().toPoint())
            self._press_global_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._pressed_page is not None and event.buttons() & Qt.LeftButton:
            distance = (event.globalPosition().toPoint() - self._press_global_pos).manhattanLength()
            detach_zone = self.rect().adjusted(-24, -34, 24, 34)
            if (
                distance >= QApplication.startDragDistance()
                and not detach_zone.contains(event.position().toPoint())
            ):
                page = self._pressed_page
                self._pressed_page = None
                self.detach_requested.emit(page, event.globalPosition().toPoint())
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._pressed_page = None
        super().mouseReleaseEvent(event)


@dataclass
class _WorkspaceEntry:
    key: str
    title: str
    page: QWidget
    detached_window: "DetachedWorkspaceWindow | None" = None


class DetachedWorkspaceWindow(QMainWindow):
    """Native window used while a workspace tab is detached."""

    def __init__(self, manager, entry: _WorkspaceEntry, global_position: QPoint):
        super().__init__(None)
        self._manager = manager
        self._workspace_key = entry.key
        self._page = entry.page
        self._allow_close = False

        self.setObjectName("detached_workspace_window")
        self.setAccessibleName(f"{entry.title}独立窗口")
        self.setWindowTitle(f"{entry.title} · 独立窗口")
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        host = QWidget(self)
        host.setObjectName("detached_workspace_host")
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QFrame(host)
        toolbar.setObjectName("detached_workspace_toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 6, 10, 6)
        toolbar_layout.setSpacing(8)
        state_label = QLabel("独立窗口", toolbar)
        state_label.setProperty("role", "eyebrow")
        toolbar_layout.addWidget(state_label)
        toolbar_layout.addStretch()
        self.reattach_button = QPushButton("回到主窗口", toolbar)
        self.reattach_button.setObjectName("reattach_workspace_button")
        self.reattach_button.setAccessibleName(f"将{entry.title}放回主窗口标签栏")
        self.reattach_button.clicked.connect(
            lambda _checked=False: self._manager.reattach_workspace(self._workspace_key)
        )
        toolbar_layout.addWidget(self.reattach_button)
        layout.addWidget(toolbar)

        self._page.hide()
        self._page.setParent(host)
        self._page.setWindowFlags(Qt.Widget)
        layout.addWidget(self._page, 1)
        self._page.show()
        self.setCentralWidget(host)

        page_size = self._page.size()
        width = min(1440, max(900, page_size.width()))
        height = min(900, max(600, page_size.height() + 42))
        self.resize(width, height)
        self.move(global_position.x() - 180, global_position.y() - 24)
        apply_application_theme(self)

    @property
    def page(self):
        return self._page

    def release_page(self, new_parent):
        page = self._page
        if page is None:
            return None
        page.hide()
        host = self.centralWidget()
        if host is not None and host.layout() is not None:
            host.layout().removeWidget(page)
        page.setParent(new_parent)
        page.setWindowFlags(Qt.Widget)
        self._page = None
        return page

    def force_close(self):
        self._allow_close = True
        self.close()

    def open_workspace_window(self, key, title, widget, source=None):
        return self._manager.open_workspace(key, title, widget, source=source)

    def closeEvent(self, event):
        if self._allow_close:
            event.accept()
            return
        if self._manager.close_detached_workspace(self._workspace_key, self):
            event.accept()
        else:
            event.ignore()


class WorkspaceTabWidget(QTabWidget):
    """Owns the fixed console tab and the application's tool workspaces."""

    workspace_closed = Signal(str)
    workspace_detached = Signal(str)
    workspace_reattached = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspace_tabs")
        self.setAccessibleName("浏览器式工作区标签栏")
        self.setDocumentMode(True)
        self.setTabsClosable(True)

        self._tab_bar = DetachableWorkspaceTabBar(self)
        self.setTabBar(self._tab_bar)
        self._tab_bar.detach_requested.connect(self.detach_page)
        self.tabCloseRequested.connect(self.close_tab)

        self._home_page = None
        self._entries: dict[str, _WorkspaceEntry] = {}
        self._key_by_page: dict[QWidget, str] = {}
        self._shutting_down = False

    def add_home_tab(self, page: QWidget, title="主控制台"):
        if self._home_page is not None:
            raise RuntimeError("The workspace home tab is already registered")
        self._home_page = page
        index = self.addTab(page, title)
        self.tabBar().setTabData(index, "home")
        self.tabBar().setTabToolTip(index, "主控制台不可关闭；点击返回 FPGA 画布")
        self._hide_close_button(index)
        self.setCurrentIndex(index)
        return index

    def _hide_close_button(self, index):
        self.tabBar().setTabButton(index, QTabBar.RightSide, None)
        self.tabBar().setTabButton(index, QTabBar.LeftSide, None)

    def _configure_tool_tab(self, index, entry):
        self.tabBar().setTabData(index, entry.key)
        self.tabBar().setTabToolTip(index, "拖出标签栏可拆分为独立窗口")
        close_button = QPushButton("×", self.tabBar())
        close_button.setObjectName("workspace_tab_close_button")
        close_button.setAccessibleName(f"关闭{entry.title}标签")
        close_button.setToolTip(f"关闭{entry.title}")
        close_button.setFixedSize(28, 28)
        close_button.clicked.connect(
            lambda _checked=False, key=entry.key: self.close_workspace(key)
        )
        self.tabBar().setTabButton(index, QTabBar.RightSide, close_button)

    def show_home(self):
        if self._home_page is not None:
            self.setCurrentWidget(self._home_page)
            self._home_page.setFocus(Qt.OtherFocusReason)

    def open_workspace(self, key, title, widget, source=None):
        key = str(key)
        entry = self._entries.get(key)
        if entry is not None:
            if entry.detached_window is not None:
                entry.detached_window.show()
                entry.detached_window.raise_()
                entry.detached_window.activateWindow()
            else:
                index = self.indexOf(entry.page)
                if index >= 0:
                    self.setCurrentIndex(index)
                    entry.page.show()
            return entry.page

        widget.hide()
        widget.setParent(self)
        widget.setWindowFlags(Qt.Widget)
        entry = _WorkspaceEntry(key=key, title=str(title), page=widget)
        self._entries[key] = entry
        self._key_by_page[widget] = key
        widget.destroyed.connect(lambda *_args, page=widget: self._page_destroyed(page))

        index = self.addTab(widget, entry.title)
        self._configure_tool_tab(index, entry)
        self.setCurrentIndex(index)
        widget.show()
        owner = self.window()
        if owner is not None:
            owner.show()
            owner.raise_()
            owner.activateWindow()
        return widget

    def contains_source(self, source):
        if source is None:
            return False
        if self._home_page is not None and (
            source is self._home_page or self._home_page.isAncestorOf(source)
        ):
            return True
        for entry in self._entries.values():
            page = entry.page
            if source is page or page.isAncestorOf(source):
                return True
        return False

    def workspace_key(self, page):
        return self._key_by_page.get(page)

    def detached_window(self, key):
        entry = self._entries.get(str(key))
        return entry.detached_window if entry is not None else None

    def close_tab(self, index):
        page = self.widget(index)
        if page is None or page is self._home_page:
            return False
        key = self._key_by_page.get(page)
        return self.close_workspace(key) if key is not None else False

    def close_workspace(self, key):
        entry = self._entries.get(str(key))
        if entry is None:
            return True
        if not entry.page.close():
            return False

        index = self.indexOf(entry.page)
        if index >= 0:
            self.removeTab(index)
        if entry.detached_window is not None:
            window = entry.detached_window
            window.release_page(self)
            window.force_close()
        self._forget_entry(entry)
        self.workspace_closed.emit(entry.key)
        return True

    def detach_page(self, page, global_position=None):
        if page is None or page is self._home_page:
            return None
        key = self._key_by_page.get(page)
        entry = self._entries.get(key) if key is not None else None
        if entry is None or entry.detached_window is not None:
            return entry.detached_window if entry is not None else None

        index = self.indexOf(page)
        if index < 0:
            return None
        self.removeTab(index)
        position = global_position or self.mapToGlobal(self.rect().center())
        window = DetachedWorkspaceWindow(self, entry, position)
        entry.detached_window = window
        window.show()
        window.raise_()
        window.activateWindow()
        self.workspace_detached.emit(entry.key)
        return window

    def reattach_workspace(self, key):
        entry = self._entries.get(str(key))
        if entry is None or entry.detached_window is None:
            return False
        window = entry.detached_window
        page = window.release_page(self)
        entry.detached_window = None
        window.force_close()
        if page is None:
            self._forget_entry(entry)
            return False
        index = self.addTab(page, entry.title)
        self._configure_tool_tab(index, entry)
        self.setCurrentIndex(index)
        page.show()
        self.workspace_reattached.emit(entry.key)
        return True

    def close_detached_workspace(self, key, window):
        entry = self._entries.get(str(key))
        if entry is None or entry.detached_window is not window:
            return True
        if not entry.page.close():
            return False
        window.release_page(self)
        entry.detached_window = None
        self._forget_entry(entry)
        self.workspace_closed.emit(entry.key)
        return True

    def _forget_entry(self, entry):
        self._entries.pop(entry.key, None)
        self._key_by_page.pop(entry.page, None)

    def _page_destroyed(self, page):
        key = self._key_by_page.pop(page, None)
        if key is None:
            return
        entry = self._entries.pop(key, None)
        if entry is None:
            return
        if not self._shutting_down and entry.detached_window is not None:
            entry.detached_window.force_close()

    def shutdown(self):
        self._shutting_down = True
        for entry in list(self._entries.values()):
            if entry.detached_window is not None:
                window = entry.detached_window
                window.release_page(self)
                entry.detached_window = None
                window.force_close()
