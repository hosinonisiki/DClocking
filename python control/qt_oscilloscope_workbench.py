"""Windows-first oscilloscope workbench with simulator and legacy UDP modes."""

from __future__ import annotations

import math
import socket
import time

import numpy as np
from PySide6.QtCore import QPointF, QRectF, QSettings, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtNetwork import QAbstractSocket, QNetworkInterface
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from oscilloscope_model import ScopeSampleBuffer
from oscilloscope_protocol import LegacyUdpScopeProtocol, ScopeProtocolError
from oscilloscope_transport import ScopeEndpointConfig, UdpScopeReceiver
from qt_ui_theme import UiColors


class ScopePlotWidget(QWidget):
    """Paint peak-preserving waveform envelopes without a plotting dependency."""

    CHANNEL_COLORS = ("#16C7A5", "#FFB347", "#6EA8FF", "#D978E8")

    def __init__(self, sample_buffer: ScopeSampleBuffer, parent=None):
        super().__init__(parent)
        self.sample_buffer = sample_buffer
        self.sample_rate_hz = 32_000_000.0
        self.visible_samples = 4_096
        self.channel_visible = [True, True, True, True]
        self.channel_gain = [1.0, 1.0, 1.0, 1.0]
        self.channel_offset = [1.5, 0.5, -0.5, -1.5]
        self.trigger_level = 0.0
        self.setObjectName("oscilloscope_plot")
        self.setAccessibleName("实时示波器波形显示")
        self.setMinimumSize(620, 400)
        self.setMouseTracking(True)

    def set_channel_visible(self, channel: int, visible: bool) -> None:
        self.channel_visible[int(channel)] = bool(visible)
        self.update()

    def set_visible_samples(self, value: int) -> None:
        self.visible_samples = max(256, int(value))
        self.update()

    @staticmethod
    def _format_rate(value: float) -> str:
        if value >= 1_000_000:
            return f"{value / 1_000_000:.2f} MS/s"
        if value >= 1_000:
            return f"{value / 1_000:.2f} kS/s"
        return f"{value:.0f} S/s"

    def paintEvent(self, _event):  # noqa: N802 - Qt virtual
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(UiColors.CANVAS_BG))

        outer = QRectF(self.rect()).adjusted(18, 18, -18, -18)
        plot = outer.adjusted(54, 34, -20, -42)
        if plot.width() <= 10 or plot.height() <= 10:
            return

        painter.setPen(QPen(QColor("#394246"), 1))
        for column in range(11):
            x = plot.left() + plot.width() * column / 10.0
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
        for row in range(9):
            y = plot.top() + plot.height() * row / 8.0
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))

        painter.setPen(QPen(QColor("#C8D0D4"), 1))
        title_font = QFont(self.font())
        title_font.setBold(True)
        title_font.setPointSize(max(10, title_font.pointSize()))
        painter.setFont(title_font)
        painter.drawText(
            QRectF(outer.left(), outer.top(), outer.width(), 24),
            Qt.AlignLeft | Qt.AlignVCenter,
            "REAL-TIME WAVEFORM",
        )
        painter.setPen(QColor("#87939A"))
        detail_font = QFont(self.font())
        detail_font.setPointSize(max(8, detail_font.pointSize() - 2))
        painter.setFont(detail_font)
        painter.drawText(
            QRectF(outer.left(), outer.top(), outer.width(), 24),
            Qt.AlignRight | Qt.AlignVCenter,
            f"{self._format_rate(self.sample_rate_hz)}  ·  {self.visible_samples:,} samples",
        )

        x_axis = QPen(QColor("#819099"), 1)
        painter.setPen(x_axis)
        painter.drawLine(plot.bottomLeft(), plot.bottomRight())
        painter.drawLine(plot.topLeft(), plot.bottomLeft())

        trigger_y = plot.center().y() - (self.trigger_level / 32768.0) * plot.height() * 0.45
        trigger_pen = QPen(QColor(UiColors.ERROR), 1, Qt.DashLine)
        painter.setPen(trigger_pen)
        painter.drawLine(
            QPointF(plot.left(), trigger_y), QPointF(plot.right(), trigger_y)
        )
        painter.drawText(
            QRectF(plot.left() + 5, trigger_y - 20, 100, 18),
            Qt.AlignLeft | Qt.AlignVCenter,
            "TRIGGER",
        )

        columns = max(1, min(1600, int(plot.width())))
        x_values, lows, highs = self.sample_buffer.min_max_envelope(
            columns, self.visible_samples
        )
        if x_values.size:
            denominator = max(1.0, float(x_values[-1]))
            for channel in range(min(self.sample_buffer.channel_count, 4)):
                if not self.channel_visible[channel]:
                    continue
                color = QColor(self.CHANNEL_COLORS[channel])
                painter.setPen(QPen(color, 1.4))
                previous = None
                for index, x_value in enumerate(x_values):
                    low = float(lows[channel, index])
                    high = float(highs[channel, index])
                    if math.isnan(low) or math.isnan(high):
                        previous = None
                        continue
                    x = plot.left() + (float(x_value) / denominator) * plot.width()
                    scale = plot.height() * 0.43 / 32768.0 * self.channel_gain[channel]
                    offset = self.channel_offset[channel] * plot.height() * 0.1
                    y_low = plot.center().y() - low * scale - offset
                    y_high = plot.center().y() - high * scale - offset
                    painter.drawLine(QPointF(x, y_low), QPointF(x, y_high))
                    midpoint = QPointF(x, (y_low + y_high) / 2.0)
                    if previous is not None:
                        painter.drawLine(previous, midpoint)
                    previous = midpoint

        legend_x = plot.left()
        for channel, color in enumerate(self.CHANNEL_COLORS):
            painter.setPen(QPen(QColor(color), 3))
            painter.drawLine(
                QPointF(legend_x, outer.bottom() - 12),
                QPointF(legend_x + 18, outer.bottom() - 12),
            )
            painter.setPen(QColor("#B8C2C7"))
            painter.drawText(
                QRectF(legend_x + 24, outer.bottom() - 23, 42, 22),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"CH{channel + 1}",
            )
            legend_x += 72


