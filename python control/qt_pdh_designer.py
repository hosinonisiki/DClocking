"""PDH parameter-rule preview. This module never writes a hardware register.

The graph illustrates the *configured criteria*, not a waveform or live state.
Legacy seven-register keys and signed Q1.15 / unsigned 32-bit values are kept
unchanged until the user explicitly edits a control and requests application.
"""

import math

from PySide6.QtCore import Qt, QPoint, QRectF, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSlider, QSpinBox, QTabWidget, QToolButton, QVBoxLayout,
    QWidget,
)

__all__ = ["PDHDesignerWidget", "PDHRuleCanvas"]

_SIGNED_16_MIN = -(2**15)
_SIGNED_16_MAX = 2**15 - 1
_UINT32_MAX = 2**32 - 1
# The existing Qt/Port route accepts only the legacy signed-int UI range.
# Loading an older hardware uint32 value must remain lossless, but proposing
# a new write above this bound is unsafe until that route is upgraded.
_UI_SAFE_TIME_MAX = 2**31 - 1
_Q15_DIVISOR = 2**15


class PDHRuleCanvas(QWidget):
    """Two separate rule schematics with draggable preview-only markers."""

    marker_changed = Signal(str, int)
    _MANUAL_KEYS = ("threshold_signal_scan", "threshold_signal_lock")
    _AUTO_KEYS = ("coef_scan", "coef_lock")

    def __init__(self, view="manual", parent=None):
        super().__init__(parent)
        if view not in ("manual", "auto"):
            raise ValueError(f"Unknown PDH rule view: {view}")
        self.view = view
        self._parameters = {}
        self._drag_key = None
        self.setObjectName(f"pdh_{view}_rule_canvas")
        self.setAccessibleName(
            "PDH 配置规则示意，可拖动阈值标记，仅修改待应用预览"
            if view == "manual" else
            "PDH 自动阈值位置配置规则示意，非实时测量，可拖动标记预览"
        )
        self.setMouseTracking(True)
        self.setMinimumSize(390, 320 if view == "manual" else 290)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setToolTip("仅预览参数规则；拖动标记不会向 FPGA 写入参数")

    def set_parameters(self, parameters):
        self._parameters = dict(parameters or {})
        self.update()

    def _axis(self):
        # Keep labels and endpoints visible when the workspace is resized.
        return 74.0, max(170.0, float(self.width() - 54))

    def _value_to_x(self, value):
        left, right = self._axis()
        if self.view == "manual":
            fraction = (int(value) - _SIGNED_16_MIN) / (_SIGNED_16_MAX - _SIGNED_16_MIN)
        else:
            # The measured min/max are the *normalized* 0% and 100% marks.
            # Negative legacy Q1.15 coefficients remain visible to the left of min.
            fraction = (int(value) / _Q15_DIVISOR + 1.0) / 2.0
        return left + max(0.0, min(1.0, fraction)) * (right - left)

    def _x_to_value(self, x):
        left, right = self._axis()
        fraction = max(0.0, min(1.0, (x - left) / (right - left)))
        if self.view == "manual":
            return max(_SIGNED_16_MIN, min(_SIGNED_16_MAX, round(
                _SIGNED_16_MIN + fraction * (_SIGNED_16_MAX - _SIGNED_16_MIN)
            )))
        return max(_SIGNED_16_MIN, min(_SIGNED_16_MAX, round(
            (2.0 * fraction - 1.0) * _Q15_DIVISOR
        )))

    def marker_position(self, key):
        """The current marker center for interactive testing and accessibility."""
        keys = self._MANUAL_KEYS if self.view == "manual" else self._AUTO_KEYS
        if key not in keys or key not in self._parameters:
            return None
        row = 106 if key == keys[0] else 190
        return QPoint(round(self._value_to_x(self._parameters[key])), row)

    @staticmethod
    def marker_drag_delta(pixels):
        return QPoint(int(pixels), 0)

    def _near_marker(self, point):
        keys = self._MANUAL_KEYS if self.view == "manual" else self._AUTO_KEYS
        for key in keys:
            center = self.marker_position(key)
            if center is not None and abs(point.x() - center.x()) <= 12 and abs(point.y() - center.y()) <= 19:
                return key
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_key = self._near_marker(event.position().toPoint())
            if self._drag_key is not None:
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_key is not None:
            value = self._x_to_value(event.position().x())
            if self._parameters.get(self._drag_key) != value:
                self._parameters[self._drag_key] = value
                self.marker_changed.emit(self._drag_key, value)
                self.update()
            event.accept()
            return
        self.setCursor(
            Qt.OpenHandCursor if self._near_marker(event.position().toPoint())
            else Qt.ArrowCursor
        )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_key is not None:
            self._drag_key = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    @staticmethod
    def _pen(color, width=1.0, style=Qt.SolidLine):
        result = QPen(QColor(color))
        result.setWidthF(width)
        result.setStyle(style)
        return result

    def _text(self, painter, x, y, content, color="#243447", size=10, weight=QFont.Normal):
        font = QFont()
        font.setPointSize(size)
        font.setWeight(weight)
        painter.setFont(font)
        painter.setPen(QColor(color))
        painter.drawText(int(x), int(y), content)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#F8F9FB"))
        painter.setPen(self._pen("#D5DCE6"))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 10, 10)

        self._text(painter, 18, 27, "配置规则示意 · 非实时信号或测量", "#667485", 10, QFont.DemiBold)
        left, right = self._axis()
        painter.setPen(self._pen("#93A0AE", 1.4))
        painter.drawLine(round(left), 145, round(right), 145)
        if self.view == "manual":
            self._paint_manual(painter, left, right)
        else:
            self._paint_auto(painter, left, right)
        painter.end()
        super().paintEvent(event)

    def _paint_manual(self, painter, left, right):
        center = self._value_to_x(0)
        painter.setPen(self._pen("#D7DFE8", 1, Qt.DashLine))
        painter.drawLine(round(center), 50, round(center), 172)
        self._text(painter, left - 35, 169, "−32768", "#667485", 9)
        self._text(painter, center - 5, 169, "0", "#667485", 9)
        self._text(painter, right - 30, 169, "32767", "#667485", 9)
        self._text(painter, 18, 197, "输入信号 · ADC 原始码", "#667485")
        rows = (
            ("threshold_signal_scan", 106, "#A00039", "入锁判据 · 信号低于标记"),
            ("threshold_signal_lock", 190, "#198895", "失锁判据 · 信号高于标记"),
        )
        for key, row, color, title in rows:
            if key not in self._parameters:
                self._text(painter, 18, row - 38, f"{title}：未读取", color)
                continue
            x = self._value_to_x(self._parameters[key])
            label_y = 66 if row == 106 else 226
            self._text(painter, 18, label_y, f"{title}  {self._parameters[key]} ADC", color, 10, QFont.DemiBold)
            painter.setPen(self._pen(color, 1.5, Qt.DashLine))
            painter.drawLine(round(x), row - 38, round(x), row + 35)
            painter.setPen(self._pen(color, 2))
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawEllipse(QRectF(x - 8, row - 8, 16, 16))
            painter.setBrush(Qt.NoBrush)
        self._paint_manual_durations(painter, left, right)
        self._text(
            painter, 18, max(309, self.height() - 17),
            "条宽按对数显示，仅示意两段确认时长；精确周期数见左侧。", "#687487", 9,
        )

    def _paint_manual_durations(self, painter, left, right):
        present = [
            int(self._parameters[key])
            for key in ("time_scan", "time_lock")
            if key in self._parameters
        ]
        reference = max([0, *present])
        for key, title, label_y, color in (
            ("time_scan", "入锁 · 连续低于阈值的确认时长", 244, "#A00039"),
            ("time_lock", "失锁 · 连续高于阈值的确认时长", 281, "#198895"),
        ):
            if key not in self._parameters:
                self._text(painter, 18, label_y, f"{title}：未读取", color, 10)
                continue
            cycles = max(0, int(self._parameters[key]))
            self._text(
                painter, 18, label_y, f"{title}  {cycles:,} 周期",
                color, 10, QFont.DemiBold,
            )
            bar_y = label_y + 10
            background = QRectF(left, bar_y, right - left, 9)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#E1E7ED"))
            painter.drawRoundedRect(background, 4.5, 4.5)
            if cycles > 0 and reference > 0:
                fraction = math.log1p(cycles) / math.log1p(reference)
                painter.setBrush(QColor(color))
                painter.drawRoundedRect(
                    QRectF(left, bar_y, max(2.0, (right - left) * fraction), 9),
                    4.5, 4.5,
                )
            painter.setBrush(Qt.NoBrush)

    def _paint_auto(self, painter, left, right):
        middle = self._value_to_x(0)
        self._text(painter, left - 29, 169, "−100%", "#667485", 9)
        self._text(painter, middle - 12, 169, "0% 最小值", "#667485", 9)
        self._text(painter, right - 37, 169, "100% 最大值", "#667485", 9)
        painter.setPen(self._pen("#CBD3DD", 1, Qt.DashLine))
        painter.drawLine(round(middle), 50, round(middle), 155)
        rows = (
            ("coef_scan", 106, "#A00039", "自动入锁阈值位置"),
            ("coef_lock", 190, "#198895", "自动失锁阈值位置"),
        )
        for key, row, color, title in rows:
            if key not in self._parameters:
                self._text(painter, 18, row - 38, f"{title}：未读取", color)
                continue
            raw = int(self._parameters[key])
            percent = raw / _Q15_DIVISOR * 100.0
            x = self._value_to_x(raw)
            label_y = 66 if row == 106 else 226
            self._text(
                painter, 18, label_y,
                f"{title}  {percent:.3f}% · Q1.15 {raw}", color, 10, QFont.DemiBold,
            )
            painter.setPen(self._pen(color, 1.5, Qt.DashLine))
            painter.drawLine(round(x), row - 38, round(x), row + 35)
            painter.setPen(self._pen(color, 2))
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawEllipse(QRectF(x - 8, row - 8, 16, 16))
            painter.setBrush(Qt.NoBrush)
        self._text(
            painter, 18, max(251, self.height() - 26),
            "阈值 = 测得最小值 + (最大值 − 最小值) × 原值 / 32768", "#687487", 9,
        )


