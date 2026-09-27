"""Operator-facing PDH experiment workspace; hardware writes stay in MainWindow.

The inherited register editor remains the engineering view. Profile, waveform,
and all chart edits are local drafts. A command readback is never FSM telemetry.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PySide6.QtCore import QIODevice, QSaveFile, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLayout, QLineEdit, QPushButton, QScrollArea, QStackedWidget,
    QTabWidget, QVBoxLayout, QWidget, QFileDialog,
)

from FPGA_Agent.pdh_experiment import (
    ExperimentProfile, WaveformTrace, cycles_to_us, us_to_cycles,
    q15_to_percent, percent_to_q15, demo_trace, parse_trace_csv,
    suggest_parameters, replay_manual, preflight, export_report, validate_parameters, MAX_CSV_BYTES,
)
from qt_pdh_designer import PDHDesignerWidget
from qt_pdh_waveform import PDHWaveformCanvas


FIELD_NAMES = {
    "threshold_signal_scan": "入锁阈值", "time_scan": "入锁确认时间",
    "threshold_signal_lock": "失锁阈值", "time_lock": "失锁确认时间",
    "coef_scan": "自动入锁位置", "coef_lock": "自动失锁位置",
}
STEP_COPY = (
    ("01  认识这套实验", "先确认每条信号来自哪里", "区分误差信号、判锁信号与扫描同步。填写一次实验方案，后续可直接复用。"),
    ("02  扫描找共振", "先看见共振，再设置判据", "打开示波器观察实际信号，或导入 CSV。拖选目标共振区域；演示数据只用于练习，不代表设备。"),
    ("03  设置锁定条件", "在波形上拖动阈值与时间", "红线：低于此值允许入锁。青线：高于此值开始判失锁。连续满足指定时间才有效；编辑只形成草稿。"),
    ("04  启动与观察", "分别确认配置、反馈与光学结果", "先检查接线和参数，再发送启动请求。旧固件没有运行状态回读，不能用请求码推断已锁定。"),
)


def _label(text, role=None):
    widget = QLabel(text)
    widget.setWordWrap(True)
    widget.setTextFormat(Qt.PlainText)
    if role:
        widget.setProperty("pdhRole", role)
    return widget


def _button(text, name, callback, primary=False):
    widget = QPushButton(text)
    widget.setObjectName(name)
    widget.setAccessibleName(text)
    widget.clicked.connect(callback)
    if primary:
        widget.setProperty("pdhRole", "primary")
    return widget


class PDHExperimentWorkbench(PDHDesignerWidget):
    """Guided tasks + daily observation + unchanged legacy engineering editor."""

    profile_changed = Signal(dict)
    local_stage_requested = Signal(dict)
    context_requested = Signal()
    locate_requested = Signal(str)
    scope_requested = Signal()
    scope_snapshot_requested = Signal()
    record_requested = Signal(str)

    def __init__(self, parent=None):
        self._experiment_ready = False
        self.profile = ExperimentProfile()
        self.trace = None
        self.replay = None
        self.current_step = 0
        self.context = {"connected": False, "topology_issues": [], "routes": {}}
        self._pending_refresh = None
        self._profile_error = None
        self._operator_errors = {}
        self._operator_sync = False
        super().__init__(parent)
        engineering = QWidget(self)
        engineering.setLayout(self.layout())
        self._build_experiment_ui(engineering)
        self._experiment_ready = True
        self.set_profile(self.profile)
        self._sync_experiment()

    def _build_experiment_ui(self, engineering):
        self.setAccessibleName("PDH 实验工作台：确认接线、扫描找共振、设置条件、启动与观察")
        self.setMinimumSize(960, 640)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 12)
        root.setSpacing(10)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(_label("PDH 实验工作台", "title"))
        titles.addWidget(_label("从实验接线到锁定判据 · 同一份配置，清楚的操作依据", "muted"))
        header.addLayout(titles, 1)
        header.addWidget(_button("打开方案", "pdh_bundle_open", self.choose_bundle))
        header.addWidget(_button("保存方案", "pdh_bundle_save", self.choose_save_bundle))
        header.addWidget(_button("记入实验记录", "pdh_record", self.create_record))
        root.addLayout(header)
        statuses = QHBoxLayout()
        self.connection_badge = _label("设备：离线", "chip")
        self.sync_badge = _label("参数：本地配置", "chip")
        self.runtime_badge = _label("运行反馈：固件未提供状态回读", "chip")
        for widget in (self.connection_badge, self.sync_badge, self.runtime_badge):
            statuses.addWidget(widget, 1)
        root.addLayout(statuses)
        self.views = QTabWidget()
        self.views.setObjectName("pdh_experiment_views")
        root.addWidget(self.views, 1)
        guided = QWidget()
        flow = QVBoxLayout(guided)
        flow.setContentsMargins(0, 10, 0, 0)
        self.steps_row = QWidget()
        steps = QHBoxLayout(self.steps_row)
        steps.setContentsMargins(0, 0, 0, 0)
        self.step_buttons = []
        for index, text in enumerate(("① 确认接线", "② 扫描找共振", "③ 设置条件", "④ 启动与观察")):
            button = _button(text, f"pdh_step_{index}", lambda _=False, i=index: self.set_step(i))
            button.setCheckable(True)
            self.step_buttons.append(button)
            steps.addWidget(button)
        flow.addWidget(self.steps_row)
        self.step_title = _label("", "section")
        self.step_hint = _label("", "muted")
        flow.addWidget(self.step_title)
        flow.addWidget(self.step_hint)
        self.pages = QStackedWidget()
        flow.addWidget(self.pages, 1)
        self.pages.addWidget(self._build_setup())
        self.pages.addWidget(self._build_analysis())
        nav = QHBoxLayout()
        nav.addWidget(_button("上一步", "pdh_step_previous", lambda: self.set_step(max(0, self.current_step-1))))
        nav.addStretch()
        self.next_button = _button("下一步：扫描找共振", "pdh_step_next", self.next_step, True)
        nav.addWidget(self.next_button)
        flow.addLayout(nav)
        self.views.addTab(guided, "首次配置")
        self.daily_placeholder = QWidget()
        self.views.addTab(self.daily_placeholder, "运行监控")
        self.views.addTab(engineering, "工程详情")
        self.views.currentChanged.connect(self._view_changed)
        self.operation_feedback = _label("从确认接线开始；所有编辑先保存为草稿，不会自动写入 FPGA。", "feedback")
        self.operation_feedback.setObjectName("pdh_operation_feedback")
        root.addWidget(self.operation_feedback)
        self._guided = guided
        self._flow = flow
        self.setStyleSheet(self.styleSheet() + """
            QLabel[pdhRole=title] { font-size: 23px; font-weight: 750; color: #21354A; }
            QLabel[pdhRole=section] { font-size: 15px; font-weight: 700; color: #21354A; }
            QLabel[pdhRole=muted] { color: #68798B; font-size: 12px; }
            QLabel[pdhRole=chip] { padding: 9px; background: #F2F5F8; border-radius: 7px; font-size: 11px; }
            QLabel[pdhRole=feedback] { padding: 8px; background: #F5F1F3; color: #7D2240; border-radius: 6px; }
            QFrame[pdhRole=card] { background: #F8FAFC; border: 1px solid #DBE2E9; border-radius: 9px; }
            QPushButton { min-height: 30px; padding: 4px 10px; border-radius: 6px; }
            QPushButton:checked, QPushButton[pdhRole=primary] { background: #990033; color: white; border: 1px solid #990033; }
            QPushButton:disabled { color: #98A2AD; background: #EFF1F4; border-color: #D8DEE6; }
            QTabWidget::pane { border: 0; }
            QScrollArea { border: 0; background: transparent; }
            QComboBox { min-height: 28px; padding: 4px 8px; }
        """)
        self.set_step(0)

    def _build_setup(self):
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        self.route_buttons = {}
        for key, title, detail in (
            ("error", "误差信号 → 解调 / 滤波 → PID → 执行器", "反馈支路：决定执行器怎样修正；不是判锁输入。"),
            ("signal", "探测信号 → 判锁判据", "判锁支路：现有固件以低于阈值入锁，需要确认共振处为谷。"),
            ("scan", "扫描源 → 扫描同步 / 扫描控制", "扫描支路：确认连接的是暂停保持还是复位，不等于输出归零。"),
        ):
            row = QFrame()
            row.setProperty("pdhRole", "card")
            rl = QHBoxLayout(row)
            labels = QVBoxLayout()
            labels.addWidget(_label(title, "section"))
            labels.addWidget(_label(detail, "muted"))
            rl.addLayout(labels, 1)
            button = _button("查看实际连接", "pdh_route_"+key, lambda _=False, k=key: self.locate_requested.emit(k))
            self.route_buttons[key] = button
            rl.addWidget(button)
            layout.addWidget(row)
        form = QGridLayout()
        self.profile_fields = {}
        definitions = (
            ("name", "实验方案", "例如：光腔 A · 快速执行器"),
            ("detector_source", "判锁信号的物理来源", "例如：反射探测器；不要凭端口名猜测"),
            ("signal_path", "判锁通道 / 信号链", "例如：ADC C → FIR2 → 判锁输入"),
            ("error_path", "误差信号链", "探测器 → 解调 → 滤波 → PID"),
            ("scan_path", "扫描源与控制方式", "扫描模块、同步输入、暂停 / 复位"),
            ("actuator_path", "执行器 / 输出范围", "DAC 通道、执行器及已确认的安全范围"),
            ("clock_hz", "已确认的 PDH 内核时钟 / Hz", "未知请留空；与示波器采样率不同"),
            ("units_per_count", "内部信号标定 / 单位每码", "选填；须包含整条信号链增益，零偏需已校正"),
            ("signal_unit", "标定后的单位", "例如 V；没有标定时使用内部信号码"),
            ("notes", "实验备注", "接线约定、执行器限制与操作者说明"),
        )
        for i, (key, name, placeholder) in enumerate(definitions):
            col = (i % 2) * 2
            row = i // 2
            edit = QLineEdit()
            edit.setObjectName("pdh_profile_"+key)
            edit.setPlaceholderText(placeholder)
            edit.setAccessibleName(name)
            edit.editingFinished.connect(self._profile_edited)
            edit.setMaxLength(2000 if key == "notes" else 500)
            self.profile_fields[key] = edit
            form.addWidget(_label(name), row*2, col, 1, 2)
            form.addWidget(edit, row*2+1, col, 1, 2)
        layout.addLayout(form)
        polarity = QHBoxLayout()
        polarity.addWidget(_label("共振在判锁输入处表现为"))
        self.polarity_combo = QComboBox()
        for label, value in (("待确认", "unknown"), ("向下的谷（适用当前固件）", "dip"), ("向上的峰（需确认反相链路）", "peak")):
            self.polarity_combo.addItem(label, value)
        self.polarity_combo.currentIndexChanged.connect(self._profile_edited)
        polarity.addWidget(self.polarity_combo, 1)
        polarity.addWidget(_button("重新检查接线", "pdh_check_wiring", self.context_requested.emit))
        layout.addLayout(polarity)
        self.wiring_summary = _label("实际连接尚未检查。", "muted")
        layout.addWidget(self.wiring_summary)
        layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        return scroll

    def _build_analysis(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.trace_badge = _label("观测：尚无数据", "chip")
        bar.addWidget(self.trace_badge, 1)
        bar.addWidget(_button("演示练习", "pdh_demo_trace", lambda: self.set_trace(demo_trace())))
        bar.addWidget(_button("导入 CSV", "pdh_import_trace", self.choose_trace))
        bar.addWidget(_button("示波器", "pdh_open_scope", self.scope_requested.emit))
        bar.addWidget(_button("取 CH1 快照", "pdh_scope_snapshot", self.scope_snapshot_requested.emit))
        root.addLayout(bar)
        self.scope_mapping_confirmed = QCheckBox("我已确认示波器 CH1 是此 PDH 判锁输入，且使用相同内部信号码")
        self.scope_mapping_confirmed.setObjectName("pdh_scope_mapping_confirmed")
        root.addWidget(self.scope_mapping_confirmed)
        middle = QHBoxLayout()
        left = QVBoxLayout()
        self.waveform = PDHWaveformCanvas()
        self.waveform.parameter_changed.connect(self.stage_value)
        self.waveform.selection_changed.connect(lambda *_: self._refresh_replay())
        left.addWidget(self.waveform, 1)
        self.replay_label = _label("拖选目标共振区域；时间轴来自数据文件或采集设置，不是状态机遥测。", "muted")
        left.addWidget(self.replay_label)
        actions = QHBoxLayout()
        self.suggest_button = _button("从选区生成判据草稿", "pdh_suggest", self.suggest_from_selection)
        actions.addWidget(self.suggest_button)
        actions.addWidget(_button("撤销草稿", "pdh_undo_draft", self.undo_draft))
        actions.addStretch()
        left.addLayout(actions)
        middle.addLayout(left, 1)
        self.controls = QFrame()
        self.controls.setProperty("pdhRole", "card")
        self.controls.setMinimumWidth(240)
        self.controls.setMaximumWidth(310)
        controls = QVBoxLayout(self.controls)
        controls.setSizeConstraint(QLayout.SetMinimumSize)
        controls.setSpacing(12)
        controls.addWidget(_label("锁定条件", "section"))
        self.mode_combo = QComboBox()
        self.mode_combo.setObjectName("pdh_operator_mode")
        self.mode_combo.addItems(["手动锁定模式", "自动锁定模式"])
        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        controls.addWidget(self.mode_combo)
        self.mode_hint = _label("", "muted")
        controls.addWidget(self.mode_hint)
        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.operator_editors = {}
        self.operator_labels = {}
        for key, name in FIELD_NAMES.items():
            editor = QDoubleSpinBox()
            editor.setObjectName("pdh_operator_"+key)
            editor.setKeyboardTracking(False)
            editor.setMinimumHeight(32)
            editor.setAccessibleName(name)
            editor.valueChanged.connect(lambda value, k=key: self._operator_changed(k, value))
            self.operator_editors[key] = editor
            label = _label(name)
            self.operator_labels[key] = label
            form.addRow(label, editor)
        controls.addLayout(form)
        self.units_hint = _label("", "muted")
        controls.addWidget(self.units_hint)
        self.diff_label = _label("暂无修改", "muted")
        self.diff_label.setObjectName("pdh_draft_diff")
        controls.addWidget(self.diff_label)
        self.local_button = _button("保存草稿到本地画布", "pdh_stage_local", self._request_local_stage)
        self.write_button = _button("写入并核对参数", "pdh_apply_verified", self._request_apply, True)
        controls.addWidget(self.local_button)
        controls.addWidget(self.write_button)
        controls.addWidget(_button("读取设备参数", "pdh_read_verified", self._request_refresh))
        controls.addStretch()
        self.controls_scroll = QScrollArea()
        self.controls_scroll.setWidgetResizable(True)
        self.controls_scroll.setMinimumWidth(275)
        self.controls_scroll.setMaximumWidth(345)
        self.controls_scroll.setWidget(self.controls)
        middle.addWidget(self.controls_scroll)
        root.addLayout(middle, 1)
        self.conflict_box = QFrame()
        conflict = QHBoxLayout(self.conflict_box)
        self.conflict_label = _label("", "muted")
        conflict.addWidget(self.conflict_label, 1)
        conflict.addWidget(_button("采用设备值", "pdh_take_device", lambda: self.resolve_refresh(False)))
        conflict.addWidget(_button("保留草稿，重新核对", "pdh_rebase_draft", lambda: self.resolve_refresh(True)))
        self.conflict_box.hide()
        root.addWidget(self.conflict_box)
        self.diagnosis = _label("", "muted")
        self.diagnosis.setObjectName("pdh_diagnosis")
        root.addWidget(self.diagnosis)
        self.run_row = QWidget()
        run = QHBoxLayout(self.run_row)
        run.setContentsMargins(0, 0, 0, 0)
        self.start_button = _button("检查并请求启动", "pdh_start_experiment", self.start_experiment, True)
        run.addWidget(self.start_button)
        run.addWidget(_button("请求退出锁定", "pdh_exit_request", self.request_idle))
        run.addWidget(_button("查看接线", "pdh_locate_wiring", lambda: self.locate_requested.emit("signal")))
        run.addWidget(_label("退出请求不等于执行器归零；当前固件无确定性停止确认。", "muted"), 1)
        root.addWidget(self.run_row)
        return page

    def _view_changed(self, index):
        # Reuse the same live draft widgets in guided and daily modes.
        if index == 1:
            self.views.widget(1).setLayout(self._flow)
            self.steps_row.hide()
            self.set_step(3)
        elif index == 0:
            self._guided.setLayout(self._flow)
            self.steps_row.show()

    def set_step(self, step):
        self.current_step = max(0, min(3, int(step)))
        title, purpose, hint = STEP_COPY[self.current_step]
        self.step_title.setText(title + "  ·  " + purpose)
        self.step_hint.setText(hint)
        self.pages.setCurrentIndex(0 if self.current_step == 0 else 1)
        for index, button in enumerate(self.step_buttons):
            button.setChecked(index == self.current_step)
        self.controls_scroll.setVisible(self.current_step >= 2)
        self.run_row.setVisible(self.current_step == 3)
        self.next_button.setText(("下一步：扫描找共振", "下一步：设置条件", "下一步：启动与观察", "保存本次实验记录")[self.current_step])
        if self._experiment_ready:
            self.context_requested.emit()

    def next_step(self):
        if not self._profile_edited():
            return
        if self.current_step == 3:
            self.create_record()
        else:
            self.set_step(self.current_step + 1)

    def set_profile(self, profile):
        profile = profile if isinstance(profile, ExperimentProfile) else ExperimentProfile.from_dict(profile)
        self._validate_display_profile(profile)
        old_profile = self.profile
        self.profile = profile
        if not self._experiment_ready:
            return
        self._operator_sync = True
        try:
            for key, editor in self.profile_fields.items():
                value = getattr(profile, key)
                editor.setText("" if value is None else str(value))
            self.polarity_combo.setCurrentIndex(self.polarity_combo.findData(profile.polarity))
        finally:
            self._operator_sync = False
        self._profile_error = None
        self._invalidate_mapping(old_profile, profile)
        self._clock_hz = profile.clock_hz
        for key in ("time_scan", "time_lock"):
            self._update_duration_hint(key)
        self._sync_experiment()

    def _profile_edited(self, *_):
        if self._operator_sync or not self._experiment_ready:
            return True
        values = self.profile.to_dict()
        for key, editor in self.profile_fields.items():
            value = editor.text().strip()
            if key in ("clock_hz", "units_per_count"):
                try:
                    value = float(value) if value else None
                except ValueError:
                    self._profile_error = f"{key} 需要有限的正数；未知请留空。"
                    self.operation_feedback.setText(self._profile_error)
                    return False
            values[key] = value
        values["polarity"] = self.polarity_combo.currentData()
        try:
            profile = ExperimentProfile.from_dict(values)
            self._validate_display_profile(profile)
        except ValueError as exc:
            self._profile_error = str(exc)
            self.operation_feedback.setText(f"方案尚未保存：{exc}")
            return False
        self._profile_error = None
        old_profile = self.profile
        self.profile = profile
        self._invalidate_mapping(old_profile, profile)
        self._clock_hz = profile.clock_hz
        self.profile_changed.emit(profile.to_dict())
        self._sync_experiment()
        return True

    def _invalidate_mapping(self, old_profile, new_profile):
        if any(getattr(old_profile, key) != getattr(new_profile, key)
               for key in ("detector_source", "signal_path", "polarity", "units_per_count", "signal_unit")):
            self.scope_mapping_confirmed.setChecked(False)
            if self.trace is not None and self.trace.source == "live":
                self._clear_observation("观测：信号映射已变化，请重新确认 CH1 并采集")

    def _clear_observation(self, label="观测：尚无数据"):
        self.trace = None
        self.replay = None
        self.waveform.set_trace([], [], source_label=label)
        self.trace_badge.setText(label)
        self.replay_label.setText("尚无当前判锁输入的波形；请导入数据或完成采集。")

    @staticmethod
    def _validate_display_profile(profile):
        if profile.clock_hz is not None:
            # Require representable UI coordinates, not an arbitrary assumed clock.
            cycles_to_us(2**32-1, profile.clock_hz)
        if profile.units_per_count is not None and not math.isfinite(profile.units_per_count * 32768):
            raise ValueError("标定倍率过大，无法显示内部信号范围")

    def set_parameters(self, parameters, source_label="本地配置", clock_hz=None):
        super().set_parameters(parameters, source_label, self.profile.clock_hz or clock_hz)
        if self._experiment_ready:
            self._operator_errors.clear()
            self._pending_refresh = None
            self.conflict_box.hide()
            self._sync_experiment()

    def _preview_changed(self, key, value):
        super()._preview_changed(key, value)
        if self._experiment_ready:
            self._sync_experiment()

    def stage_value(self, key, value):
        if key not in FIELD_NAMES or self._operator_sync:
            return
        validate_parameters({key: value}, for_write=True)
        self._operator_errors.pop(key, None)
        self._stage_legacy_value(key, value)

    def _duration_changed(self, key, text):
        super()._duration_changed(key, text)
        if self._experiment_ready and not self._syncing:
            if key not in self._invalid_fields:
                self._operator_errors.pop(key, None)
            self._sync_experiment()

    def _stage_legacy_value(self, key, value):
        """Load compatible values; inherited uint32 guard blocks unsafe new writes."""
        if key.startswith("time_"):
            getattr(self, "_"+key+"_editor").setText(str(value))
        elif key.startswith("coef_"):
            getattr(self, "_"+key+"_raw").setValue(value)
        else:
            getattr(self, "_"+key+"_editor").setValue(value)
        self._sync_experiment()

    def _operator_changed(self, key, value):
        if self._operator_sync:
            return
        try:
            if key.startswith("time_"):
                raw = us_to_cycles(value, self.profile.clock_hz)
            elif key.startswith("coef_"):
                raw = percent_to_q15(value)
            else:
                raw = round(value / (self.profile.units_per_count or 1))
            self.stage_value(key, raw)
        except ValueError as exc:
            # Keep the rejected visible value and block actions. A failed edit
            # must not silently fall back to the previous register value.
            self._operator_errors[key] = str(exc)
            self.operation_feedback.setText(str(exc))
            self._sync_experiment()

    def _mode_changed(self, *_):
        self._sync_experiment()

    def _sync_experiment(self):
        if not self._experiment_ready:
            return
        self._operator_sync = True
        auto = self.mode_combo.currentIndex() == 1
        try:
            for key, editor in self.operator_editors.items():
                is_auto = key.startswith("coef_")
                editor.setVisible(auto == is_auto)
                self.operator_labels[key].setVisible(auto == is_auto)
                enabled = key in self._preview
                value = self._preview.get(key, 0)
                if is_auto:
                    editor.setDecimals(6)
                    editor.setRange(-100, q15_to_percent(32767))
                    editor.setSuffix(" %")
                    value = q15_to_percent(value)
                elif key.startswith("time_"):
                    editor.setDecimals(6)
                    editor.setRange(0, cycles_to_us(2**32-1, self.profile.clock_hz) if self.profile.clock_hz else 2**32-1)
                    editor.setSuffix(" μs" if self.profile.clock_hz else " 周期")
                    value = cycles_to_us(value, self.profile.clock_hz) if self.profile.clock_hz else value
                    enabled = enabled and self.profile.clock_hz is not None and not auto
                else:
                    scale = self.profile.units_per_count or 1
                    editor.setDecimals(6 if self.profile.units_per_count else 0)
                    editor.setRange(-32768*scale, 32767*scale)
                    editor.setSuffix(" "+(self.profile.signal_unit if self.profile.units_per_count else "码"))
                    value *= scale
                editor.setEnabled(enabled)
                if key not in self._operator_errors:
                    editor.setValue(value)
        finally:
            self._operator_sync = False
        self.mode_hint.setText("扫描测量后自动生成阈值和时间；不是自动 PID 整定或自动重锁。手动判据不在本模式生效。" if auto else "信号持续低于入锁线 → 接入反馈；持续高于失锁线 → 退出锁定。")
        self.units_hint.setText("时间按已确认内核时钟换算；图中纵轴始终为内部信号码。" if self.profile.clock_hz else "请先在接线方案中确认内核时钟，才可用 μs 编辑时间；历史周期值保持不变。")
        pending = self.staged_parameters()
        self.diff_label.setText("\n".join(f"{FIELD_NAMES[k]}：{self._baseline.get(k, '—')} → {v}" for k, v in pending.items()) or "暂无修改 · 原始值保持不变")
        connected = bool(self.context.get("connected"))
        self.connection_badge.setText("设备：串口已连接" if connected else "设备：离线，可配置与回放")
        invalid = bool(self._operator_errors or self._invalid_fields)
        self.sync_badge.setText("参数：" + ("有无效输入，请更正" if invalid else "有待核对冲突" if self._conflict_message else "草稿未应用" if pending else self._source_label))
        self.write_button.setEnabled(connected and self.apply_button.isEnabled() and not invalid)
        self.local_button.setEnabled(not connected and bool(pending) and not invalid and not self._conflict_message)
        self.waveform.set_parameters(self._preview, clock_hz=self.profile.clock_hz)
        self.waveform.setEnabled(not auto)
        self.suggest_button.setEnabled(self.trace is not None and not auto)
        self._refresh_replay()
        self._refresh_diagnosis()

    def set_context(self, context):
        if self.context.get("routes", {}) != context.get("routes", {}):
            self.scope_mapping_confirmed.setChecked(False)
            if self.trace is not None and self.trace.source == "live":
                self._clear_observation("观测：画布连线已变化，请重新确认映射")
        self.context = dict(context)
        routes = context.get("routes", {})
        for key, button in self.route_buttons.items():
            button.setToolTip(routes.get(key, "尚未连接"))
        self.wiring_summary.setText("\n".join(f"{label}：{routes.get(key, '尚未连接')}" for key, label in (("signal", "判锁输入"), ("scan", "扫描同步"), ("pid", "PID 控制"), ("scan_control", "扫描控制"))))
        self._sync_experiment()

    def _refresh_diagnosis(self):
        issues = preflight(self.profile, self._preview, connected=bool(self.context.get("connected")),
                           topology_issues=self.context.get("topology_issues", []))
        messages = [item["message"] for item in issues]
        self.diagnosis.setText("检查与下一步：" + "；".join(messages[:4]) if messages else "本地检查通过；仍需设备参数回读与实际波形确认。")

    def set_trace(self, trace):
        if not isinstance(trace, WaveformTrace):
            raise ValueError("需要带来源的 WaveformTrace")
        self.trace = trace
        source = {"demo": "演示练习 · 非实测", "import": "文件回放 · 非实时", "live": "实测快照 · 非连续遥测"}[trace.source]
        label = source + (" · " + trace.label if trace.label else "")
        self.trace_badge.setText(label)
        self.waveform.set_trace(trace.time_s, trace.value, source_label=source)
        self._sync_experiment()

    def choose_trace(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入判锁波形：time_s,value", "", "CSV (*.csv)")
        if path:
            try:
                if Path(path).stat().st_size > MAX_CSV_BYTES:
                    raise ValueError("CSV 超过 2 MB，请截取所需波形区段")
                self.set_trace(parse_trace_csv(Path(path).read_text(encoding="utf-8-sig"), label=Path(path).name))
            except (OSError, ValueError) as exc:
                self.operation_feedback.setText(f"波形未替换：{exc}")

    def suggest_from_selection(self):
        if self.trace is None:
            return
        try:
            selection = self.waveform.selection or (None, None)
            result = suggest_parameters(self.trace, *selection, clock_hz=self.profile.clock_hz)
            for key, value in result["parameters"].items():
                if key in self._MANUAL_KEYS:
                    self.stage_value(key, value)
            self.operation_feedback.setText("仅生成草稿，未写 FPGA。" + str(result["explanation"]))
        except ValueError as exc:
            self.operation_feedback.setText(f"无法生成建议：{exc}")

    def _refresh_replay(self):
        if not self._experiment_ready or self.trace is None:
            return
        if self.mode_combo.currentIndex() == 1:
            self.replay = None
            self.replay_label.setText("自动模式由 FPGA 测量极值和脉宽；当前无自动测量结果回读。图上手动阈值仅供参考，不代表自动生效值。")
            return
        if not self.profile.clock_hz:
            self.replay = None
            self.replay_label.setText("已载入波形。确认内核时钟后可预演持续时间判据；当前未推断入锁事件。")
            return
        try:
            self.replay = replay_manual(self.trace, self._preview, self.profile.clock_hz)
            events = self.replay.get("events", [])
            detail = "；".join(f"{event['time_s']*1000:.3g} ms：{event['label']}" for event in events[:4])
            self.replay_label.setText("离线判据预演（非 FPGA 状态）：" + (detail or "当前区段未满足完整入锁条件，请检查阈值和持续时间。"))
        except ValueError as exc:
            self.replay = None
            self.replay_label.setText(f"预演待配置：{exc}")

    def undo_draft(self):
        self.set_parameters(self._baseline, self._source_label)
        self.operation_feedback.setText("已撤销未应用的参数草稿；设备未写入。")

    def _request_local_stage(self):
        if not self.local_button.isEnabled():
            return
        self.local_stage_requested.emit(self.staged_parameters())

    def start_experiment(self):
        self.context_requested.emit()
        if not self._profile_edited():
            return
        issues = preflight(self.profile, self._preview, connected=bool(self.context.get("connected")),
                           topology_issues=self.context.get("topology_issues", []))
        blockers = [i["message"] for i in issues if i.get("severity") == "error"]
        if self.profile.polarity != "dip":
            blockers.append("请先确认判锁输入在共振处为谷")
        if self.profile.clock_hz is None:
            blockers.append("请先确认内核时钟")
        if any(not getattr(self.profile, key).strip() for key in ("detector_source", "signal_path", "error_path", "scan_path", "actuator_path")):
            blockers.append("实验接线与执行器范围记录尚未完成")
        if not self.context.get("connected"):
            blockers.insert(0, "设备离线")
        if self.staged_parameters():
            blockers.append("有未应用的参数草稿，请先写入并核对")
        if self._conflict_message:
            blockers.append(self._conflict_message)
        if self._invalid_fields or self._operator_errors:
            blockers.append("参数输入无效，请更正或撤销草稿；不能按旧值启动")
        if self._preview.get("pc_cmd") != 0:
            blockers.append("当前不是待机请求；请先请求退出并确认设备行为，再重新启动")
        if blockers:
            self.operation_feedback.setText("启动未发送：" + "；".join(blockers))
            return
        self._request_command(self.mode_combo.currentIndex()+1)
        self.operation_feedback.setText(self.command_request_feedback.text())

    def request_idle(self):
        self._request_command(0)
        self.operation_feedback.setText(self.command_request_feedback.text() + " 这是退出请求，不是已停机或输出归零的确认。")

    def _request_command(self, value):
        if value != 0 and (self._invalid_fields or self._operator_errors):
            self.command_request_feedback.setText("参数输入无效；启动请求未发送。")
            return
        super()._request_command(value)

    def _request_apply(self):
        if self._operator_errors:
            self.operation_feedback.setText("参数输入无效；请更正或撤销草稿，未写入 FPGA。")
            return
        super()._request_apply()
        if self._experiment_ready:
            self.operation_feedback.setText(self.feedback.text())

    def set_apply_result(self, success, message="", *, readback_confirmed=False):
        super().set_apply_result(success, message, readback_confirmed=readback_confirmed)
        if self._experiment_ready:
            self.operation_feedback.setText(self.feedback.text())
            self._sync_experiment()

    def mark_conflict(self, message):
        super().mark_conflict(message)
        if self._experiment_ready:
            self.operation_feedback.setText(self.feedback.text())
            self._sync_experiment()

    def accept_refresh(self, parameters, source_label):
        if not self.staged_parameters():
            self.set_parameters(parameters, source_label)
            return
        self._pending_refresh = (dict(parameters), source_label, self.staged_parameters())
        differences = [f"{FIELD_NAMES[k]}：旧 {self._baseline.get(k)} / 新 {parameters.get(k)} / 草稿 {v}"
                       for k, v in self.staged_parameters().items()]
        self.conflict_label.setText("参数已重新读取，请选择如何处理草稿：\n" + "\n".join(differences))
        self.conflict_box.show()
        self.mark_conflict("已读取新基线；请明确选择采用设备值或保留草稿")

    def resolve_refresh(self, keep_draft):
        if self._pending_refresh is None:
            return
        parameters, source, changes = self._pending_refresh
        self.set_parameters(parameters, source)
        if keep_draft:
            for key, value in changes.items():
                self._stage_legacy_value(key, value)
        self._pending_refresh = None
        self.conflict_box.hide()
        self.operation_feedback.setText("已采用新基线；请核对草稿差异后再应用。" if keep_draft else "已采用设备值，旧草稿已丢弃。")

    def export_bundle(self):
        self._validate_visible_parameters()
        if not self._profile_edited():
            raise ValueError(self._profile_error)
        return {"version": 1, "profile": self.profile.to_dict(),
                "parameters": self.preview_parameters(), "mode": self.mode_combo.currentIndex(),
                "trace": self.trace.to_dict() if self.trace else None,
                "selection": list(self.waveform.selection) if self.waveform.selection else None}

    def _validate_visible_parameters(self):
        if self._operator_errors:
            raise ValueError("参数输入无效：" + "；".join(self._operator_errors.values()))
        # Valid historical uint32 values remain savable even when they cannot
        # be newly written through the int31 path. Malformed text cannot be
        # silently serialized as its last valid value.
        for key in ("time_scan", "time_lock"):
            if key not in self._preview:
                continue
            text = getattr(self, "_" + key + "_editor").text()
            if not text or len(text) > 10 or not all("0" <= c <= "9" for c in text):
                raise ValueError(FIELD_NAMES[key] + "必须是完整周期整数")
            if int(text) != self._preview[key]:
                raise ValueError(FIELD_NAMES[key] + "输入尚未有效，请更正或撤销草稿")
        validate_parameters(self._preview)

    def import_bundle(self, payload):
        if not isinstance(payload, dict) or type(payload.get("version")) is not int or payload["version"] != 1:
            raise ValueError("不支持的 PDH 实验方案版本")
        profile = ExperimentProfile.from_dict(payload.get("profile", {}))
        self._validate_display_profile(profile)
        params = validate_parameters(payload.get("parameters", {}))
        mode = payload.get("mode", 0)
        if type(mode) is not int or mode not in (0, 1):
            raise ValueError("不支持的锁定模式")
        trace = WaveformTrace.from_dict(payload["trace"]) if payload.get("trace") is not None else None
        if trace is not None and trace.source == "live":
            trace = WaveformTrace(trace.time_s, trace.value, "import", "已保存的快照回放 · " + trace.label[:1800])
        selection = payload.get("selection")
        if selection is not None:
            if trace is None or not isinstance(selection, list) or len(selection) != 2:
                raise ValueError("无效的波形选区")
            if not all(type(x) in (int, float) for x in selection) or not trace.time_s[0] <= selection[0] < selection[1] <= trace.time_s[-1]:
                raise ValueError("波形选区超出数据范围")
        # Parse the complete bundle before mutating visible state. Imported commands
        # are not executed or adopted as current hardware requests.
        self.set_parameters(self._baseline, self._source_label)
        self.set_profile(profile)
        for key, value in params.items():
            if key in FIELD_NAMES:
                if value == self._baseline.get(key):
                    continue
                self._stage_legacy_value(key, value)
        self.mode_combo.setCurrentIndex(mode)
        self.trace = None
        self.replay = None
        self.waveform.set_trace([], [], source_label="尚无数据")
        self.trace_badge.setText("观测：尚无数据")
        if trace is not None:
            self.set_trace(trace)
            if selection:
                self.waveform.set_selection(*selection)
        self.scope_mapping_confirmed.setChecked(False)
        self.operation_feedback.setText("方案已载入为本地草稿；未写 FPGA，未执行保存的控制请求。")

    @staticmethod
    def _atomic_json(path, payload):
        data = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
        file = QSaveFile(str(path))
        if not file.open(QIODevice.WriteOnly):
            raise OSError(file.errorString())
        if file.write(data) != len(data) or not file.commit():
            file.cancelWriting()
            raise OSError(file.errorString())

    def save_bundle(self, path):
        self._atomic_json(path, self.export_bundle())

    def load_bundle(self, path):
        path = Path(path)
        if path.stat().st_size > 16_000_000:
            raise ValueError("方案超过 16 MB")
        self.import_bundle(json.loads(path.read_text(encoding="utf-8")))

    def choose_bundle(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开 PDH 实验方案", "", "JSON (*.json)")
        if path:
            try:
                self.load_bundle(path)
            except (OSError, ValueError) as exc:
                self.operation_feedback.setText(f"方案未载入：{exc}")

    def choose_save_bundle(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存 PDH 实验方案", "pdh-experiment.json", "JSON (*.json)")
        if path:
            try:
                self.save_bundle(path)
                self.operation_feedback.setText("实验方案与波形已保存；这是本地记录，不代表硬件已应用。")
            except (OSError, ValueError) as exc:
                self.operation_feedback.setText(f"方案未保存：{exc}")

    def create_record(self):
        try:
            self._validate_visible_parameters()
        except ValueError as exc:
            self.operation_feedback.setText(f"记录未保存：{exc}")
            return
        if not self._profile_edited():
            return
        report = export_report(self.profile, self._preview, self.trace, self.replay)
        report += "\n\n## 当前参数来源\n\n" + self._source_label + "\n\n运行状态：固件未提供回读，不能确认已锁定。\n"
        self.record_requested.emit(report)