class OscilloscopeWorkbench(QWidget):
    """Realtime scope tool kept separate from the existing UART control plane."""

    SETTINGS_PREFIX = "oscilloscope/"
    INQUIRY_GRACE_SECONDS = 0.25
    CAPTURE_TIMEOUT_SECONDS = 2.0
    MAX_CAPTURE_TIMEOUT_SECONDS = 30.0
    SIMULATION_SAMPLE_RATE_HZ = 32_000_000.0
    LEGACY_FALLBACK_SAMPLE_RATE_HZ = 65_000_000.0
    MAX_REPORTED_SAMPLE_RATE_HZ = 1_000_000_000

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self._settings = settings or QSettings("DClocking", "PrecisionWorkstation")
        self.protocol = LegacyUdpScopeProtocol()
        self.sample_buffer = ScopeSampleBuffer(channel_count=4, capacity=262_144)
        self._receiver: UdpScopeReceiver | None = None
        self._simulation_index = 0
        self._simulation_started_at = None
        self._last_metric_time = time.monotonic()
        self._last_metric_samples = 0
        self._total_samples_received = 0
        self._capture_received = 0
        self._capture_cycles = 0
        self._capture_request_due = 0.0
        self._capture_request_sent = False
        self._capture_deadline = 0.0
        self._capture_stats_baseline = 0
        self._capture_drop_baseline = 0
        self._capabilities_checked = False
        self._rng = np.random.default_rng(0xDCC10C)
        self._is_running = False
        self._last_source_is_udp = None
        self._simulation_channel_selection = [True, True, True, True]

        self.setObjectName("oscilloscope_workbench")
        self.setAccessibleName("实时示波器工作台")
        self.setMinimumSize(1040, 640)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())
        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_body(), 1)
        root.addWidget(self._build_status_bar())

        self._simulation_timer = QTimer(self)
        self._simulation_timer.setTimerType(Qt.PreciseTimer)
        self._simulation_timer.setInterval(25)
        self._simulation_timer.timeout.connect(self._generate_simulation_block)
        self._render_timer = QTimer(self)
        self._render_timer.setInterval(33)
        self._render_timer.timeout.connect(self._refresh_display)
        self._render_timer.start()

        self._connect_controls()
        self._restore_settings()
        self.plot.set_visible_samples(int(self.visible_samples_combo.currentData()))
        self._sync_source_controls()
        self._sync_button_state()

    @property
    def is_running(self) -> bool:
        return self._is_running

    def _build_header(self):
        header = QFrame(self)
        header.setObjectName("scope_header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(10)
        identity = QVBoxLayout()
        title = QLabel("OSCILLOSCOPE · DATA PLANE", header)
        title.setObjectName("scope_title")
        title.setStyleSheet("font-size: 17px; font-weight: 800; letter-spacing: 1px;")
        subtitle = QLabel("FPGA → Ethernet UDP → Windows PC → 实时显示", header)
        subtitle.setStyleSheet(f"color: {UiColors.TEXT_MUTED};")
        identity.addWidget(title)
        identity.addWidget(subtitle)
        layout.addLayout(identity)
        layout.addStretch()
        self.protocol_badge = QLabel("LEGACY UDP V0 · 协议草案", header)
        self.protocol_badge.setObjectName("scope_protocol_badge")
        self.protocol_badge.setStyleSheet(
            "color: #8F123D; background: #F5E6EB; border: 1px solid #E5C7D2;"
            "border-radius: 9px; padding: 5px 10px; font-weight: 700;"
        )
        layout.addWidget(self.protocol_badge)
        return header

    def _build_toolbar(self):
        bar = QFrame(self)
        bar.setObjectName("scope_toolbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(9)

        layout.addWidget(QLabel("数据源", bar))
        self.source_combo = QComboBox(bar)
        self.source_combo.setObjectName("scope_source_combo")
        self.source_combo.addItems(("内置仿真", "FPGA UDP"))
        layout.addWidget(self.source_combo)

        self.start_button = QPushButton("开始采集", bar)
        self.start_button.setObjectName("scope_start_button")
        self.start_button.setProperty("variant", "primary")
        self.stop_button = QPushButton("停止", bar)
        self.stop_button.setObjectName("scope_stop_button")
        self.clear_button = QPushButton("清空波形", bar)
        self.clear_button.setObjectName("scope_clear_button")
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.clear_button)
        layout.addStretch()
        self.connection_status_label = QLabel("● 就绪", bar)
        self.connection_status_label.setObjectName("scope_connection_status")
        self.connection_status_label.setStyleSheet(
            f"color: {UiColors.TEXT_MUTED}; font-weight: 700;"
        )
        layout.addWidget(self.connection_status_label)
        return bar

    def _build_body(self):
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setObjectName("scope_body_splitter")
        splitter.setChildrenCollapsible(False)

        plot_host = QWidget(splitter)
        plot_layout = QVBoxLayout(plot_host)
        plot_layout.setContentsMargins(14, 14, 8, 14)
        plot_layout.setSpacing(10)
        metrics = QHBoxLayout()
        self.sample_rate_metric = self._metric("采样率", "32.00 MS/s", plot_host)
        self.received_metric = self._metric("接收样本", "0", plot_host)
        self.throughput_metric = self._metric("显示吞吐", "0 S/s", plot_host)
        self.packet_metric = self._metric("UDP 数据报", "0", plot_host)
        for card in (
            self.sample_rate_metric[0],
            self.received_metric[0],
            self.throughput_metric[0],
            self.packet_metric[0],
        ):
            metrics.addWidget(card)
        plot_layout.addLayout(metrics)
        self.plot = ScopePlotWidget(self.sample_buffer, plot_host)
        plot_layout.addWidget(self.plot, 1)
        splitter.addWidget(plot_host)

        controls_scroll = QScrollArea(splitter)
        controls_scroll.setObjectName("scope_controls_scroll")
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setMinimumWidth(330)
        controls_scroll.setMaximumWidth(430)
        controls = QWidget(controls_scroll)
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(12, 12, 16, 18)
        controls_layout.setSpacing(12)
        controls_layout.addWidget(self._build_network_group())
        controls_layout.addWidget(self._build_acquisition_group())
        controls_layout.addWidget(self._build_channel_group())
        controls_layout.addWidget(self._build_trigger_group())
        controls_layout.addStretch()
        controls_scroll.setWidget(controls)
        splitter.addWidget(controls_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes((950, 360))
        return splitter

    @staticmethod
    def _metric(title, initial, parent):
        card = QFrame(parent)
        card.setObjectName("scope_metric_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)
        label = QLabel(title, card)
        label.setStyleSheet(f"color: {UiColors.TEXT_MUTED}; font-size: 10px;")
        value = QLabel(initial, card)
        value.setStyleSheet("font-family: monospace; font-weight: 800; font-size: 15px;")
        layout.addWidget(label)
        layout.addWidget(value)
        return card, value

    def _build_network_group(self):
        group = QGroupBox("Windows UDP 监听", self)
        form = QFormLayout(group)
        self.local_ip_combo = QComboBox(group)
        self.local_ip_combo.setEditable(True)
        self.local_ip_combo.addItems(self._local_ipv4_addresses())
        self.local_port_spin = QSpinBox(group)
        self.local_port_spin.setRange(1, 65535)
        self.local_port_spin.setValue(self.protocol.DEFAULT_PORT)
        self.local_port_spin.setEnabled(False)
        self.local_port_spin.setToolTip(
            "当前 Legacy UDP V0 的 FPGA 回包端口固定为 8080"
        )
        self.fpga_ip_edit = QLineEdit(self.protocol.DEFAULT_FPGA_IP, group)
        self.fpga_mac_edit = QLineEdit(self.protocol.DEFAULT_FPGA_MAC, group)
        form.addRow("本机监听 IP", self.local_ip_combo)
        form.addRow("本机 UDP 端口", self.local_port_spin)
        form.addRow("FPGA IP", self.fpga_ip_edit)
        form.addRow("FPGA MAC", self.fpga_mac_edit)
        note = QLabel("标准 UDP，无需 Npcap 或管理员权限；首次监听可能触发 Windows 防火墙提示。", group)
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {UiColors.TEXT_MUTED}; font-size: 10px;")
        form.addRow(note)
        return group

    def _build_acquisition_group(self):
        group = QGroupBox("采集与显示", self)
        form = QFormLayout(group)
        self.capture_samples_spin = QSpinBox(group)
        self.capture_samples_spin.setRange(512, self.protocol.MAX_SAMPLE_COUNT)
        self.capture_samples_spin.setSingleStep(512)
        self.capture_samples_spin.setValue(16_384)
        self.capture_samples_spin.setToolTip(
            "Legacy UDP V0 因 HDL 字节计数和 FIFO 分包限制，只允许 512 点整数倍"
        )
        self.acquisition_mode_combo = QComboBox(group)
        self.acquisition_mode_combo.addItems(("连续", "单次"))
        self.visible_samples_combo = QComboBox(group)
        for value in (1024, 4096, 16384, 65536, 262144):
            self.visible_samples_combo.addItem(f"{value:,} samples", value)
        self.visible_samples_combo.setCurrentIndex(1)
        self.refresh_rate_spin = QSpinBox(group)
        self.refresh_rate_spin.setRange(10, 60)
        self.refresh_rate_spin.setValue(30)
        self.refresh_rate_spin.setSuffix(" FPS")
        form.addRow("运行方式", self.acquisition_mode_combo)
        form.addRow("每帧采集点数", self.capture_samples_spin)
        form.addRow("显示窗口", self.visible_samples_combo)
        form.addRow("刷新率", self.refresh_rate_spin)
        return group

    def _build_channel_group(self):
        group = QGroupBox("通道", self)
        grid = QGridLayout(group)
        self.channel_checks = []
        self.channel_scale_spins = []
        self.channel_offset_spins = []
        colors = ScopePlotWidget.CHANNEL_COLORS
        gain_header = QLabel("增益", group)
        gain_header.setStyleSheet(f"color: {UiColors.TEXT_MUTED}; font-size: 10px;")
        offset_header = QLabel("偏移", group)
        offset_header.setStyleSheet(f"color: {UiColors.TEXT_MUTED}; font-size: 10px;")
        grid.addWidget(gain_header, 0, 1)
        grid.addWidget(offset_header, 0, 2)
        for channel in range(4):
            check = QCheckBox(f"CH{channel + 1}", group)
            check.setChecked(channel == 0 or self.source_combo.currentText() == "内置仿真")
            check.setStyleSheet(f"color: {colors[channel]}; font-weight: 800;")
            scale = QDoubleSpinBox(group)
            scale.setRange(0.1, 10.0)
            scale.setSingleStep(0.1)
            scale.setValue(1.0)
            scale.setSuffix(" ×")
            offset = QDoubleSpinBox(group)
            offset.setRange(-4.0, 4.0)
            offset.setSingleStep(0.1)
            offset.setValue(self.plot.channel_offset[channel])
            offset.setSuffix(" div")
            grid.addWidget(check, channel + 1, 0)
            grid.addWidget(scale, channel + 1, 1)
            grid.addWidget(offset, channel + 1, 2)
            self.channel_checks.append(check)
            self.channel_scale_spins.append(scale)
            self.channel_offset_spins.append(offset)
        return group

    def _build_trigger_group(self):
        group = QGroupBox("FPGA 触发参数", self)
        form = QFormLayout(group)
        self.trigger_mode_combo = QComboBox(group)
        self.trigger_mode_combo.addItems(("自动", "普通", "单次", "关闭"))
        self.trigger_type_combo = QComboBox(group)
        self.trigger_type_combo.addItems(("上升沿", "下降沿", "窗口", "电平"))
        self.trigger_channel_combo = QComboBox(group)
        self.trigger_channel_combo.addItems(("CH1", "CH2", "CH3", "CH4"))
        self.trigger_level_spin = QSpinBox(group)
        self.trigger_level_spin.setRange(-32768, 32767)
        self.trigger_level_spin.setValue(0)
        self.downsample_spin = QSpinBox(group)
        self.downsample_spin.setRange(1, 65536)
        self.downsample_spin.setValue(1)
        self.sustain_spin = QSpinBox(group)
        self.sustain_spin.setRange(0, 65535)
        form.addRow("模式", self.trigger_mode_combo)
        form.addRow("类型", self.trigger_type_combo)
        form.addRow("通道", self.trigger_channel_combo)
        form.addRow("阈值", self.trigger_level_spin)
        form.addRow("降采样比", self.downsample_spin)
        form.addRow("持续计数", self.sustain_spin)
        self.hardware_mapping_label = QLabel(
            "⚠ 待硬件确认：当前仅暂存界面参数，不写入现有 UART 寄存器。", group
        )
        self.hardware_mapping_label.setObjectName("scope_hardware_mapping_status")
        self.hardware_mapping_label.setWordWrap(True)
        self.hardware_mapping_label.setStyleSheet(
            f"color: {UiColors.WARNING}; font-weight: 700; font-size: 10px;"
        )
        form.addRow(self.hardware_mapping_label)
        return group

    def _build_status_bar(self):
        status = QFrame(self)
        status.setObjectName("scope_status_bar")
        status.setFixedHeight(34)
        layout = QHBoxLayout(status)
        layout.setContentsMargins(14, 0, 14, 0)
        self.detail_status_label = QLabel("模拟模式可用于完整验证；UDP 模式等待 FPGA 联调。", status)
        self.detail_status_label.setStyleSheet(f"color: {UiColors.TEXT_MUTED};")
        self.loss_status_label = QLabel("丢包检测：Legacy 不支持", status)
        self.loss_status_label.setStyleSheet(f"color: {UiColors.WARNING};")
        layout.addWidget(self.detail_status_label)
        layout.addStretch()
        layout.addWidget(self.loss_status_label)
        return status

    @staticmethod
    def _local_ipv4_addresses():
        values = ["0.0.0.0", "127.0.0.1"]
        try:
            for interface in QNetworkInterface.allInterfaces():
                flags = interface.flags()
                if not flags & QNetworkInterface.IsUp:
                    continue
                for entry in interface.addressEntries():
                    address = entry.ip()
                    if address.protocol() != QAbstractSocket.IPv4Protocol:
                        continue
                    text = address.toString()
                    if text and text not in values:
                        values.append(text)
        except Exception:
            pass
        try:
            for result in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                address = result[4][0]
                if address not in values:
                    values.append(address)
        except OSError:
            pass
        return values

    def _connect_controls(self):
        self.source_combo.currentTextChanged.connect(self._sync_source_controls)
        self.start_button.clicked.connect(self.start_acquisition)
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.clear_button.clicked.connect(self.sample_buffer.clear)
        self.clear_button.clicked.connect(self.plot.update)
        self.visible_samples_combo.currentIndexChanged.connect(
            lambda _index: self.plot.set_visible_samples(
                int(self.visible_samples_combo.currentData())
            )
        )
        self.refresh_rate_spin.valueChanged.connect(
            lambda fps: self._render_timer.setInterval(max(16, round(1000 / fps)))
        )
        self.trigger_level_spin.valueChanged.connect(self._set_trigger_level)
        for index, check in enumerate(self.channel_checks):
            check.toggled.connect(
                lambda checked, channel=index: self.plot.set_channel_visible(
                    channel, checked
                )
            )
        for index, scale in enumerate(self.channel_scale_spins):
            scale.valueChanged.connect(
                lambda value, channel=index: self._set_channel_gain(channel, value)
            )
        for index, offset in enumerate(self.channel_offset_spins):
            offset.valueChanged.connect(
                lambda value, channel=index: self._set_channel_offset(channel, value)
            )

    def _set_trigger_level(self, value):
        self.plot.trigger_level = float(value)
        self.plot.update()

    def _set_channel_gain(self, channel, value):
        self.plot.channel_gain[int(channel)] = float(value)
        self.plot.update()

    def _set_channel_offset(self, channel, value):
        self.plot.channel_offset[int(channel)] = float(value)
        self.plot.update()

    def _sync_source_controls(self, *_args, update_detail=True):
        udp = self.source_combo.currentText() == "FPGA UDP"
        previous_udp = self._last_source_is_udp
        for widget in (
            self.local_ip_combo,
            self.fpga_ip_edit,
            self.fpga_mac_edit,
        ):
            widget.setEnabled(udp and not self._is_running)
        self.local_port_spin.setValue(self.protocol.DEFAULT_PORT)
        self.local_port_spin.setEnabled(False)

        if udp:
            if previous_udp is False:
                self._simulation_channel_selection = [
                    check.isChecked() for check in self.channel_checks
                ]
            self.channel_checks[0].setChecked(True)
            self.channel_checks[0].setEnabled(not self._is_running)
            for check in self.channel_checks[1:]:
                check.setChecked(False)
                check.setEnabled(False)
        else:
            if previous_udp is True:
                for check, checked in zip(
                    self.channel_checks, self._simulation_channel_selection
                ):
                    check.setChecked(checked)
            for check in self.channel_checks:
                check.setEnabled(True)

        self._last_source_is_udp = udp
        if not self._is_running and (previous_udp is None or previous_udp != udp):
            self._reset_source_metrics(udp)
        if update_detail:
            self.detail_status_label.setText(
                "Legacy UDP V0 固定 8080 且当前仅返回 CH1；"
                "网络状态独立于主界面的串口连接。"
                if udp
                else "模拟四通道数据用于 Windows 界面、缓存与绘图链路验证。"
            )
        if not self._is_running:
            self.packet_metric[1].setText("—" if udp else "SIM —")

    def _reset_source_metrics(self, udp=None):
        if udp is None:
            udp = self.source_combo.currentText() == "FPGA UDP"
        sample_rate = (
            self.LEGACY_FALLBACK_SAMPLE_RATE_HZ
            if udp
            else self.SIMULATION_SAMPLE_RATE_HZ
        )
        self.plot.sample_rate_hz = float(sample_rate)
        self.sample_rate_metric[1].setText(
            "等待设备" if udp else ScopePlotWidget._format_rate(sample_rate)
        )
        self.received_metric[1].setText("0")
        self.throughput_metric[1].setText("0 S/s")
        self.packet_metric[1].setText("—" if udp else "SIM —")
        self.loss_status_label.setText(
            "丢包检测：Legacy 无包序号"
            if udp
            else "仿真数据：无网络丢包"
        )
        for index, check in enumerate(self.channel_checks):
            self.plot.set_channel_visible(index, check.isChecked())

    def _channel_mask(self) -> int:
        if self.source_combo.currentText() == "FPGA UDP":
            return 1
        mask = 0
        for index, check in enumerate(self.channel_checks):
            if check.isChecked():
                mask |= 1 << index
        return mask

    def start_acquisition(self):
        if self._is_running:
            return
        self.sample_buffer.clear()
        self._last_metric_time = time.monotonic()
        self._last_metric_samples = 0
        self._total_samples_received = 0
        self._capture_received = 0
        self._capture_cycles = 0
        self._capture_deadline = 0.0
        self._capture_stats_baseline = 0
        self._capture_drop_baseline = 0
        self._capabilities_checked = False
        self._reset_source_metrics()
        if self.source_combo.currentText() == "内置仿真":
            self._simulation_index = 0
            self._simulation_started_at = time.monotonic()
            self._simulation_timer.start()
            self._is_running = True
            self.connection_status_label.setText("● 仿真运行")
            self.connection_status_label.setStyleSheet(
                f"color: {UiColors.STATUS_OK}; font-weight: 800;"
            )
        else:
            try:
                channel_mask = self._channel_mask()
                if channel_mask == 0:
                    raise ScopeProtocolError("请至少启用一个采集通道")
                config = ScopeEndpointConfig(
                    local_ip=self.local_ip_combo.currentText().strip(),
                    local_port=self.local_port_spin.value(),
                    allowed_remote_ip=self.fpga_ip_edit.text().strip(),
                    allowed_remote_port=self.protocol.DEFAULT_PORT,
                )
                receiver = UdpScopeReceiver(config, protocol=self.protocol)
                receiver.start()
                receiver.send_inquiry(
                    self.fpga_ip_edit.text().strip(),
                    self.protocol.DEFAULT_PORT,
                    self.fpga_mac_edit.text().strip(),
                )
            except (OSError, ValueError, RuntimeError) as exc:
                if "receiver" in locals():
                    receiver.stop()
                self.connection_status_label.setText("● UDP 启动失败")
                self.connection_status_label.setStyleSheet(
                    f"color: {UiColors.ERROR}; font-weight: 800;"
                )
                QMessageBox.warning(self, "无法启动示波器", str(exc))
                return False
            self._receiver = receiver
            self._capture_request_due = time.monotonic() + self.INQUIRY_GRACE_SECONDS
            self._capture_request_sent = False
            self._is_running = True
            endpoint = receiver.bound_endpoint
            self.connection_status_label.setText(
                f"● 正在监听 {endpoint[0]}:{endpoint[1]} · 等待设备信息"
            )
            self.connection_status_label.setStyleSheet(
                f"color: {UiColors.STATUS_OK}; font-weight: 800;"
            )
        self._sync_button_state()
        self._sync_source_controls()
        return True

    def stop_acquisition(self):
        self._stop_acquisition("● 已停止")

    def _stop_acquisition(self, status_text, *, detail=None, error=False):
        self._simulation_timer.stop()
        receiver = self._receiver
        self._receiver = None
        self._capture_request_sent = False
        self._capture_deadline = 0.0
        if receiver is not None:
            receiver.stop()
        self._is_running = False
        self.connection_status_label.setText(status_text)
        self.connection_status_label.setStyleSheet(
            f"color: {UiColors.ERROR if error else UiColors.TEXT_MUTED}; font-weight: 700;"
        )
        self._sync_button_state()
        self._sync_source_controls(update_detail=detail is None)
        if detail is not None:
            self.detail_status_label.setText(detail)

    def _sync_button_state(self):
        self.start_button.setEnabled(not self._is_running)
        self.stop_button.setEnabled(self._is_running)
        self.source_combo.setEnabled(not self._is_running)
        self.acquisition_mode_combo.setEnabled(not self._is_running)
        self.capture_samples_spin.setEnabled(not self._is_running)

    def _generate_simulation_block(self):
        sample_rate = 32_000_000.0
        count = 2048
        if self.acquisition_mode_combo.currentText() == "单次":
            remaining = self.capture_samples_spin.value() - self._capture_received
            count = min(count, max(0, remaining))
            if count == 0:
                self.stop_acquisition()
                self.connection_status_label.setText("● 单次采集完成")
                return
        indices = np.arange(count, dtype=np.float64) + self._simulation_index
        frequencies = (30_000.0, 75_000.0, 180_000.0, 400_000.0)
        amplitudes = (27_000.0, 18_000.0, 13_000.0, 9_000.0)
        channels = []
        for channel, (frequency, amplitude) in enumerate(zip(frequencies, amplitudes)):
            phase = channel * 0.65
            signal = amplitude * np.sin(2.0 * np.pi * frequency * indices / sample_rate + phase)
            if channel == 1:
                signal += 3_200.0 * np.sin(2.0 * np.pi * 32_000.0 * indices / sample_rate)
            noise = self._rng.normal(0.0, 180.0 + channel * 30.0, count)
            channels.append(np.clip(signal + noise, -32768, 32767))
        self.sample_buffer.append(np.asarray(channels, dtype=np.float32))
        self._simulation_index += count
        self._capture_received += count
        self._total_samples_received += count
        if (
            self.acquisition_mode_combo.currentText() == "单次"
            and self._capture_received >= self.capture_samples_spin.value()
        ):
            self.stop_acquisition()
            self.connection_status_label.setText("● 单次采集完成")
            self.connection_status_label.setStyleSheet(
                f"color: {UiColors.STATUS_OK}; font-weight: 800;"
            )

    def _send_capture_request(self, receiver):
        discard = getattr(receiver, "discard_queued_samples", None)
        if callable(discard):
            discard()
        else:
            # Test doubles and older adapters may only expose drain().
            receiver.drain(max_packets=4096)
        stats = receiver.stats
        self._capture_received = 0
        self._capture_stats_baseline = stats.received_sample_count
        self._capture_drop_baseline = stats.queue_dropped_packets
        receiver.send_capture_request(
            self.fpga_ip_edit.text().strip(),
            self.protocol.DEFAULT_PORT,
            self.fpga_mac_edit.text().strip(),
            self._channel_mask(),
            self.capture_samples_spin.value(),
        )
        expected_seconds = self.capture_samples_spin.value() / max(
            1.0, float(self.plot.sample_rate_hz)
        )
        self._capture_deadline = time.monotonic() + min(
            self.MAX_CAPTURE_TIMEOUT_SECONDS,
            max(self.CAPTURE_TIMEOUT_SECONDS, expected_seconds * 20.0),
        )

    def _fail_udp_capture(self, reason):
        self._stop_acquisition(
            "● UDP 采集失败",
            detail=str(reason),
            error=True,
        )

    def _validate_reported_capabilities(self, capabilities):
        if capabilities is None:
            return True
        expected_ip = self.fpga_ip_edit.text().strip()
        expected_mac = self.protocol._format_mac(
            self.protocol._mac_bytes(self.fpga_mac_edit.text().strip())
        )
        identity_mismatch = (
            capabilities.fpga_ip != expected_ip
            or capabilities.fpga_mac != expected_mac
        )
        format_errors = []
        if not capabilities.signed:
            format_errors.append("样本必须为有符号数")
        if capabilities.sample_bytes != 2:
            format_errors.append("样本容器必须为 2 字节")
        if not 1 <= capabilities.sample_bits <= 16:
            format_errors.append("有效位数必须为 1 至 16 bit")
        if capabilities.channel_count != 1:
            format_errors.append("Legacy UDP V0 仅支持单通道数据包")
        if not 1 <= capabilities.sample_rate_hz <= self.MAX_REPORTED_SAMPLE_RATE_HZ:
            format_errors.append("采样率超出 1 S/s 至 1 GS/s 安全范围")
        if not self.protocol.LEGACY_SAMPLE_GRANULARITY <= capabilities.sample_depth <= 0xFFFFFFFF:
            format_errors.append("采样深度无效")
        elif capabilities.sample_depth < self.capture_samples_spin.value():
            format_errors.append("设备采样深度小于本次请求点数")

        if identity_mismatch or format_errors:
            details = []
            if identity_mismatch:
                details.append(
                    f"设备身份为 {capabilities.fpga_ip} / {capabilities.fpga_mac}，"
                    f"期望 {expected_ip} / {expected_mac}"
                )
            details.extend(format_errors)
            self._fail_udp_capture(
                "设备信息与 Legacy 协议不兼容：" + "；".join(details) + "。"
            )
            return False
        self._capabilities_checked = True
        return True

    def _refresh_display(self):
        receiver = self._receiver
        if receiver is not None:
            stats = receiver.stats
            if not getattr(receiver, "is_running", True):
                self._fail_udp_capture(
                    f"接收线程已停止：{stats.last_error or '未提供错误详情'}"
                )
                self.plot.update()
                return
            capabilities = receiver.last_capabilities
            if not self._validate_reported_capabilities(capabilities):
                self.plot.update()
                return
            if not self._capture_request_sent and (
                capabilities is not None
                or time.monotonic() >= self._capture_request_due
            ):
                try:
                    self._send_capture_request(receiver)
                except (OSError, ValueError, RuntimeError) as exc:
                    self._fail_udp_capture(f"采集请求发送失败：{exc}")
                    self.plot.update()
                    return
                else:
                    self._capture_request_sent = True
                    self.connection_status_label.setText("● 已发送采集请求 · 正在接收")
                    if not getattr(receiver, "is_running", True):
                        self._fail_udp_capture(
                            f"接收线程已停止：{receiver.stats.last_error or '未提供错误详情'}"
                        )
                        self.plot.update()
                        return
            packets = (
                receiver.drain(max_packets=4096)
                if self._capture_request_sent
                else []
            )
            if packets:
                # Current HDL exposes only the lower 16-bit stream.  Do not
                # pretend it contains four interleaved channels.
                remaining = self.capture_samples_spin.value() - self._capture_received
                block = np.concatenate([packet.samples for packet in packets])
                accepted = block[: max(0, remaining)]
                if accepted.size:
                    self.sample_buffer.append_channel(0, accepted)
                    self._capture_received += int(accepted.size)
                    self._total_samples_received += int(accepted.size)
            stats = receiver.stats
            dropped_this_capture = max(
                0, stats.queue_dropped_packets - self._capture_drop_baseline
            )
            if dropped_this_capture:
                self.loss_status_label.setText(
                    f"PC 队列丢弃 {dropped_this_capture} 包；当前采集不完整"
                )
                self._fail_udp_capture(
                    "PC 接收队列发生丢包，已停止以避免把不完整数据标记为有效采集。"
                )
                self.plot.update()
                return

            if (
                self._capture_request_sent
                and self._capture_received < self.capture_samples_spin.value()
                and time.monotonic() >= self._capture_deadline
            ):
                wire_samples = max(
                    0, stats.received_sample_count - self._capture_stats_baseline
                )
                self._fail_udp_capture(
                    f"采集响应超时：请求 {self.capture_samples_spin.value()} 点，"
                    f"PC 仅收到 {wire_samples} 点。Legacy 协议无包序号，无法自动补包。"
                )
                self.plot.update()
                return

            if (
                self._capture_request_sent
                and self._capture_received >= self.capture_samples_spin.value()
            ):
                self._capture_cycles += 1
                if self.acquisition_mode_combo.currentText() == "连续":
                    try:
                        self._send_capture_request(receiver)
                    except (OSError, ValueError, RuntimeError) as exc:
                        self._fail_udp_capture(f"连续采集重启失败：{exc}")
                        self.plot.update()
                        return
                else:
                    self._stop_acquisition("● 单次采集完成")
                    self.connection_status_label.setStyleSheet(
                        f"color: {UiColors.STATUS_OK}; font-weight: 800;"
                    )
                    self.plot.update()
                    return
            if capabilities is not None:
                self.plot.sample_rate_hz = float(capabilities.sample_rate_hz)
                self.sample_rate_metric[1].setText(
                    ScopePlotWidget._format_rate(capabilities.sample_rate_hz)
                )
                self.detail_status_label.setText(
                    f"设备报告 {capabilities.channel_count} 通道 / "
                    f"{capabilities.sample_bits} bit / 深度 {capabilities.sample_depth:,}；"
                    "字段尚未完成硬件联调。"
                )
            self.packet_metric[1].setText(f"{stats.received_datagrams:,}")
            if stats.malformed_datagrams or stats.queue_dropped_packets:
                self.loss_status_label.setText(
                    f"坏包 {stats.malformed_datagrams} · PC 队列丢弃 {stats.queue_dropped_packets} · "
                    "FPGA 包序号不可见"
                )
        else:
            if self.source_combo.currentText() == "内置仿真":
                if self._is_running and self._simulation_started_at is not None:
                    elapsed = max(0.0, time.monotonic() - self._simulation_started_at)
                    self.packet_metric[1].setText(f"SIM {elapsed:.1f}s")
                elif not self.packet_metric[1].text().startswith("SIM"):
                    self.packet_metric[1].setText("SIM —")
            else:
                self.packet_metric[1].setText("—")

        total = self._total_samples_received
        now = time.monotonic()
        elapsed = now - self._last_metric_time
        if elapsed >= 0.25:
            rate = max(0.0, (total - self._last_metric_samples) / elapsed)
            self.throughput_metric[1].setText(ScopePlotWidget._format_rate(rate))
            self._last_metric_samples = total
            self._last_metric_time = now
        self.received_metric[1].setText(f"{total:,}")
        self.plot.update()

    def _restore_settings(self):
        prefix = self.SETTINGS_PREFIX
        source = str(self._settings.value(prefix + "source", "内置仿真"))
        if self.source_combo.findText(source) >= 0:
            self.source_combo.setCurrentText(source)
        local_ip = str(self._settings.value(prefix + "local_ip", "0.0.0.0"))
        self.local_ip_combo.setCurrentText(local_ip)
        self.local_port_spin.setValue(self.protocol.DEFAULT_PORT)
        self.fpga_ip_edit.setText(
            str(self._settings.value(prefix + "fpga_ip", self.protocol.DEFAULT_FPGA_IP))
        )
        self.fpga_mac_edit.setText(
            str(self._settings.value(prefix + "fpga_mac", self.protocol.DEFAULT_FPGA_MAC))
        )
        capture = int(self._settings.value(prefix + "capture_samples", 16_384))
        capture -= capture % self.protocol.LEGACY_SAMPLE_GRANULARITY
        self.capture_samples_spin.setValue(max(512, capture))
        self.refresh_rate_spin.setValue(
            int(self._settings.value(prefix + "refresh_fps", 30))
        )
        mode = str(self._settings.value(prefix + "acquisition_mode", "连续"))
        if self.acquisition_mode_combo.findText(mode) >= 0:
            self.acquisition_mode_combo.setCurrentText(mode)
        visible = int(self._settings.value(prefix + "visible_samples", 4096))
        visible_index = self.visible_samples_combo.findData(visible)
        if visible_index >= 0:
            self.visible_samples_combo.setCurrentIndex(visible_index)
        for index, check in enumerate(self.channel_checks):
            default = index == 0 or source == "内置仿真"
            value = self._settings.value(prefix + f"channel_{index + 1}", default)
            check.setChecked(str(value).lower() not in ("0", "false", "no"))
            self.channel_scale_spins[index].setValue(
                float(self._settings.value(prefix + f"gain_{index + 1}", 1.0))
            )
            self.channel_offset_spins[index].setValue(
                float(
                    self._settings.value(
                        prefix + f"offset_{index + 1}",
                        self.plot.channel_offset[index],
                    )
                )
            )
        self.trigger_level_spin.setValue(
            int(self._settings.value(prefix + "trigger_level", 0))
        )
        self.downsample_spin.setValue(
            int(self._settings.value(prefix + "downsample", 1))
        )
        self.sustain_spin.setValue(
            int(self._settings.value(prefix + "sustain", 0))
        )

    def _save_settings(self):
        prefix = self.SETTINGS_PREFIX
        self._settings.setValue(prefix + "source", self.source_combo.currentText())
        self._settings.setValue(prefix + "local_ip", self.local_ip_combo.currentText())
        self._settings.setValue(prefix + "fpga_ip", self.fpga_ip_edit.text())
        self._settings.setValue(prefix + "fpga_mac", self.fpga_mac_edit.text())
        self._settings.setValue(prefix + "capture_samples", self.capture_samples_spin.value())
        self._settings.setValue(prefix + "refresh_fps", self.refresh_rate_spin.value())
        self._settings.setValue(
            prefix + "acquisition_mode", self.acquisition_mode_combo.currentText()
        )
        self._settings.setValue(
            prefix + "visible_samples", int(self.visible_samples_combo.currentData())
        )
        self._settings.setValue(prefix + "trigger_level", self.trigger_level_spin.value())
        self._settings.setValue(prefix + "downsample", self.downsample_spin.value())
        self._settings.setValue(prefix + "sustain", self.sustain_spin.value())
        for index, check in enumerate(self.channel_checks):
            self._settings.setValue(prefix + f"channel_{index + 1}", check.isChecked())
            self._settings.setValue(
                prefix + f"gain_{index + 1}", self.channel_scale_spins[index].value()
            )
            self._settings.setValue(
                prefix + f"offset_{index + 1}", self.channel_offset_spins[index].value()
            )
        self._settings.sync()

    def shutdown(self):
        self.stop_acquisition()
        self._render_timer.stop()
        self._save_settings()

    def showEvent(self, event):  # noqa: N802 - Qt virtual
        if not self._render_timer.isActive():
            self._render_timer.start()
        super().showEvent(event)

    def closeEvent(self, event):  # noqa: N802 - Qt virtual
        self.shutdown()
        event.accept()