class PDHDesignerWidget(QWidget):
    """Named PDH criteria and staged editors, compatible with the original ABI."""

    # The native time registers are uint32; Qt's Signal(int) truncates above 2**31-1.
    parameter_preview_changed = Signal(str, object)
    apply_requested = Signal(dict)
    command_requested = Signal(int)
    refresh_requested = Signal()

    _MANUAL_KEYS = ("threshold_signal_scan", "time_scan", "threshold_signal_lock", "time_lock")
    _AUTO_KEYS = ("coef_scan", "coef_lock")
    _TIME_DISPLAY_NAMES = {
        "time_scan": "入锁确认时长",
        "time_lock": "失锁确认时长",
    }
    _COMMAND_LABELS = {
        0: "00 · 空闲／复位请求",
        1: "01 · 手动锁定模式启动请求",
        2: "10 · 自动锁定模式启动请求",
        3: "11 · 特定自动退出指令（高级兼容值）",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pdh_designer_widget")
        self.setAccessibleName("PDH 状态机参数规则设计工作台")
        self.setMinimumSize(890, 600)
        self._baseline = {}
        self._preview = {}
        self._invalid_fields = set()
        self._syncing = False
        self._source_label = "未读取"
        self._conflict_message = None
        self._clock_hz = None
        self._build_ui()
        self.set_parameters({}, source_label="未读取")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(3)
        title = QLabel("PDH · 状态机判据设计")
        title.setObjectName("pdh_designer_title")
        heading.addWidget(title)
        subtitle = QLabel("只编辑现有参数 · 曲线为规则示意，非实际信号")
        subtitle.setObjectName("pdh_designer_subtitle")
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()
        self.refresh_button = QPushButton("刷新参数", self)
        self.refresh_button.setObjectName("pdh_refresh_button")
        self.refresh_button.setAccessibleName("请求重新读取 PDH 参数")
        self.refresh_button.setToolTip(
            "请求主窗口重新读取当前设备／节点参数；成功刷新后会丢弃未应用更改，"
            "读取失败时预览保留。点击本按钮本身不会清空或写入任何参数。"
        )
        self.refresh_button.clicked.connect(self._request_refresh)
        header.addWidget(self.refresh_button)
        self.source_badge = QLabel("参数来源：未读取")
        self.source_badge.setObjectName("pdh_source_badge")
        header.addWidget(self.source_badge)
        root.addLayout(header)

        self.command_label = QLabel("控制请求：未读取 · 请求码不是当前硬件状态")
        self.command_label.setObjectName("pdh_command_label")
        root.addWidget(self.command_label)
        root.addWidget(self._build_command_panel())

        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("pdh_designer_tabs")
        root.addWidget(self.tabs, 1)
        self.manual_canvas = PDHRuleCanvas("manual", self)
        self.auto_canvas = PDHRuleCanvas("auto", self)
        self.tabs.addTab(self._build_manual_tab(), "手动判据")
        self.tabs.addTab(self._build_auto_tab(), "自动校准")

        footer = QHBoxLayout()
        self.feedback = QLabel("从硬件读取参数后才可确认当前设置。")
        self.feedback.setObjectName("pdh_designer_feedback")
        self.feedback.setWordWrap(True)
        footer.addWidget(self.feedback, 1)
        self.apply_button = QPushButton("应用修改")
        self.apply_button.setObjectName("pdh_apply_button")
        self.apply_button.setProperty("variant", "primary")
        self.apply_button.setAccessibleName("应用待修改的 PDH 寄存器参数")
        self.apply_button.clicked.connect(self._request_apply)
        footer.addWidget(self.apply_button)
        root.addLayout(footer)

        self.setStyleSheet(
            "QWidget#pdh_designer_widget { background: #FFFFFF; color: #243447; }"
            "QLabel#pdh_designer_title { color: #253447; font-size: 21px; font-weight: 750; }"
            "QLabel#pdh_designer_subtitle, QLabel#pdh_command_label { color: #697584; font-size: 11px; }"
            "QLabel#pdh_source_badge { background: #F4F5F6; border: 1px solid #D8DBDF; "
            "border-radius: 8px; color: #576474; padding: 8px 11px; font-size: 11px; }"
            "QPushButton#pdh_refresh_button { background: #FFFFFF; border: 1px solid #CAD0D7; "
            "border-radius: 6px; min-height: 25px; color: #283948; padding: 4px 10px; }"
            "QPushButton#pdh_refresh_button:hover { color: #9B0036; border-color: #9B0036; }"
            "QLabel#pdh_designer_feedback { color: #708091; font-size: 11px; }"
            "QFrame#pdh_command_panel { background: #F7F8FA; border: 1px solid #D9DEE5; "
            "border-radius: 7px; }"
            "QLabel#pdh_command_title { color: #283948; font-size: 12px; font-weight: 700; "
            "border: none; }"
            "QLabel#pdh_command_warning { color: #8F3552; font-size: 10px; border: none; }"
            "QLabel#pdh_command_request_feedback, QLabel#pdh_command_advanced_detail { "
            "color: #667485; font-size: 10px; border: none; }"
            "QPushButton[pdhCommand=true] { background: #FFFFFF; border: 1px solid #CAD0D7; "
            "border-radius: 5px; color: #283948; padding: 5px 12px; min-height: 26px; }"
            "QPushButton[pdhCommand=true]:hover { border-color: #9B0036; color: #9B0036; }"
            "QPushButton[pdhCommand=true]:disabled { background: #ECEFF2; color: #9FA8B2; "
            "border-color: #DDE2E8; }"
            "QToolButton#pdh_command_advanced_toggle { color: #9B0036; border: none; "
            "font-size: 10px; font-weight: 600; padding: 3px; }"
            "QLabel#pdh_section_title { font-size: 14px; font-weight: 700; color: #283948; }"
            "QLabel#pdh_field_hint, QLabel#pdh_duration_hint { color: #748292; font-size: 10px; }"
            "QLineEdit, QSpinBox, QDoubleSpinBox { min-height: 27px; background: #FFFFFF; "
            "border: 1px solid #CAD0D7; border-radius: 5px; padding: 2px 7px; color: #283948; }"
            "QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #9B0036; }"
            "QPushButton#pdh_apply_button { background: #9B0036; color: #FFFFFF; "
            "border: none; border-radius: 6px; min-height: 35px; min-width: 110px; "
            "font-size: 12px; font-weight: 700; padding: 4px 14px; }"
            "QPushButton#pdh_apply_button:disabled { background: #D7D0D3; color: #797579; }"
            "QTabWidget#pdh_designer_tabs::pane { border: 1px solid #D9DEE5; border-radius: 8px; }"
            "QTabBar::tab { padding: 8px 18px; color: #6A7580; }"
            "QTabBar::tab:selected { color: #9B0036; font-weight: 700; }"
            "QSlider::groove:horizontal { height: 6px; background: #DDE2E8; border-radius: 3px; }"
            "QSlider::sub-page:horizontal { background: #9B0036; border-radius: 3px; }"
            "QSlider::handle:horizontal { width: 17px; height: 17px; margin: -6px 0; "
            "background: white; border: 2px solid #9B0036; border-radius: 8px; }"
        )

    def _build_command_panel(self):
        panel = QFrame(self)
        panel.setObjectName("pdh_command_panel")
        panel.setAccessibleName("PDH 控制请求，与参数编辑和应用分离")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(4)

        top = QHBoxLayout()
        heading = QLabel("控制请求 · 不代表当前硬件状态", panel)
        heading.setObjectName("pdh_command_title")
        top.addWidget(heading)
        top.addStretch()
        self.command_advanced_toggle = QToolButton(panel)
        self.command_advanced_toggle.setObjectName("pdh_command_advanced_toggle")
        self.command_advanced_toggle.setAccessibleName("展开兼容指令 11 的真实语义")
        self.command_advanced_toggle.setText("高级说明 ▸")
        self.command_advanced_toggle.setCheckable(True)
        self.command_advanced_toggle.toggled.connect(self._toggle_advanced_help)
        top.addWidget(self.command_advanced_toggle)
        layout.addLayout(top)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self._command_buttons = []
        for value, object_name, label, explanation in (
            (
                0, "pdh_command_idle_button", "待机请求 (00)",
                "发出 pc_cmd=00 请求；现有状态机不保证所有状态立即停止，需确认硬件后续行为。",
            ),
            (
                1, "pdh_command_manual_button", "手动锁定模式 (01)",
                "请求发送 pc_cmd=01 手动锁定模式启动请求；仅空闲状态识别 00→01 边沿，"
                "先进入扫描阶段，不表示已锁定。",
            ),
            (
                2, "pdh_command_auto_button", "自动锁定模式 (10)",
                "请求发送 pc_cmd=10 自动锁定模式启动请求；仅空闲状态识别 00→10 边沿，"
                "先进入自动校准流程，不表示已锁定。",
            ),
        ):
            button = QPushButton(label, panel)
            button.setObjectName(object_name)
            button.setProperty("pdhCommand", True)
            button.setAccessibleName(label)
            button.setToolTip(explanation)
            button.clicked.connect(
                lambda _checked=False, command=value: self._request_command(command)
            )
            buttons.addWidget(button)
            self._command_buttons.append(button)
        buttons.addStretch()
        layout.addLayout(buttons)

        warning = QLabel(
            "启动仅在空闲态识别 00→01／10 边沿；00 是待机请求，现有逻辑不保证任何状态立即停止。",
            panel,
        )
        warning.setObjectName("pdh_command_warning")
        warning.setWordWrap(True)
        layout.addWidget(warning)

        self.command_request_feedback = QLabel("尚未发出控制请求。", panel)
        self.command_request_feedback.setObjectName("pdh_command_request_feedback")
        layout.addWidget(self.command_request_feedback)

        self.command_advanced_detail = QLabel(
            "11：仅在 AUTO_LOCKING 中，信号高于自动失锁阈值并持续达到确认周期后，"
            "才允许退出到 IDLE。它不是第四种启动模式或即时停止；"
            "旧参数编辑方式仍保留此兼容值。",
            panel,
        )
        self.command_advanced_detail.setObjectName("pdh_command_advanced_detail")
        self.command_advanced_detail.setWordWrap(True)
        self.command_advanced_detail.hide()
        layout.addWidget(self.command_advanced_detail)
        return panel

    def _toggle_advanced_help(self, expanded):
        self.command_advanced_detail.setVisible(bool(expanded))
        self.command_advanced_toggle.setText(
            "收起说明 ▾" if expanded else "高级说明 ▸"
        )

    def _request_command(self, value):
        # Emit an intent only. The MainWindow owns validation, transport, and
        # device confirmation; never write from a graph or change the baseline.
        if self._conflict_message is not None:
            return
        value = int(value)
        self.command_request_feedback.setText(
            f"已发出 {self._COMMAND_LABELS[value]}；等待控制器处理／设备确认。"
        )
        self.command_requested.emit(value)

    def _tab_layout(self):
        tab = QWidget(self.tabs)
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(16, 18, 16, 16)
        layout.setSpacing(18)
        form = QWidget(tab)
        form.setMinimumWidth(310)
        form.setMaximumWidth(390)
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(13)
        layout.addWidget(form, 0)
        return tab, layout, form_layout

    @staticmethod
    def _section_title(content, parent=None):
        result = QLabel(content, parent)
        result.setObjectName("pdh_section_title")
        return result

    @staticmethod
    def _field_hint(content, parent=None):
        result = QLabel(content, parent)
        result.setObjectName("pdh_field_hint")
        result.setWordWrap(True)
        return result

    def _build_manual_tab(self):
        tab, layout, form = self._tab_layout()
        for title, threshold_key, duration_key, condition in (
            ("入锁 · 从扫描切换到锁定", "threshold_signal_scan", "time_scan", "信号连续低于阈值"),
            ("失锁 · 从锁定退出", "threshold_signal_lock", "time_lock", "信号连续高于阈值"),
        ):
            form.addWidget(self._section_title(title, tab))
            grid = QGridLayout()
            grid.setHorizontalSpacing(7)
            grid.setVerticalSpacing(7)
            threshold_label = QLabel("振幅阈值", tab)
            threshold = QSpinBox(tab)
            threshold.setRange(_SIGNED_16_MIN, _SIGNED_16_MAX)
            threshold.setObjectName(f"pdh_{threshold_key}")
            threshold.setAccessibleName(f"{title} 振幅阈值 ADC 原始码")
            threshold.setToolTip(f"{condition}；原值为有符号 16 位 ADC 码")
            threshold.valueChanged.connect(
                lambda value, key=threshold_key: self._preview_changed(key, value)
            )
            duration_label = QLabel("确认时长", tab)
            duration = QLineEdit(tab)
            duration.setObjectName(f"pdh_{duration_key}_cycles")
            duration.setAccessibleName(f"{title} 确认持续的时钟周期数")
            duration.setMaxLength(10)
            duration.setPlaceholderText("未读取")
            duration.setToolTip(
                "可显示／保留完整无符号 32 位历史原值；当前界面新写入兼容安全上限为 "
                "2147483647 周期"
            )
            duration.textChanged.connect(
                lambda text, key=duration_key: self._duration_changed(key, text)
            )
            clock_hint = QLabel("未确认板卡时钟 · 周期值优先", tab)
            clock_hint.setObjectName("pdh_duration_hint")
            clock_hint.setWordWrap(True)
            setattr(self, f"_{duration_key}_hint", clock_hint)
            grid.addWidget(threshold_label, 0, 0)
            grid.addWidget(threshold, 0, 1)
            grid.addWidget(QLabel("ADC 码", tab), 0, 2)
            grid.addWidget(duration_label, 1, 0)
            grid.addWidget(duration, 1, 1)
            grid.addWidget(QLabel("周期", tab), 1, 2)
            grid.addWidget(clock_hint, 2, 1, 1, 2)
            form.addLayout(grid)
            form.addWidget(self._field_hint(f"{condition}，并持续达到确认时长才切换；等于阈值不计入。", tab))
            setattr(self, f"_{threshold_key}_editor", threshold)
            setattr(self, f"_{duration_key}_editor", duration)
        form.addStretch()
        layout.addWidget(self.manual_canvas, 1)
        self.manual_canvas.marker_changed.connect(self._manual_marker_changed)
        return tab

    def _build_auto_tab(self):
        tab, layout, form = self._tab_layout()
        form.addWidget(self._field_hint(
            "阈值位置由状态机测得的最小值、最大值与 Q1.15 系数计算；"
            "本图仅显示设置的位置，不展示未经回读的测量结果。", tab
        ))
        for title, key in (
            ("自动入锁阈值位置", "coef_scan"),
            ("自动失锁阈值位置", "coef_lock"),
        ):
            form.addWidget(self._section_title(title, tab))
            percent_row = QHBoxLayout()
            percent_row.addWidget(QLabel("位置", tab))
            percent = QDoubleSpinBox(tab)
            percent.setObjectName(f"pdh_{key}_percent")
            percent.setRange(-100.0, _SIGNED_16_MAX / _Q15_DIVISOR * 100.0)
            percent.setDecimals(3)
            percent.setSingleStep(0.1)
            percent.setSuffix(" %")
            percent.setAccessibleName(f"{title}，以百分比显示 Q1.15 原始值")
            percent.valueChanged.connect(
                lambda value, parameter_key=key: self._percent_changed(parameter_key, value)
            )
            percent_row.addWidget(percent, 1)
            form.addLayout(percent_row)
            slider = QSlider(Qt.Horizontal, tab)
            slider.setObjectName(f"pdh_{key}_slider")
            slider.setRange(_SIGNED_16_MIN, _SIGNED_16_MAX)
            slider.setAccessibleName(f"滑动预览{title}，不直接写硬件")
            slider.setToolTip("滑动只改预览；负比例为旧格式允许的原始值，位于测量最小值外侧")
            slider.valueChanged.connect(
                lambda value, parameter_key=key: self._preview_changed(parameter_key, value)
            )
            form.addWidget(slider)
            raw_row = QHBoxLayout()
            raw_row.addWidget(QLabel("原始 Q1.15", tab))
            raw = QSpinBox(tab)
            raw.setObjectName(f"pdh_{key}_raw")
            raw.setRange(_SIGNED_16_MIN, _SIGNED_16_MAX)
            raw.setAccessibleName(f"{title} Q1.15 原始寄存器值")
            raw.valueChanged.connect(
                lambda value, parameter_key=key: self._preview_changed(parameter_key, value)
            )
            raw_row.addWidget(raw, 1)
            form.addLayout(raw_row)
            setattr(self, f"_{key}_percent", percent)
            setattr(self, f"_{key}_slider", slider)
            setattr(self, f"_{key}_raw", raw)
        self.auto_warning = self._field_hint("配置示意；不是当前 FPGA 阈值。", tab)
        self.auto_warning.setObjectName("pdh_auto_warning")
        form.addWidget(self.auto_warning)
        form.addStretch()
        layout.addWidget(self.auto_canvas, 1)
        self.auto_canvas.marker_changed.connect(self._auto_marker_changed)
        return tab

    @staticmethod
    def _normalized_parameters(parameters):
        result = dict(parameters or {})
        for key in (*PDHDesignerWidget._MANUAL_KEYS, *PDHDesignerWidget._AUTO_KEYS, "pc_cmd"):
            if key in result:
                try:
                    result[key] = int(result[key])
                except (ValueError, TypeError, OverflowError):
                    # Unparseable persisted values must not be silently converted to 0.
                    raise ValueError(f"PDH 参数 {key} 无法解析为原始整数值") from None
        return result

    def set_parameters(self, parameters, source_label="本地配置", clock_hz=None):
        """Refresh from a named source; never infer live FPGA state from a cache."""
        parsed = self._normalized_parameters(parameters)
        self._syncing = True
        try:
            self._baseline = dict(parsed)
            self._preview = dict(parsed)
            self._invalid_fields.clear()
            self._conflict_message = None
            self._source_label = str(source_label or "未读取")
            try:
                clock = float(clock_hz)
                self._clock_hz = clock if math.isfinite(clock) and clock > 0.0 else None
            except (ValueError, TypeError, OverflowError):
                self._clock_hz = None
            self.source_badge.setText(f"参数来源：{self._source_label}")
            self.source_badge.setStyleSheet("")
            for button in self._command_buttons:
                button.setEnabled(True)
            self.command_label.setText(
                f"控制请求：{self._COMMAND_LABELS.get(parsed['pc_cmd'], parsed['pc_cmd'])} · 请求码不是当前硬件状态"
                if "pc_cmd" in parsed else
                "控制请求：未读取 · 请求码不是当前硬件状态"
            )
            for key in ("threshold_signal_scan", "threshold_signal_lock"):
                editor = getattr(self, f"_{key}_editor")
                editor.setEnabled(key in parsed)
                if key in parsed:
                    editor.setValue(parsed[key])
            for key in ("time_scan", "time_lock"):
                editor = getattr(self, f"_{key}_editor")
                editor.setEnabled(key in parsed)
                editor.setText(str(parsed[key]) if key in parsed else "")
                self._update_duration_hint(key)
            for key in self._AUTO_KEYS:
                enabled = key in parsed
                raw_value = int(parsed.get(key, 0))
                for suffix in ("percent", "slider", "raw"):
                    getattr(self, f"_{key}_{suffix}").setEnabled(enabled)
                if enabled:
                    getattr(self, f"_{key}_raw").setValue(raw_value)
                    getattr(self, f"_{key}_slider").setValue(raw_value)
                    getattr(self, f"_{key}_percent").setValue(
                        raw_value / _Q15_DIVISOR * 100.0
                    )
            self.manual_canvas.set_parameters(self._preview)
            self.auto_canvas.set_parameters(self._preview)
            self._update_warning()
            self.feedback.setText(
                "规则设置已刷新；无硬件状态回读时不显示“实时锁定状态”。"
            )
            self.feedback.setStyleSheet("")
            self._update_apply_button()
        finally:
            self._syncing = False

    def mark_conflict(self, message):
        """Retain pending values while locking writes against an unverified node."""
        self._conflict_message = str(message or "当前设备／节点来源未核对")
        self._source_label = "待核对"
        self.source_badge.setText("参数来源：待核对")
        self.source_badge.setStyleSheet(
            "color: #9B0036; background: #FFF1F5; border: 1px solid #D89AB0;"
        )
        for button in self._command_buttons:
            button.setEnabled(False)
        self.feedback.setText(
            f"参数来源待核对：{self._conflict_message}。待应用预览已保留；"
            "请刷新参数并确认当前节点后再操作。"
        )
        self.feedback.setStyleSheet("color: #9B0036; font-weight: 600;")
        self._update_apply_button()

    def update_command_value(self, command):
        """Update the displayed request from its named source; keep rule edits."""
        value = int(command)
        self._baseline["pc_cmd"] = value
        self._preview["pc_cmd"] = value
        self.command_label.setText(
            f"控制请求：{self._COMMAND_LABELS.get(value, value)} · 请求码不是当前硬件状态"
        )

    def _request_refresh(self):
        if self._conflict_message is not None:
            self.feedback.setText(
                f"已请求重新读取以核对：{self._conflict_message}。"
                "读取失败时预览保留；成功刷新后会丢弃未应用更改。"
            )
        else:
            self.feedback.setText(
                "已请求重新读取当前设备／节点参数；读取失败时预览保留，"
                "成功刷新后会丢弃未应用更改。"
            )
        self.refresh_requested.emit()

    def preview_parameters(self):
        return dict(self._preview)

    def baseline_parameters(self):
        return dict(self._baseline)

    def staged_parameters(self):
        return {
            key: int(self._preview[key])
            for key in (*self._MANUAL_KEYS, *self._AUTO_KEYS)
            if key in self._preview and self._preview.get(key) != self._baseline.get(key)
        }

    def _update_duration_hint(self, key):
        label = getattr(self, f"_{key}_hint")
        if key not in self._preview:
            label.setText("未读取 · 时间不能推算")
            return
        cycles = self._preview[key]
        legacy_note = (
            " · 超过当前界面新写入安全上限，仅保留历史值"
            if cycles > _UI_SAFE_TIME_MAX and self._preview.get(key) == self._baseline.get(key)
            else ""
        )
        if self._clock_hz is None:
            label.setText(f"{cycles:,} 周期 · 未确认板卡时钟{legacy_note}")
        else:
            label.setText(
                f"{cycles:,} 周期 ≈ {cycles / self._clock_hz * 1000.0:.3g} ms"
                f" · 按 {self._clock_hz / 1e6:g} MHz 换算{legacy_note}"
            )

    def _update_warning(self):
        outside = [
            key for key in self._AUTO_KEYS
            if key in self._preview and self._preview[key] < 0
        ]
        if outside:
            self.auto_warning.setText(
                "注意：历史系数超出常用 0–100% 区间，原始 Q1.15 值已保留；"
                "图中标记位于测量最小值外侧。"
            )
            self.auto_warning.setStyleSheet("color: #9B0036; font-size: 10px; font-weight: 600;")
        else:
            self.auto_warning.setText(
                "0–100% 为测量最小值到最大值的位置；曲线不是实时测量。"
            )
            self.auto_warning.setStyleSheet("color: #748292; font-size: 10px;")

    def _update_apply_button(self):
        self.apply_button.setEnabled(
            bool(self.staged_parameters())
            and not self._invalid_fields
            and self._conflict_message is None
        )
        self.apply_button.setToolTip(
            "参数来源待核对，已锁定应用；请刷新参数确认节点。"
            if self._conflict_message is not None else
            f"来源：{self._source_label}；点击后才请求应用；拖动和输入只更新预览"
        )

    def _preview_changed(self, key, value):
        if self._syncing:
            return
        value = int(value)
        if self._preview.get(key) == value:
            return
        self._preview[key] = value
        if key in self._AUTO_KEYS:
            for suffix, normalized in (
                ("raw", value), ("slider", value),
                ("percent", value / _Q15_DIVISOR * 100.0),
            ):
                editor = getattr(self, f"_{key}_{suffix}")
                editor.blockSignals(True)
                editor.setValue(normalized)
                editor.blockSignals(False)
        self.manual_canvas.set_parameters(self._preview)
        self.auto_canvas.set_parameters(self._preview)
        self._update_warning()
        self._update_apply_button()
        self.parameter_preview_changed.emit(key, value)

    def _percent_changed(self, key, percentage):
        if self._syncing:
            return
        value = round(float(percentage) / 100.0 * _Q15_DIVISOR)
        value = max(_SIGNED_16_MIN, min(_SIGNED_16_MAX, value))
        self._preview_changed(key, value)

    def _duration_changed(self, key, text):
        if self._syncing:
            return
        display_name = self._TIME_DISPLAY_NAMES.get(key, key)
        # Do not strip Unicode whitespace into a valid-looking integer.
        if not text or len(text) > 10 or not all("0" <= character <= "9" for character in text):
            self._invalid_fields.add(key)
            self.feedback.setText(
                f"{display_name}仅允许 ASCII 数字 0–9；请以完整时钟周期整数输入。"
            )
            self.feedback.setStyleSheet("color: #9B0036; font-weight: 600;")
            self._update_apply_button()
            return
        cycles = int(text)
        if cycles > _UINT32_MAX:
            self._invalid_fields.add(key)
            self.feedback.setText(
                f"{display_name}超出硬件 uint32 范围 0–4294967295；"
                "当前界面兼容安全上限为 2147483647 周期。"
            )
            self.feedback.setStyleSheet("color: #9B0036; font-weight: 600;")
            self._update_apply_button()
            return
        if cycles > _UI_SAFE_TIME_MAX and cycles == self._baseline.get(key):
            # Returning to an unchanged historical readback is not a new
            # write. It must not block an unrelated safe field modification.
            self._invalid_fields.discard(key)
            self._preview_changed(key, cycles)
            self._update_duration_hint(key)
            self.feedback.setText(
                f"{display_name}的历史 uint32 原值已保留；仅变更字段会在点击应用时提交。"
            )
            self.feedback.setStyleSheet("")
            self._update_apply_button()
            return
        if cycles > _UI_SAFE_TIME_MAX:
            # Keep the full proposed value visible in the preview, but never
            # dispatch it through the current signed-int UI/transport route.
            self._invalid_fields.add(key)
            self._preview_changed(key, cycles)
            self._update_duration_hint(key)
            self.feedback.setText(
                f"{display_name}已保留为待应用预览；当前界面兼容安全上限为 "
                "2147483647 周期，超限值不能应用。历史设备值可原样显示。"
            )
            self.feedback.setStyleSheet("color: #9B0036; font-weight: 600;")
            self._update_apply_button()
            return
        self._invalid_fields.discard(key)
        self._preview_changed(key, cycles)
        self._update_duration_hint(key)
        self.feedback.setText("待应用预览 · FPGA 参数尚未写入。")
        self.feedback.setStyleSheet("")
        self._update_apply_button()

    def _manual_marker_changed(self, key, value):
        editor = getattr(self, f"_{key}_editor")
        editor.setValue(value)

    def _auto_marker_changed(self, key, value):
        editor = getattr(self, f"_{key}_raw")
        editor.setValue(value)

    def _request_apply(self):
        pending = self.staged_parameters()
        if self._conflict_message is not None or self._invalid_fields or not pending:
            return
        self.feedback.setText("已请求应用；等待写入结果／设备参数回读，不能据此认定已生效。")
        self.apply_requested.emit(pending)

    def set_apply_result(self, success, message=""):
        """Report controller feedback without silently changing baseline values."""
        if self._conflict_message is not None:
            self.mark_conflict(self._conflict_message)
            return
        if success:
            self.feedback.setText(
                f"写入请求已处理。{message} 请回读设备后确认实际值。"
            )
        else:
            self.feedback.setText(
                f"应用未确认：{message or '请检查设备连接与运行日志'}；预览保留，可重新尝试。"
            )
        self._update_apply_button()
