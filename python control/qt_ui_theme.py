"""Visual tokens and shared painting helpers for the DClocking workstation."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QFontDatabase, QPainter, QPen


class UiColors:
    PKU_WINE = "#85172E"
    PKU_WINE_HOVER = "#9D1C38"
    PKU_WINE_PRESSED = "#681123"
    ERROR = "#D2556E"
    SURFACE = "#FBFBF9"
    SURFACE_ALT = "#F2F0ED"
    SURFACE_RAISED = "#FFFFFF"
    BORDER = "#D8D4CE"
    BORDER_STRONG = "#BDB7AF"
    TEXT = "#303438"
    TEXT_MUTED = "#72777B"
    TEXT_ON_DARK = "#F5F5F2"
    CANVAS_BG = "#171B1D"
    CANVAS_GRID = "#31383B"
    NODE_BG = "#272D30"
    NODE_HEADER = "#30373A"
    NODE_BORDER = "#4B565B"
    PORT_INPUT = "#45B991"
    PORT_OUTPUT = "#E05B62"
    STATUS_OK = "#2F9A73"
    WARNING = "#D99A34"


def _ui_font_family() -> str:
    available = set(QFontDatabase.families())
    for family in ("Helvetica Neue", "PingFang SC", ".AppleSystemUIFont"):
        if family in available:
            return family
    return ".AppleSystemUIFont"


def build_application_stylesheet() -> str:
    c = UiColors
    return f"""
QMainWindow, QWidget {{
    color: {c.TEXT};
    background: {c.SURFACE};
}}
QWidget#left_rail {{
    background: {c.PKU_WINE};
    border: none;
}}
QWidget#command_bar {{
    background: {c.SURFACE_RAISED};
    border-bottom: 1px solid {c.BORDER};
}}
QFrame#canvas_frame {{
    background: {c.CANVAS_BG};
    border: none;
}}
QWidget#inspector_panel, QFrame#inspector_panel {{
    background: {c.SURFACE};
    border-left: 1px solid {c.BORDER};
}}
QFrame#status_bar {{
    background: {c.SURFACE_ALT};
    border-top: 1px solid {c.BORDER};
}}
QLabel {{
    background: transparent;
}}
QLabel[role="eyebrow"] {{
    color: {c.TEXT_MUTED};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel[role="sectionTitle"] {{
    color: {c.TEXT};
    font-size: 13px;
    font-weight: 700;
}}
QPushButton, QToolButton {{
    min-height: 30px;
    padding: 0 12px;
    color: {c.TEXT};
    background: {c.SURFACE_RAISED};
    border: 1px solid {c.BORDER};
    border-radius: 7px;
    font-weight: 600;
}}
QPushButton:hover, QToolButton:hover {{
    border-color: {c.BORDER_STRONG};
    background: {c.SURFACE_ALT};
}}
QPushButton:pressed, QToolButton:pressed {{
    background: {c.BORDER};
}}
QPushButton:focus, QToolButton:focus, QComboBox:focus,
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{
    border: 2px solid {c.PKU_WINE};
}}
QPushButton:disabled, QToolButton:disabled, QComboBox:disabled {{
    color: #AAA8A3;
    background: #EEECE8;
    border-color: #DDD9D3;
}}
QPushButton[variant="primary"], QToolButton[variant="primary"],
QPushButton#agent_toggle_button:checked, QToolButton#agent_toggle_button:checked {{
    color: white;
    background: {c.PKU_WINE};
    border-color: {c.PKU_WINE};
}}
QPushButton[variant="primary"]:hover, QToolButton[variant="primary"]:hover {{
    background: {c.PKU_WINE_HOVER};
}}
QPushButton[variant="primary"]:pressed, QToolButton[variant="primary"]:pressed {{
    background: {c.PKU_WINE_PRESSED};
}}
QToolButton[rail="true"] {{
    min-width: 46px;
    min-height: 46px;
    padding: 0;
    color: white;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    font-size: 18px;
}}
QToolButton[rail="true"]:hover {{
    background: rgba(255, 255, 255, 35);
}}
QToolButton[rail="true"]:checked {{
    color: {c.PKU_WINE};
    background: white;
}}
QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {{
    min-height: 30px;
    padding: 0 10px;
    background: {c.SURFACE_RAISED};
    border: 1px solid {c.BORDER};
    border-radius: 7px;
    selection-background-color: {c.PKU_WINE};
}}
QComboBox::drop-down {{
    width: 24px;
    border: none;
}}
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    min-height: 29px;
    padding: 2px 8px;
    border-radius: 5px;
}}
QListWidget::item:hover {{
    background: {c.SURFACE_ALT};
}}
QListWidget::item:selected {{
    color: {c.PKU_WINE};
    background: #F3E7EA;
}}
QScrollArea, QPlainTextEdit, QTextEdit {{
    background: {c.SURFACE_RAISED};
    border: 1px solid {c.BORDER};
    border-radius: 6px;
}}
QScrollBar:vertical {{
    width: 9px;
    margin: 2px;
    background: transparent;
}}
QScrollBar::handle:vertical {{
    min-height: 28px;
    background: {c.BORDER_STRONG};
    border-radius: 4px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0;
    height: 0;
}}
QSplitter::handle {{
    width: 1px;
    height: 1px;
    background: {c.BORDER};
}}
QTabWidget::pane {{
    border: none;
}}
QTabBar::tab {{
    padding: 8px 12px;
    color: {c.TEXT_MUTED};
    background: transparent;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    color: {c.PKU_WINE};
    border-bottom-color: {c.PKU_WINE};
}}
QToolTip {{
    color: white;
    background: {c.NODE_BG};
    border: 1px solid {c.NODE_BORDER};
    padding: 5px;
}}
QDockWidget {{
    color: {c.TEXT};
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}
"""


def apply_application_theme(widget) -> None:
    font = QFont(_ui_font_family(), 12)
    widget.setFont(font)
    widget.setStyleSheet(build_application_stylesheet())


def draw_node_chrome(
    painter: QPainter, rect: QRectF, selected: bool = False
) -> None:
    border = UiColors.ERROR if selected else UiColors.NODE_BORDER
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setBrush(QBrush(QColor(UiColors.NODE_BG)))
    painter.setPen(QPen(QColor(border), 2 if selected else 1))
    painter.drawRoundedRect(rect, 8, 8)

    header = QRectF(rect.left(), rect.top(), rect.width(), min(28.0, rect.height()))
    painter.setBrush(QBrush(QColor(UiColors.NODE_HEADER)))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(header, 8, 8)
    painter.drawRect(QRectF(header.left(), header.bottom() - 8, header.width(), 8))
    painter.setBrush(QBrush(QColor(UiColors.PKU_WINE)))
    painter.drawRoundedRect(
        QRectF(rect.left() + 8, rect.top() + 7, 4, 14), 2, 2
    )
    painter.restore()
