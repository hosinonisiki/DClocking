"""Qt stylesheets for the FPGA Agent chat UI."""

CHAT_WIDGET_STYLE = """
QWidget#chat_panel {
    background-color: #FBFBF9;
    border: none;
}

QScrollArea#chat_scroll_area, QScrollArea#chat_scroll_area > QWidget > QWidget {
    background-color: #FBFBF9;
    border: none;
}

QPlainTextEdit#chat_input {
    background-color: #FFFFFF;
    color: #303438;
    border: 1px solid #D8D4CE;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #85172E;
}
QPlainTextEdit#chat_input:focus {
    border: 2px solid #85172E;
}

QPushButton#send_button {
    background-color: #85172E;
    color: #FFFFFF;
    border: none;
    border-radius: 24px;
    padding: 0px;
    font-weight: bold;
    font-size: 23px;
}
QPushButton#send_button:hover {
    background-color: #9D1C38;
}
QPushButton#send_button:pressed {
    background-color: #681123;
}
QPushButton#send_button[mode="stop"] {
    background-color: #171A1C;
    font-size: 17px;
}
QPushButton#send_button[mode="stop"]:hover {
    background-color: #303438;
}
QPushButton#send_button:disabled {
    background-color: #5B5F62;
    color: #FFFFFF;
}

QPushButton#settings_button {
    background-color: transparent;
    color: #303438;
    border: 1px solid #D8D4CE;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton#settings_button:hover {
    background-color: #F2F0ED;
    border-color: #85172E;
}

QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #BDB7AF;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #8D8881;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

USER_BUBBLE_STYLE = """
QTextBrowser {
    background-color: #85172E;
    color: #FFFFFF;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 13px;
}
"""

ASSISTANT_BUBBLE_STYLE = """
QTextBrowser {
    background-color: #FFFFFF;
    color: #303438;
    border: 1px solid #D8D4CE;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 13px;
}
"""

SYSTEM_MSG_STYLE = """
QLabel {
    color: #72777B;
    font-size: 11px;
    padding: 4px 8px;
}
"""

TOOL_CALL_STYLE = """
QFrame#tool_call_frame {
    background-color: #F2F0ED;
    border: 1px solid #D8D4CE;
    border-radius: 8px;
    padding: 8px;
}
QPushButton#tool_toggle {
    background-color: transparent;
    color: #85172E;
    border: none;
    font-size: 12px;
    font-weight: bold;
    text-align: left;
    padding: 4px;
}
QPushButton#tool_toggle:hover {
    color: #9D1C38;
}
QLabel#tool_detail {
    color: #303438;
    font-size: 11px;
    padding: 4px;
    font-family: "Menlo", "Courier New", monospace;
}
"""

THINKING_STYLE = """
QLabel#thinking_label {
    color: #72777B;
    font-size: 12px;
    padding: 8px 16px;
    font-style: italic;
}
"""
