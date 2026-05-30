"""Qt stylesheets for the FPGA Agent chat UI."""

CHAT_WIDGET_STYLE = """
QWidget#chat_panel {
    background-color: #1e1e2e;
    border: none;
}

QWidget#chat_scroll_area {
    background-color: #1e1e2e;
    border: none;
}

QPlainTextEdit#chat_input {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #585b70;
}
QPlainTextEdit#chat_input:focus {
    border-color: #89b4fa;
}

QPushButton#send_button {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#send_button:hover {
    background-color: #b4d0fb;
}
QPushButton#send_button:pressed {
    background-color: #74a8f7;
}
QPushButton#send_button:disabled {
    background-color: #45475a;
    color: #6c7086;
}

QPushButton#settings_button {
    background-color: transparent;
    color: #a6adc8;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton#settings_button:hover {
    background-color: #313244;
    border-color: #89b4fa;
}

QScrollBar:vertical {
    background-color: #1e1e2e;
    width: 8px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

USER_BUBBLE_STYLE = """
QTextBrowser {
    background-color: #89b4fa;
    color: #1e1e2e;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 13px;
}
"""

ASSISTANT_BUBBLE_STYLE = """
QTextBrowser {
    background-color: #313244;
    color: #cdd6f4;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 13px;
}
"""

SYSTEM_MSG_STYLE = """
QLabel {
    color: #6c7086;
    font-size: 11px;
    padding: 4px 8px;
}
"""

TOOL_CALL_STYLE = """
QFrame#tool_call_frame {
    background-color: #2a2a3d;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 8px;
}
QPushButton#tool_toggle {
    background-color: transparent;
    color: #94e2d5;
    border: none;
    font-size: 12px;
    font-weight: bold;
    text-align: left;
    padding: 4px;
}
QPushButton#tool_toggle:hover {
    color: #b4efe4;
}
QLabel#tool_detail {
    color: #bac2de;
    font-size: 11px;
    padding: 4px;
    font-family: "Consolas", "Courier New", monospace;
}
"""

THINKING_STYLE = """
QLabel#thinking_label {
    color: #6c7086;
    font-size: 12px;
    padding: 8px 16px;
    font-style: italic;
}
"""
