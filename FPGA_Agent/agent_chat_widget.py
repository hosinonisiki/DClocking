"""Agent chat widget — dockable chat panel for FPGA Agent interaction.

Provides a message-bubble chat UI with markdown rendering for LLM responses,
collapsible tool-call display, and an input area.
"""

from __future__ import annotations

from collections import deque
import json

from shiboken6 import isValid
from PySide6.QtCore import Qt, QEvent, Signal, QTimer, QSize
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QPlainTextEdit, QPushButton, QLabel,
    QTextBrowser, QFrame, QSizePolicy, QDialog,
    QFormLayout, QLineEdit, QDialogButtonBox, QComboBox,
    QMessageBox,
)

from chat_styles import (
    CHAT_WIDGET_STYLE,
    USER_BUBBLE_STYLE,
    ASSISTANT_BUBBLE_STYLE,
    SYSTEM_MSG_STYLE,
    TOOL_CALL_STYLE,
    THINKING_STYLE,
)


class _WrappingToolButton(QPushButton):
    """Keep long tool names accessible without imposing a minimum chat width."""

    def __init__(self, text):
        super().__init__()
        self._label = QLabel(self)
        self._label.setTextFormat(Qt.PlainText)
        self._label.setWordWrap(True)
        self._label.setMinimumWidth(0)
        self._label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._label.setStyleSheet(
            "color: #85172E; background: transparent; border: none; "
            "font-size: 12px; font-weight: bold;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._label)
        policy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        self.setMinimumWidth(0)
        self.setText(text)

    def setText(self, text):
        self._full_text = text
        # QLabel word-wrap does not break long underscore-delimited identifiers.
        # Invisible display-only break opportunities preserve the public text
        # and accessible name while keeping every part of the tool name visible.
        self._label.setText("\u200b".join(text[index:index + 16]
                                       for index in range(0, len(text), 16)))
        self.setAccessibleName(text)
        self.updateGeometry()

    def text(self):
        return self._full_text

    def sizeHint(self):
        return self.layout().sizeHint()

    def minimumSizeHint(self):
        return QSize(0, 28)

    def heightForWidth(self, width):
        return self.layout().heightForWidth(width)


class AgentChatWidget(QDockWidget):
    """Dockable chat panel for the FPGA Agent."""

    user_message_submitted = Signal(str)
    cancel_requested = Signal()
    settings_saved = Signal(dict)
    approval_resolved = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__("FPGA Agent", parent)
        self.setObjectName("agent_chat_dock")
        self.setMinimumWidth(320)
        self.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )

        # Central widget
        central = QWidget()
        central.setObjectName("chat_panel")
        central.setStyleSheet(CHAT_WIDGET_STYLE)
        self.setWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header bar
        header = QHBoxLayout()
        title = QLabel("FPGA Agent")
        title.setStyleSheet("color: #303438; font-size: 14px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        self._settings_btn = QPushButton("设置")
        self._settings_btn.setObjectName("settings_button")
        self._settings_btn.setAccessibleName("打开 Agent 设置")
        self._settings_btn.clicked.connect(self.open_settings)
        header.addWidget(self._settings_btn)

        layout.addLayout(header)

        self._runtime_status = QLabel()
        self._runtime_status.setObjectName("agent_runtime_status")
        self._runtime_status.setTextFormat(Qt.PlainText)
        self._runtime_status.setWordWrap(True)
        self._runtime_status.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self._runtime_status.setMinimumWidth(0)
        self._runtime_status.setStyleSheet("color: #72777B; font-size: 11px;")
        layout.addWidget(self._runtime_status)
        self.set_runtime_status("harness")

        # Scroll area for messages
        self._scroll = QScrollArea()
        self._scroll.setObjectName("chat_scroll_area")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._msg_container = QWidget()
        self._msg_container.setMinimumWidth(0)
        self._msg_container.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self._msg_layout = QVBoxLayout(self._msg_container)
        self._msg_layout.setContentsMargins(4, 4, 4, 4)
        self._msg_layout.setSpacing(8)
        self._msg_layout.addStretch()

        self._scroll.setWidget(self._msg_container)
        self._message_viewport = self._scroll.viewport()
        layout.addWidget(self._scroll, stretch=1)

        # Thinking indicator
        self._thinking_label = QLabel("")
        self._thinking_label.setObjectName("thinking_label")
        self._thinking_label.setStyleSheet(THINKING_STYLE)
        self._thinking_label.setVisible(False)
        layout.addWidget(self._thinking_label)

        self._is_thinking = False
        self._cancel_pending = False
        self._thinking_dots = 0
        self._think_timer = QTimer(self)
        self._think_timer.timeout.connect(self._update_thinking_dots)

        # Input area
        input_row = QHBoxLayout()
        self._input = QPlainTextEdit()
        self._input.setObjectName("chat_input")
        self._input.setPlaceholderText("描述你想搭建的功能，例如：帮我实现 PDH 锁定...")
        self._input.setMaximumHeight(80)
        self._input.installEventFilter(self)
        input_row.addWidget(self._input)

        self._send_btn = QPushButton("↑")
        self._send_btn.setObjectName("send_button")
        self._send_btn.setProperty("mode", "send")
        self._send_btn.setFixedSize(48, 48)
        self._send_btn.setAccessibleName("发送 Agent 消息")
        self._send_btn.setToolTip("发送（Enter）")
        self._send_btn.clicked.connect(self._handle_primary_action)
        input_row.addWidget(self._send_btn)

        layout.addLayout(input_row)

        # Track tool call frames for updating
        self._pending_tool_frames: dict[tuple[str, str], QFrame] = {}
        self._approval_frames: dict[str, QFrame] = {}
        self._approval_scroll_request = None
        self._stream_bubble = None
        self._stream_run_id = None
        self._retired_stream_runs = deque(maxlen=256)
        self._stream_characters = 0
        self._stream_truncated = False
        self._stream_fit_timer = QTimer(self)
        self._stream_fit_timer.setSingleShot(True)
        self._stream_fit_timer.setInterval(40)
        self._stream_fit_timer.timeout.connect(self._fit_stream_bubble)
        self._message_resize_timer = QTimer(self)
        self._message_resize_timer.setSingleShot(True)
        self._message_resize_timer.timeout.connect(self._refit_message_bubbles)
        self._message_viewport.installEventFilter(self)
        self._scroll.verticalScrollBar().rangeChanged.connect(self._reveal_pending_approval)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_user_message(self, text: str):
        """Add a user message bubble (right-aligned)."""
        bubble = QTextBrowser()
        bubble.setStyleSheet(USER_BUBBLE_STYLE)
        bubble.setPlainText(text)
        self._prepare_message_bubble(bubble, 280)
        self._add_bubble(bubble, align_right=True)
        self._schedule_message_bubble_fit(bubble)

    def add_assistant_message(self, markdown_text: str):
        """Add an assistant message bubble (left-aligned, markdown rendered)."""
        bubble = self._make_assistant_bubble()
        self._render_assistant_markdown(bubble, markdown_text)
        self._schedule_message_bubble_fit(bubble)

    def _make_assistant_bubble(self):
        bubble = QTextBrowser()
        bubble.setStyleSheet(ASSISTANT_BUBBLE_STYLE)
        bubble.setOpenExternalLinks(True)
        self._prepare_message_bubble(bubble, 300)
        self._add_bubble(bubble, align_right=False)
        return bubble

    @staticmethod
    def _render_assistant_markdown(bubble, markdown_text):
        try:
            import markdown
            html = markdown.markdown(
                markdown_text,
                extensions=["fenced_code", "tables", "codehilite"],
            )
        except ImportError:
            bubble.setMarkdown(markdown_text)
        else:
            bubble.setHtml(html)

    def append_assistant_delta(self, run_id: str, text: str):
        """Append plain-text output to the active run, without duplicate cards."""
        if (not self._is_thinking or self._cancel_pending or not text
                or run_id in self._retired_stream_runs):
            return
        if self._stream_run_id is not None and self._stream_run_id != run_id:
            return
        if self._stream_bubble is None:
            self._stream_run_id = run_id
            self._stream_bubble = self._make_assistant_bubble()
        if self._stream_truncated:
            return
        # This is a display limit only; the engine retains its own full receipt.
        remaining = max(0, 512 * 1024 - self._stream_characters)
        visible = text[:remaining]
        self._stream_characters += len(visible)
        if len(text) > remaining:
            visible += "\n…（流式显示已截断）"
            self._stream_truncated = True
        cursor = self._stream_bubble.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(visible)
        if not self._stream_fit_timer.isActive():
            self._stream_fit_timer.start()

    def finish_assistant_message(self, markdown_text: str):
        """Replace streaming text with final Markdown, even after thinking stops."""
        bubble = self._stream_bubble
        if bubble is None or not isValid(bubble):
            self.add_assistant_message(markdown_text)
            return
        self._render_assistant_markdown(bubble, markdown_text)
        self._schedule_message_bubble_fit(bubble)
        self._retire_stream_bubble()

    def _fit_stream_bubble(self):
        bubble = self._stream_bubble
        if bubble is not None and isValid(bubble):
            self._fit_message_bubble(bubble)
            self._scroll_to_bottom()

    def _retire_stream_bubble(self):
        self._stream_fit_timer.stop()
        if self._stream_run_id is not None:
            self._retired_stream_runs.append(self._stream_run_id)
        self._stream_run_id = None
        self._stream_bubble = None
        self._stream_characters = 0
        self._stream_truncated = False

    def add_system_message(self, text: str):
        """Add a centered system info message."""
        label = QLabel(text)
        label.setTextFormat(Qt.PlainText)
        label.setStyleSheet(SYSTEM_MSG_STYLE)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        self._constrain_message_label(label)
        self._insert_widget(label)

    def add_tool_call(self, tool_name: str, args_json: str, result_json: str = ""):
        """Add a collapsible tool-call display."""
        frame = self._make_tool_frame(tool_name, args_json, result_json)
        self._insert_widget(frame)

    def set_runtime_status(self, engine: str, text: str = ""):
        """Display the selected engine; an error never selects a fallback."""
        name = {"harness": "DeepSeek Harness", "native": "Native · 原生兼容引擎"}.get(
            engine, str(engine)
        )
        self._runtime_status.setText(f"{name} · {text}" if text else name)
        self._runtime_status.setToolTip(
            "执行引擎由设置显式选择；发生错误不会自动切换引擎。"
        )

    def update_tool_call(self, run_id: str, call_id: str, name: str,
                         args_json: str, result_json: str, status: str):
        """Update a tool receipt by identity, not by its possibly repeated name."""
        key = (str(run_id), str(call_id))
        frame = self._pending_tool_frames.get(key)
        if frame is None:
            frame = self._make_tool_frame(name, args_json, result_json)
            self._pending_tool_frames[key] = frame
            self._insert_widget(frame)
        labels = {
            "pending": "等待执行", "running": "执行中", "started": "执行中",
            "awaiting_approval": "等待确认", "completed": "完成",
            "success": "完成", "failed": "失败", "error": "失败",
            "cancelled": "已取消", "denied": "已拒绝",
            "read_only": "只读查询", "local_staged": "本地配置已更新",
            "hardware_unverified": "硬件状态未验证",
        }
        toggle = frame.findChild(QPushButton, "tool_toggle")
        detail = frame.findChild(QLabel, "tool_detail")
        result = frame.findChild(QLabel, "tool_result")
        toggle.setText(f"Tool: {name} · {labels.get(status, status)}")
        detail.setText(f"Args: {self._bounded_detail(args_json)}")
        result.setText(f"→ {self._bounded_detail(result_json)}" if result_json else "")
        result.setVisible(toggle.isChecked() and bool(result_json))
        frame.setProperty("tool_status", status)

    def show_tool_approval(self, request_id: str, summary: str, details):
        """Show an inline, one-shot approval. No nested modal event loop."""
        if request_id in self._approval_frames:
            return
        frame = QFrame()
        frame.setObjectName("tool_approval_frame")
        frame.setMinimumWidth(0)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        frame.setStyleSheet("""
            QFrame#tool_approval_frame {
                background: #FFF8F9; border: 1px solid #DAB8C0; border-radius: 12px;
            }
            QFrame#tool_approval_frame QLabel {
                color: #303438; background: transparent; border: none;
            }
            QFrame#tool_approval_frame QLabel#approval_summary {
                color: #85172E; font-weight: 600;
            }
            QFrame#tool_approval_frame QLabel#approval_status { color: #72777B; }
            QFrame#tool_approval_frame QPushButton {
                border: 1px solid #D8D2CC; border-radius: 8px; padding: 8px 12px;
                color: #303438; background: #FFFFFF;
            }
            QFrame#tool_approval_frame QPushButton#approval_allow_once {
                color: #FFFFFF; background: #85172E; border-color: #85172E;
            }
            QFrame#tool_approval_frame QPushButton:disabled,
            QFrame#tool_approval_frame QPushButton#approval_allow_once:disabled {
                color: #8C8884; background: #EDE9E5; border-color: #EDE9E5;
            }
        """)
        frame.setProperty("approval_pending", True)
        layout = QVBoxLayout(frame)
        heading = QLabel(str(summary))
        heading.setObjectName("approval_summary")
        heading.setTextFormat(Qt.PlainText)
        heading.setWordWrap(True)
        self._constrain_message_label(heading)
        layout.addWidget(heading)
        frame.setProperty("request_id", request_id)
        display_details = details
        if isinstance(details, dict):
            display_details = {key: details[key] for key in (
                "tool", "arguments", "transport_state", "warning"
            ) if key in details}
            metadata = []
            for key in ("run_id", "call_id"):
                if key in details:
                    frame.setProperty(key, str(details[key]))
                    metadata.append(f"{key}: {details[key]}")
            frame.setToolTip("\n".join(metadata))
        detail = QLabel(self._bounded_detail(display_details))
        detail.setObjectName("approval_detail")
        detail.setTextFormat(Qt.PlainText)
        detail.setWordWrap(True)
        self._constrain_message_label(detail)
        detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(detail)
        state = QLabel("等待你的确认；仅允许本次操作。")
        state.setObjectName("approval_status")
        state.setWordWrap(True)
        self._constrain_message_label(state)
        layout.addWidget(state)
        buttons = QHBoxLayout()
        allow = QPushButton("允许一次")
        allow.setObjectName("approval_allow_once")
        allow.setAccessibleName("仅允许本次 Agent 操作")
        deny = QPushButton("拒绝")
        deny.setObjectName("approval_deny")
        deny.setAccessibleName("拒绝本次 Agent 操作")
        allow.clicked.connect(lambda: self._resolve_tool_approval(request_id, True))
        deny.clicked.connect(lambda: self._resolve_tool_approval(request_id, False))
        buttons.addWidget(allow)
        buttons.addWidget(deny)
        layout.addLayout(buttons)
        self._approval_frames[request_id] = frame
        self._approval_scroll_request = request_id
        self._insert_widget(frame)
        QTimer.singleShot(0, self._reveal_pending_approval)

    def _reveal_pending_approval(self, *_range):
        """Keep new actions visible as Qt finishes deferred document layouts."""
        frame = self._approval_frames.get(self._approval_scroll_request)
        if frame is None or not isValid(frame) or not frame.property("approval_pending"):
            return
        button = frame.findChild(QPushButton, "approval_allow_once")
        self._scroll.ensureWidgetVisible(button, 0, 12)

    def dismiss_tool_approvals(self):
        """Fail closed when generation ends, is cancelled, or chat is cleared."""
        for request_id in tuple(self._approval_frames):
            self._resolve_tool_approval(request_id, False, cancelled=True)

    def expire_tool_approval(self, request_id: str):
        """Reflect a terminal gateway request without making another decision."""
        frame = self._approval_frames.get(request_id)
        if frame is None or not frame.property("approval_pending"):
            return
        if self._approval_scroll_request == request_id:
            self._approval_scroll_request = None
        frame.setProperty("approval_pending", False)
        for button in frame.findChildren(QPushButton):
            button.setEnabled(False)
        frame.findChild(QLabel, "approval_status").setText("请求已结束或已取消，无法继续授权。")

    def _resolve_tool_approval(self, request_id: str, allowed: bool,
                               *, cancelled: bool = False):
        frame = self._approval_frames.get(request_id)
        if frame is None or not frame.property("approval_pending"):
            return
        if self._approval_scroll_request == request_id:
            self._approval_scroll_request = None
        frame.setProperty("approval_pending", False)
        for button in frame.findChildren(QPushButton):
            button.setEnabled(False)
        status = "已取消，未授权" if cancelled else ("已允许一次" if allowed else "已拒绝")
        frame.findChild(QLabel, "approval_status").setText(status)
        self.approval_resolved.emit(request_id, allowed)

    def set_thinking(self, visible: bool):
        """Show thinking state and switch the primary action to cancel."""
        self._is_thinking = visible
        self._cancel_pending = False
        self._settings_btn.setEnabled(not visible)
        self._thinking_label.setVisible(visible)
        if visible:
            self._retire_stream_bubble()
            self._thinking_dots = 0
            self._think_timer.start(400)
            self._send_btn.setText("■")
            self._send_btn.setProperty("mode", "stop")
            self._send_btn.setAccessibleName("停止 Agent 生成")
            self._send_btn.setToolTip("停止生成")
            self._send_btn.setEnabled(True)
            self._update_thinking_dots()
        else:
            self._fit_stream_bubble()
            self.dismiss_tool_approvals()
            self._think_timer.stop()
            self._thinking_label.clear()
            self._send_btn.setText("↑")
            self._send_btn.setProperty("mode", "send")
            self._send_btn.setAccessibleName("发送 Agent 消息")
            self._send_btn.setToolTip("发送（Enter）")
            self._send_btn.setEnabled(True)
        self._refresh_primary_button_style()

    def clear_chat(self):
        """Clear all messages."""
        self.dismiss_tool_approvals()
        self._retire_stream_bubble()
        self._pending_tool_frames.clear()
        self._approval_frames.clear()
        self._approval_scroll_request = None
        while self._msg_layout.count() > 1:
            item = self._msg_layout.takeAt(0)
            self._delete_message_item(item)

    @staticmethod
    def _delete_message_item(item):
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            layout = item.layout()
            while layout.count():
                AgentChatWidget._delete_message_item(layout.takeAt(0))
            layout.deleteLater()

    def open_settings(self):
        """Open the Agent settings dialog from any presentation control."""
        if self._is_thinking:
            QMessageBox.information(
                self,
                "Agent 正在运行",
                "请先停止当前生成，再修改 API Endpoint 或密钥。",
            )
            return
        self._open_settings()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _handle_primary_action(self):
        if self._is_thinking:
            if self._cancel_pending:
                return
            self._cancel_pending = True
            self._thinking_label.setText("正在停止生成…")
            self._send_btn.setEnabled(False)
            self._send_btn.setAccessibleName("正在停止 Agent 生成")
            self.cancel_requested.emit()
            # Set the runtime cancellation token before waking an approval
            # waiter; denying first could let its model loop start a new call.
            self.dismiss_tool_approvals()
            return
        self._send_message()

    def _send_message(self):
        if self._is_thinking:
            return
        text = self._input.toPlainText().strip()
        if not text:
            return
        self.add_user_message(text)
        self._input.clear()
        self.user_message_submitted.emit(text)

    def eventFilter(self, obj, event):
        """Send with Enter while preserving Shift+Enter for a newline."""
        if (obj is self._message_viewport and event.type() == QEvent.Resize
                and hasattr(self, "_message_resize_timer")):
            self._message_resize_timer.start(0)
        if obj is self._input and event.type() == QEvent.KeyPress:
            if (
                event.key() in (Qt.Key_Return, Qt.Key_Enter)
                and not (event.modifiers() & Qt.ShiftModifier)
            ):
                if not self._is_thinking:
                    self._send_message()
                return True
        return super().eventFilter(obj, event)

    def _refresh_primary_button_style(self):
        style = self._send_btn.style()
        style.unpolish(self._send_btn)
        style.polish(self._send_btn)
        self._send_btn.update()

    def _prepare_message_bubble(self, bubble: QTextBrowser, width: int) -> None:
        """Configure a message surface that grows vertically with its document."""
        bubble.setProperty("preferred_bubble_width", width)
        bubble.setFixedWidth(min(width, self._message_width()))
        bubble.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        bubble.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        bubble.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def _schedule_message_bubble_fit(self, bubble: QTextBrowser) -> None:
        """Fit after layout has established the styled viewport dimensions."""
        QTimer.singleShot(0, lambda: self._fit_message_bubble(bubble))

    def _fit_message_bubble(self, bubble: QTextBrowser) -> None:
        if bubble is None or not isValid(bubble) or bubble.viewport().width() <= 0:
            return
        bubble.setFixedWidth(min(bubble.property("preferred_bubble_width") or 300,
                                 self._message_width()))
        document = bubble.document()
        document.setTextWidth(float(bubble.viewport().width()))
        document_height = int(document.documentLayout().documentSize().height() + 0.999)
        chrome_height = max(0, bubble.height() - bubble.viewport().height())
        bubble.setFixedHeight(max(44, document_height + chrome_height))

    def _message_width(self):
        # Container and row each add four pixels on both horizontal sides.
        return max(1, self._scroll.viewport().width() - 16)

    def _refit_message_bubbles(self):
        for bubble in self._msg_container.findChildren(QTextBrowser):
            self._fit_message_bubble(bubble)

    @staticmethod
    def _constrain_message_label(label):
        label.setMinimumWidth(0)
        label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

    def _add_bubble(self, widget, align_right: bool):
        row = QHBoxLayout()
        row.setContentsMargins(4, 2, 4, 2)
        if align_right:
            row.addStretch()
            row.addWidget(widget)
        else:
            row.addWidget(widget)
            row.addStretch()
        self._insert_layout(row)

    def _insert_widget(self, widget):
        self._msg_layout.insertWidget(self._msg_layout.count() - 1, widget)
        self._message_resize_timer.start(0)

    def _insert_layout(self, layout):
        self._msg_layout.insertLayout(self._msg_layout.count() - 1, layout)
        # Scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _make_tool_frame(self, tool_name: str, args_json: str,
                         result_json: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("tool_call_frame")
        frame.setMinimumWidth(0)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        frame.setStyleSheet(TOOL_CALL_STYLE)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        toggle = _WrappingToolButton(f"Tool: {tool_name}")
        toggle.setObjectName("tool_toggle")
        toggle.setCheckable(True)

        detail = QLabel(f"Args: {self._bounded_detail(args_json)}")
        detail.setObjectName("tool_detail")
        detail.setTextFormat(Qt.PlainText)
        detail.setWordWrap(True)
        self._constrain_message_label(detail)
        detail.setVisible(False)

        result_label = QLabel(f"→ {self._bounded_detail(result_json)}" if result_json else "")
        result_label.setObjectName("tool_result")
        result_label.setTextFormat(Qt.PlainText)
        result_label.setWordWrap(True)
        self._constrain_message_label(result_label)
        result_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        result_label.setVisible(False)

        def _toggle(checked):
            detail.setVisible(checked)
            result_label.setVisible(checked and bool(result_label.text()))

        toggle.toggled.connect(_toggle)
        layout.addWidget(toggle)
        layout.addWidget(detail)
        layout.addWidget(result_label)

        return frame

    @staticmethod
    def _bounded_detail(value) -> str:
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False, indent=2, default=str)
        return value if len(value) <= 8000 else value[:8000] + "\n…（显示已截断）"

    def _update_thinking_dots(self):
        if self._cancel_pending:
            return
        self._thinking_dots = ((self._thinking_dots + 1) % 4)
        self._thinking_label.setText(
            "Agent is thinking" + "." * self._thinking_dots
        )

    def _open_settings(self):
        """Open a simple settings dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("FPGA Agent Settings")
        dialog.setMinimumWidth(420)

        layout = QFormLayout(dialog)

        endpoint_edit = QLineEdit()
        endpoint_edit.setPlaceholderText("https://api.openai.com/v1")
        api_key_edit = QLineEdit()
        api_key_edit.setEchoMode(QLineEdit.Password)
        api_key_edit.setPlaceholderText("sk-...")
        model_edit = QLineEdit()
        model_edit.setPlaceholderText("gpt-4o")
        engine_select = QComboBox()
        engine_select.setObjectName("agent_engine_selector")
        engine_select.setAccessibleName("Agent 执行引擎")
        engine_select.addItem("DeepSeek Harness（默认）", "harness")
        engine_select.addItem("Native（原生兼容引擎）", "native")

        from pathlib import Path
        from secret_store import load_agent_configuration

        config_path = Path(__file__).resolve().parent / "config.json"
        try:
            cfg, stored_key, warning = load_agent_configuration(config_path)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "无法读取 Agent 设置", str(exc))
            return
        llm = cfg.get("llm", {})
        endpoint_edit.setText(llm.get("endpoint", ""))
        model_edit.setText(llm.get("model", ""))
        engine_select.setCurrentIndex(max(0, engine_select.findData(
            cfg.get("agent", {}).get("engine", "harness")
        )))
        if stored_key:
            api_key_edit.setPlaceholderText("已安全保存；留空则保持当前密钥")
        if warning:
            warning_label = QLabel(warning, dialog)
            warning_label.setWordWrap(True)
            warning_label.setStyleSheet("color: #A15C00;")
            layout.addRow(warning_label)

        layout.addRow("执行引擎:", engine_select)
        runtime_hint = QLabel(
            "Harness 负责推理与工具循环；所有画布和硬件操作仍通过应用网关。"
            "运行时不可用时不会自动回退，可在此显式选择 Native。"
        )
        runtime_hint.setWordWrap(True)
        layout.addRow(runtime_hint)
        layout.addRow("API Endpoint:", endpoint_edit)
        layout.addRow("API Key:", api_key_edit)
        layout.addRow("Model:", model_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save |
                                   QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self._save_settings(
            dialog, endpoint_edit.text(), api_key_edit.text(),
            model_edit.text(), engine_select.currentData()))
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.exec()

    def _save_settings(self, dialog, endpoint, api_key, model, engine=None):
        from pathlib import Path
        from secret_store import save_agent_settings

        config_path = Path(__file__).resolve().parent / "config.json"
        try:
            config, active_key = save_agent_settings(
                config_path,
                endpoint=endpoint,
                api_key=api_key,
                model=model,
                engine=engine,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            QMessageBox.warning(self, "无法保存 Agent 设置", str(exc))
            return
        self.settings_saved.emit({"config": config, "api_key": active_key})
        dialog.accept()
