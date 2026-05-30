"""Agent chat widget — dockable chat panel for FPGA Agent interaction.

Provides a message-bubble chat UI with markdown rendering for LLM responses,
collapsible tool-call display, and an input area.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QEvent, Signal, QTimer
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QPlainTextEdit, QPushButton, QLabel,
    QTextBrowser, QFrame, QSizePolicy, QDialog,
    QFormLayout, QLineEdit, QDialogButtonBox,
)

from chat_styles import (
    CHAT_WIDGET_STYLE,
    USER_BUBBLE_STYLE,
    ASSISTANT_BUBBLE_STYLE,
    SYSTEM_MSG_STYLE,
    TOOL_CALL_STYLE,
    THINKING_STYLE,
)


class AgentChatWidget(QDockWidget):
    """Dockable chat panel for the FPGA Agent."""

    user_message_submitted = Signal(str)

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
        title.setStyleSheet("color: #cdd6f4; font-size: 14px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        self._settings_btn = QPushButton("Settings")
        self._settings_btn.setObjectName("settings_button")
        self._settings_btn.clicked.connect(self._open_settings)
        header.addWidget(self._settings_btn)

        layout.addLayout(header)

        # Scroll area for messages
        self._scroll = QScrollArea()
        self._scroll.setObjectName("chat_scroll_area")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._msg_container = QWidget()
        self._msg_layout = QVBoxLayout(self._msg_container)
        self._msg_layout.setContentsMargins(4, 4, 4, 4)
        self._msg_layout.setSpacing(8)
        self._msg_layout.addStretch()

        self._scroll.setWidget(self._msg_container)
        layout.addWidget(self._scroll, stretch=1)

        # Thinking indicator
        self._thinking_label = QLabel("")
        self._thinking_label.setObjectName("thinking_label")
        self._thinking_label.setStyleSheet(THINKING_STYLE)
        self._thinking_label.setVisible(False)
        layout.addWidget(self._thinking_label)

        # Input area
        input_row = QHBoxLayout()
        self._input = QPlainTextEdit()
        self._input.setObjectName("chat_input")
        self._input.setPlaceholderText("描述你想搭建的功能，例如：帮我实现 PDH 锁定...")
        self._input.setMaximumHeight(80)
        self._input.installEventFilter(self)
        input_row.addWidget(self._input)

        self._send_btn = QPushButton("Send")
        self._send_btn.setObjectName("send_button")
        self._send_btn.clicked.connect(self._send_message)
        input_row.addWidget(self._send_btn)

        layout.addLayout(input_row)

        # Track tool call frames for updating
        self._pending_tool_frames: dict[str, QFrame] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_user_message(self, text: str):
        """Add a user message bubble (right-aligned)."""
        bubble = QTextBrowser()
        bubble.setStyleSheet(USER_BUBBLE_STYLE)
        bubble.setPlainText(text)
        bubble.setMaximumWidth(280)
        bubble.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self._add_bubble(bubble, align_right=True)

    def add_assistant_message(self, markdown_text: str):
        """Add an assistant message bubble (left-aligned, markdown rendered)."""
        bubble = QTextBrowser()
        bubble.setStyleSheet(ASSISTANT_BUBBLE_STYLE)
        bubble.setOpenExternalLinks(True)
        bubble.setMaximumWidth(300)
        bubble.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        try:
            import markdown
            html = markdown.markdown(
                markdown_text,
                extensions=["fenced_code", "tables", "codehilite"],
            )
        except ImportError:
            html = markdown_text.replace("\n", "<br>")

        bubble.setHtml(html)
        self._add_bubble(bubble, align_right=False)

    def add_system_message(self, text: str):
        """Add a centered system info message."""
        label = QLabel(text)
        label.setStyleSheet(SYSTEM_MSG_STYLE)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        self._insert_widget(label)

    def add_tool_call(self, tool_name: str, args_json: str, result_json: str = ""):
        """Add a collapsible tool-call display."""
        frame = self._make_tool_frame(tool_name, args_json, result_json)
        self._insert_widget(frame)

    def set_thinking(self, visible: bool):
        """Show/hide the thinking indicator with animated dots."""
        self._thinking_label.setVisible(visible)
        if visible:
            self._thinking_dots = 0
            self._think_timer = QTimer(self)
            self._think_timer.timeout.connect(self._update_thinking_dots)
            self._think_timer.start(400)
        else:
            if hasattr(self, '_think_timer') and self._think_timer:
                self._think_timer.stop()

    def clear_chat(self):
        """Clear all messages."""
        while self._msg_layout.count() > 1:
            item = self._msg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _send_message(self):
        text = self._input.toPlainText().strip()
        if not text:
            return
        self.add_user_message(text)
        self._input.clear()
        self.user_message_submitted.emit(text)

    def eventFilter(self, obj, event):
        """Handle Shift+Enter to send."""
        if obj is self._input and event.type() == QEvent.KeyPress:
            if (event.key() == Qt.Key_Return and
                    event.modifiers() == Qt.ShiftModifier):
                self._send_message()
                return True
        return super().eventFilter(obj, event)

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
        frame.setStyleSheet(TOOL_CALL_STYLE)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        toggle = QPushButton(f"Tool: {tool_name}")
        toggle.setObjectName("tool_toggle")
        toggle.setCheckable(True)

        detail = QLabel(f"Args: {args_json}")
        detail.setObjectName("tool_detail")
        detail.setWordWrap(True)
        detail.setVisible(False)

        result_label = QLabel(f"→ {result_json[:200]}" if result_json else "")
        result_label.setObjectName("tool_detail")
        result_label.setWordWrap(True)
        result_label.setVisible(False)

        def _toggle(checked):
            detail.setVisible(checked)
            result_label.setVisible(checked and bool(result_json))

        toggle.toggled.connect(_toggle)
        layout.addWidget(toggle)
        layout.addWidget(detail)
        if result_json:
            layout.addWidget(result_label)

        return frame

    def _update_thinking_dots(self):
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

        # Load current config
        import json
        from pathlib import Path
        config_path = Path(__file__).resolve().parent / "config.json"
        if config_path.exists():
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            llm = cfg.get("llm", {})
            endpoint_edit.setText(llm.get("endpoint", ""))
            api_key_edit.setText(llm.get("api_key", ""))
            model_edit.setText(llm.get("model", ""))

        layout.addRow("API Endpoint:", endpoint_edit)
        layout.addRow("API Key:", api_key_edit)
        layout.addRow("Model:", model_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save |
                                   QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self._save_settings(
            dialog, endpoint_edit.text(), api_key_edit.text(),
            model_edit.text()))
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.exec()

    def _save_settings(self, dialog, endpoint, api_key, model):
        import json
        from pathlib import Path
        config_path = Path(__file__).resolve().parent / "config.json"
        cfg = {}
        if config_path.exists():
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
        if "llm" not in cfg:
            cfg["llm"] = {}
        if endpoint:
            cfg["llm"]["endpoint"] = endpoint
        if api_key:
            cfg["llm"]["api_key"] = api_key
        if model:
            cfg["llm"]["model"] = model
        config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        dialog.accept()
