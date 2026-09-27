"""Shared, side-effect-free PDH experiment vocabulary and offline analysis.

No Qt, transport, file writes or hardware operations belong here.  The seven
legacy register names remain the wire/storage ABI.  Suggestions and sampled
trace replay are never firmware telemetry or proof of an optical lock.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, fields
from decimal import Decimal, ROUND_HALF_UP
import io
import math
from collections.abc import Mapping


MAX_WRITE_CYCLES = 2**31 - 1
MAX_LEGACY_CYCLES = 2**32 - 1
MAX_TRACE_SAMPLES = 20_000
MAX_CSV_BYTES = 2_000_000
_REGISTERS = {
    "pc_cmd": (0, 3),
    "threshold_signal_lock": (-32768, 32767),
    "threshold_signal_scan": (-32768, 32767),
    "time_scan": (0, MAX_LEGACY_CYCLES),
    "time_lock": (0, MAX_LEGACY_CYCLES),
    "coef_scan": (-32768, 32767),
    "coef_lock": (-32768, 32767),
}


def _number(value, name, *, positive=False):
    if type(value) not in (int, float):
        raise ValueError(f"{name} 必须是有限数值，不能是布尔或字符串")
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid or (positive and value <= 0):
        raise ValueError(f"{name} 必须是{'正的' if positive else ''}有限数值")
    return value


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} 必须是 {low}～{high} 范围内的整数")
    return value


def _text(value, name, *, required=False, limit=2048):
    if type(value) is not str or len(value) > limit or (required and not value.strip()):
        raise ValueError(f"{name} 必须是{'非空' if required else ''}文本，最多 {limit} 字符")


def _mapping(data, allowed, name):
    if not isinstance(data, Mapping) or set(data) - set(allowed):
        raise ValueError(f"{name} 必须是对象且不能包含未知字段")


@dataclass(frozen=True)
class ExperimentProfile:
    """Operator-confirmed apparatus facts, not assumed firmware defaults."""

    version: int = 1
    name: str = "未命名实验"
    detector_source: str = ""
    polarity: str = "unknown"
    signal_path: str = ""
    error_path: str = ""
    scan_path: str = ""
    actuator_path: str = ""
    clock_hz: float | None = None
    units_per_count: float | None = None
    signal_unit: str = "内部信号码"
    notes: str = ""

    def __post_init__(self):
        _integer(self.version, "实验方案版本", 1, 1)
        for key in ("name", "detector_source", "signal_path", "error_path", "scan_path",
                    "actuator_path", "signal_unit", "notes"):
            _text(getattr(self, key), key, required=key in ("name", "signal_unit"),
                  limit=8192 if key == "notes" else 2048)
        if type(self.polarity) is not str or self.polarity not in ("unknown", "dip", "peak"):
            raise ValueError("共振方向只能是 unknown、dip 或 peak")
        for key in ("clock_hz", "units_per_count"):
            if getattr(self, key) is not None:
                _number(getattr(self, key), key, positive=True)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        _mapping(data, (field.name for field in fields(cls)), "实验方案")
        return cls(**data)


def validate_parameters(parameters, *, for_write=False):
    """Return a detached partial register mapping; retain old uint32 timings."""
    _mapping(parameters, _REGISTERS, "PDH 参数")
    result = {}
    for key, value in parameters.items():
        low, high = _REGISTERS[key]
        if for_write and key in ("time_scan", "time_lock"):
            high = MAX_WRITE_CYCLES
        result[key] = _integer(value, key, low, high)
    return result


def cycles_to_us(cycles, clock_hz):
    """Display legacy uint32 values without truncating them."""
    _integer(cycles, "时钟周期", 0, MAX_LEGACY_CYCLES)
    _number(clock_hz, "已确认的状态机时钟", positive=True)
    result = float(Decimal(cycles) * Decimal(1_000_000) / Decimal(str(clock_hz)))
    return _number(result, "换算后的时间")


def us_to_cycles(duration_us, clock_hz):
    """New writes use safe signed-counter range; halfway values round up."""
    _number(duration_us, "确认时间")
    _number(clock_hz, "已确认的状态机时钟", positive=True)
    if duration_us < 0:
        raise ValueError("确认时间不能为负")
    cycles = Decimal(str(duration_us)) * Decimal(str(clock_hz)) / Decimal(1_000_000)
    if cycles > MAX_WRITE_CYCLES:
        raise ValueError("确认时间超过安全可写范围，请缩短时间")
    return int(cycles.to_integral_value(rounding=ROUND_HALF_UP))


def q15_to_percent(raw):
    return _integer(raw, "Q1.15", -32768, 32767) * 100 / 32768


def percent_to_q15(percent):
    _number(percent, "阈值百分比")
    if not -100 <= percent <= q15_to_percent(32767):
        raise ValueError("百分比超出 Q1.15 可表示范围（-100%～99.9969482421875%）")
    raw = Decimal(str(percent)) * Decimal(32768) / Decimal(100)
    return int(raw.to_integral_value(rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class WaveformTrace:
    """Bounded time-domain samples in PDHS input internal signed-16 units."""

    time_s: tuple[float, ...]
    value: tuple[float, ...]
    source: str = "import"
    label: str = ""

    def __post_init__(self):
        if not isinstance(self.time_s, (tuple, list)) or not isinstance(self.value, (tuple, list)):
            raise ValueError("波形时间和值必须是数组")
        if not 2 <= len(self.time_s) <= MAX_TRACE_SAMPLES or len(self.time_s) != len(self.value):
            raise ValueError(f"波形需要 2～{MAX_TRACE_SAMPLES} 个成对样本")
        if type(self.source) is not str or self.source not in ("demo", "import", "live"):
            raise ValueError("波形来源只能是 demo、import 或 live")
        _text(self.label, "波形名称")
        for index, (time, value) in enumerate(zip(self.time_s, self.value)):
            _number(time, "样本时间")
            _number(value, "样本值")
            if not -32768 <= value <= 32767:
                raise ValueError("波形样本必须是 PDHS 输入的有符号 16 位内部信号码")
            if index and time <= self.time_s[index - 1]:
                raise ValueError("样本时间必须严格递增")
        object.__setattr__(self, "time_s", tuple(self.time_s))
        object.__setattr__(self, "value", tuple(self.value))
        _number(self.duration_s, "波形时长", positive=True)

    @property
    def duration_s(self):
        return self.time_s[-1] - self.time_s[0]

    @property
    def minimum(self):
        return min(self.value)

    @property
    def maximum(self):
        return max(self.value)

    def to_dict(self):
        return {"time_s": list(self.time_s), "value": list(self.value),
                "source": self.source, "label": self.label}

    @classmethod
    def from_dict(cls, data):
        _mapping(data, ("time_s", "value", "source", "label"), "波形")
        if not {"time_s", "value"} <= set(data):
            raise ValueError("波形缺少 time_s 或 value")
        return cls(**data)


def parse_trace_csv(text, label="CSV"):
    """Parse a bounded UTF-8 CSV, never interpreting it as live telemetry."""
    if type(text) is not str or len(text) > MAX_CSV_BYTES or len(text.encode("utf-8")) > MAX_CSV_BYTES:
        raise ValueError("CSV 超过 2 MB 或不是文本")
    rows = csv.reader(io.StringIO(text.lstrip("\ufeff")), strict=True)
    times, values = [], []
    try:
        if next(rows, None) != ["time_s", "value"]:
            raise ValueError("CSV 表头应为 time_s,value；value 是 PDHS 输入内部信号码")
        for row in rows:
            if not row:
                continue
            if len(row) != 2 or len(times) >= MAX_TRACE_SAMPLES:
                raise ValueError("CSV 列数不正确或超过 20000 个样本")
            times.append(float(row[0]))
            values.append(float(row[1]))
    except (csv.Error, OverflowError) as exc:
        raise ValueError("CSV 解析失败") from exc
    return WaveformTrace(times, values, "import", label)


def demo_trace():
    """Deterministic instructional dip; never samples a connected device."""
    times = tuple(index * .00005 for index in range(401))
    values = tuple(18000 - 15000 * math.exp(-((time - .01) / .0015)**2) for time in times)
    return WaveformTrace(times, values, "demo", "DEMO · 合成共振谷（非设备采集）")


def _interval(trace, start_s, end_s):
    start = trace.time_s[0] if start_s is None else _number(start_s, "选区起点")
    end = trace.time_s[-1] if end_s is None else _number(end_s, "选区终点")
    if not trace.time_s[0] <= start < end <= trace.time_s[-1]:
        raise ValueError("选区必须在波形范围内且起点早于终点")
    samples = [(time, value) for time, value in zip(trace.time_s, trace.value) if start <= time <= end]
    if len(samples) < 2:
        raise ValueError("选区至少需要两个样本")
    return samples


def suggest_parameters(trace, start_s=None, end_s=None, clock_hz=None):
    """Draft dip thresholds from the selection; no command register is emitted."""
    samples = _interval(trace, start_s, end_s)
    minimum, maximum = min(v for _, v in samples), max(v for _, v in samples)
    if maximum - minimum < 2:
        raise ValueError("选区幅度变化不足，无法建议有效判据")
    enter = round(minimum + .25 * (maximum - minimum))
    loss = round(minimum + .65 * (maximum - minimum))
    parameters = {"threshold_signal_scan": enter, "threshold_signal_lock": loss,
                  "coef_scan": percent_to_q15(25), "coef_lock": percent_to_q15(65)}
    duration_basis = "未确认状态机时钟：仅建议阈值，不生成确认时间。"
    if clock_hz is not None:
        _number(clock_hz, "已确认的状态机时钟", positive=True)
        beginning, longest = None, 0.
        for time, value in samples:
            if value < enter:
                beginning = time if beginning is None else beginning
                longest = max(longest, time - beginning)
            else:
                beginning = None
        if longest > 0:
            parameters["time_scan"] = us_to_cycles(longest * .5e6, clock_hz)
            parameters["time_lock"] = us_to_cycles(longest * 4e6, clock_hz)
            duration_basis = "根据所选采样波形最长连续低于入锁线区段：入锁取半宽，失锁取四倍宽；仅为初始建议。"
        else:
            duration_basis = "所选采样波形未包含足够长的连续低值区段，不生成确认时间。"
    return {"parameters": validate_parameters(parameters, for_write=True), "source": trace.source,
            "provenance": "suggestion", "duration_basis": duration_basis,
            "explanation": "选区最小值到最大值的 25%/65% 位置作为谷形判据草稿；不是 FPGA 自动测量结果，也不会写入硬件。"}


def replay_manual(trace, parameters, clock_hz):
    """Sample-resolution manual criterion preview, not a clock-accurate FSM sim.

    Strict inequalities, continuous-condition reset, and no automatic re-entry
    after loss follow the manual mode.  Capture gaps, FPGA synchronizers and
    off-by-one counter clocks are deliberately not presented as measured events.
    """
    config = validate_parameters(parameters)
    required = {"threshold_signal_scan", "threshold_signal_lock", "time_scan", "time_lock"}
    if not required <= set(config):
        raise ValueError("预演需要完整的手动入锁/失锁阈值和确认时间")
    enter_seconds = cycles_to_us(config["time_scan"], clock_hz) / 1e6
    loss_seconds = cycles_to_us(config["time_lock"], clock_hz) / 1e6
    events, beginning, phase = [], None, "scanning"
    for time, value in zip(trace.time_s, trace.value):
        condition = value < config["threshold_signal_scan"] if phase == "scanning" else value > config["threshold_signal_lock"]
        if not condition:
            beginning = None
            continue
        beginning = time if beginning is None else beginning
        hold = enter_seconds if phase == "scanning" else loss_seconds
        # Relative tolerance only compensates binary timestamp subtraction.
        elapsed = time - beginning
        if elapsed < hold and not math.isclose(elapsed, hold, rel_tol=1e-12, abs_tol=0.):
            continue
        event = "predicted_enter" if phase == "scanning" else "predicted_loss"
        events.append({"time_s": time, "event": event,
                       "label": "预计接入反馈" if phase == "scanning" else "预计退出反馈"})
        if phase == "feedback":
            break  # Legacy manual mode returns to IDLE, not automatic rescanning.
        phase, beginning = "feedback", None
    return {"provenance": "prediction", "source": trace.source, "events": events,
            "warnings": ["离线采样判据预测，不是 FPGA 实时状态或光学锁定证明。",
                         "采样间隔内的穿越、硬件流水线与计数器周期不能从此波形精确还原。"],
            "summary": f"按手动判据预测到 {len(events)} 次切换；设备实际状态未提供。"}


def preflight(profile, parameters, *, connected=False, topology_issues=()):
    """Operator guidance; absence of messages never certifies hardware safety."""
    config = validate_parameters(parameters)
    messages = []

    def add(code, message, action, severity="warning"):
        messages.append({"code": code, "severity": severity, "message": message, "action": action})

    if not connected:
        add("offline", "设备未连接；当前仅可编辑草稿和回放。", "连接设备后再检查并应用参数")
    if profile.clock_hz is None:
        add("clock_unknown", "状态机时钟未确认，不能可靠换算确认时间。", "填写已验证的固件时钟，不要使用示波器采样率代替")
    if profile.polarity == "unknown":
        add("polarity_unknown", "尚未确认共振在判锁输入上表现为谷还是峰。", "观察判锁输入波形并确认方向")
    elif profile.polarity == "peak":
        add("polarity_incompatible", "现有固件按低于阈值入锁，不能直接捕获向上的峰。", "检查信号变换和极性；确认内部输入表现为谷", "error")
    for field, label in (("signal_path", "判锁信号链"), ("error_path", "误差信号链"),
                         ("scan_path", "扫描控制链"), ("actuator_path", "执行器输出")):
        if not getattr(profile, field).strip():
            add(f"{field}_missing", f"尚未记录{label}。", f"在实验方案中填写{label}并核对实际连接")
    if profile.units_per_count is None:
        add("calibration_unknown", "内部信号尚未标定，阈值按内部信号码显示。", "只有确认完整信号链标定后才能显示物理单位", "info")
    if config.get("threshold_signal_scan", -32768) >= config.get("threshold_signal_lock", 32767):
        add("threshold_order", "入锁线不低于失锁线，可能产生相互重叠的判据。", "在波形上确认两条阈值线及滞回区间")
    if any(config.get(key, 0) > MAX_WRITE_CYCLES for key in ("time_scan", "time_lock")):
        add("legacy_counter", "已保留旧版超范围周期值，未做截断；不适合作为新的写入值。", "核对原配置后明确选择安全确认时间", "error")
    if any(config.get(key, 0) < 0 for key in ("coef_scan", "coef_lock")):
        add("legacy_coefficient", "负的自动阈值位置可能落在测得范围之外；保留原值。", "在工程详情核对是否确实需要负系数")
    for issue in topology_issues:
        _text(issue, "接线检查结果")
        add("topology", issue, "定位并修正对应连接，再重新检查", "error")
    add("telemetry_unavailable", "设备运行阶段未提供，参数写入不代表已经锁定。", "通过实际采集信号及可用状态回读验证", "info")
    return messages


def export_report(profile, parameters, trace=None, replay=None):
    """Portable markdown snapshot with explicit evidence boundaries."""
    config = validate_parameters(parameters)
    safe = lambda value: str(value).replace("|", "\\|").replace("\n", " / ").replace("<", "&lt;")
    lines = [f"# PDH 实验记录：{safe(profile.name)}", "", "## 实验方案", "",
             "| 项目 | 内容 |", "| --- | --- |"]
    for key, value in profile.to_dict().items():
        lines.append(f"| {key} | {safe(value if value is not None else '未确认')} |")
    lines += ["", "## 参数快照（原有寄存器字段，未声明设备已同步）", "",
              "| 参数 | 数值 |", "| --- | --- |"]
    lines.extend(f"| {key} | {value} |" for key, value in config.items())
    lines += ["", "## 数据来源与状态", "", "设备实际运行状态：未提供。参数快照不证明光学锁定。"]
    if trace is None:
        lines.append("波形：未加载。")
    else:
        lines.append(f"波形来源：{trace.source} / {safe(trace.label)}；{len(trace.value)} 点，时长 {trace.duration_s:g} s。")
        lines.append("波形数值：PDHS 输入内部信号码；demo 为合成演示，import 为导入数据。")
    if replay is not None:
        lines += ["", "离线判据预测（不是 FPGA 事件回读）："]
        for event in replay.get("events", []):
            lines.append(f"- {safe(event.get('time_s'))} s：{safe(event.get('label', event.get('event')))}")
        if not replay.get("events"):
            lines.append("- 未预测到判据切换。")
    return "\n".join(lines) + "\n"
