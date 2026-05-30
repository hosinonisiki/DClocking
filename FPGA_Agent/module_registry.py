"""Module registry — structured descriptions of all FPGA modules for LLM context.

This module provides LLM-friendly descriptions of every available module type:
ports, signal types, parameters, typical use patterns, and compatibility.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Complete registry of all built-in modules
# ---------------------------------------------------------------------------

MODULE_REGISTRY: dict[str, dict] = {
    "PID控制器": {
        "display_name": "PID控制器",
        "internal_names": ["PIDC", "PID2"],
        "max_instances": 2,
        "purpose": "PID feedback controller for closed-loop stabilization, "
                   "laser locking, and general feedback control.",
        "category": "control",
        "inputs": [
            {"index": 0, "name": "RESET", "display": "关闭",
             "signal": ["bool"],
             "description": "Auto-reset/disable control. HIGH disables PID output."},
            {"index": 1, "name": "IN", "display": "误差信号",
             "signal": ["level", "phase"],
             "description": "Error signal input (setpoint - measurement)."},
        ],
        "outputs": [
            {"index": 0, "name": "OUT", "display": "反馈信号",
             "signal": ["level", "differential"],
             "description": "PID correction output."},
        ],
        "direct_params": [
            {"key": "gain_p", "label": "P增益", "type": "int",
             "min": -8388608, "max": 8388607, "note": "线性增益系数"},
            {"key": "gain_i", "label": "I增益", "type": "int",
             "min": -2147483648, "max": 2147483647, "note": "线性增益系数"},
            {"key": "gain_d", "label": "D增益", "type": "int",
             "min": -8388608, "max": 8388607, "note": "线性增益系数"},
            {"key": "setpoint", "label": "设定值", "type": "int",
             "min": -32768, "max": 32767, "note": "物理信号"},
            {"key": "limit_integral", "label": "积分限幅", "type": "int",
             "min": 0, "max": 32767},
            {"key": "limit_sum", "label": "输出限幅", "type": "int",
             "min": 0, "max": 32767},
            {"key": "enable_auto_reset", "label": "自动控制使能", "type": "bool"},
        ],
        "indirect_params": [
            {"key": "overall_gain", "label": "整体增益", "type": "float", "unit": "dB"},
            {"key": "pi_corner", "label": "PI交点频率", "type": "float", "unit": "Hz"},
            {"key": "pd_corner", "label": "PD交点频率", "type": "float", "unit": "Hz"},
            {"key": "saturation_gain", "label": "饱和增益", "type": "float", "unit": "dB"},
            {"key": "saturation_turning_frequency", "label": "饱和拐点频率",
             "type": "float", "unit": "Hz"},
        ],
        "typical_connections": [
            "P_.IN <— 混频器 output (error signal)",
            "P_.OUT —> 累加器 error input",
            "PDH状态机 PID_RESET —> P_.RESET",
        ],
    },

    "累加器": {
        "display_name": "累加器",
        "internal_names": ["ACCM", "ACC2"],
        "max_instances": 2,
        "purpose": "Phase/frequency accumulator. Integrates an input signal and "
                   "produces slow and fast sawtooth outputs. Core of NCO/DDS.",
        "category": "signal_gen",
        "inputs": [
            {"index": 0, "name": "ERROR_IN", "display": "外部反馈输入",
             "signal": ["level", "phase"],
             "description": "External feedback / error correction input."},
            {"index": 1, "name": "BIAS_IN", "display": "外部偏置输入",
             "signal": ["differential"],
             "description": "External bias offset (frequency control)."},
            {"index": 2, "name": "RESET", "display": "自动开关指令",
             "signal": ["bool"],
             "description": "Auto-reset control from state machine."},
            {"index": 3, "name": "PAUSE", "display": "暂停累加指令",
             "signal": ["bool"],
             "description": "Pause accumulation (hold current phase)."},
            {"index": 4, "name": "LF_RESET", "display": "环路滤波器开关指令",
             "signal": ["bool"],
             "description": "Reset the internal loop filter."},
        ],
        "outputs": [
            {"index": 0, "name": "SLOW_OUT", "display": "慢变累加值输出",
             "signal": ["level", "phase"],
             "description": "Slow-varying accumulated value (NCO phase)."},
            {"index": 1, "name": "FAST_OUT", "display": "快变累加值输出",
             "signal": ["level", "phase"],
             "description": "Fast-varying accumulated value."},
        ],
        "direct_params": [
            {"key": "enable_auto_reset", "label": "自动控制使能", "type": "bool"},
        ],
        "indirect_params": [
            {"key": "freq", "label": "频率", "type": "float",
             "min": 0, "max": 125e6, "unit": "Hz",
             "note": "Base frequency of the slow accumulator"},
            {"key": "ratio", "label": "频率比", "type": "int",
             "min": 1, "max": 32768,
             "note": "Fast/slow accumulator frequency ratio (power of 2)"},
        ],
        "typical_connections": [
            "A_.SLOW_OUT —> 三角函数运算器 phase input",
            "A_.FAST_OUT —> DAC output or monitor",
            "A_.ERROR_IN <— PID controller output",
            "PDH状态机 SCAN_RESET —> A_.RESET",
        ],
    },

    "三角函数运算器": {
        "display_name": "三角函数运算器",
        "internal_names": ["TRIG", "TRI2", "TRI3", "TRI4"],
        "max_instances": 4,
        "purpose": "CORDIC-based sine/cosine calculator. Converts phase input "
                   "to sine and cosine amplitude outputs.",
        "category": "math",
        "inputs": [
            {"index": 0, "name": "IN", "display": "相位信号输入",
             "signal": ["phase"],
             "description": "Phase input (from accumulator or other source)."},
        ],
        "outputs": [
            {"index": 0, "name": "SIN", "display": "正弦信号输出",
             "signal": ["level"],
             "description": "Sine amplitude output."},
            {"index": 1, "name": "COS", "display": "余弦信号输出",
             "signal": ["level"],
             "description": "Cosine amplitude output."},
        ],
        "direct_params": [],
        "indirect_params": [],
        "typical_connections": [
            "T_.IN <— 累加器.SLOW_OUT (phase source)",
            "T_.SIN —> 混频器 input (modulation/demodulation)",
            "T_.COS —> 混频器 input (I/Q reference)",
        ],
    },

    "反三角函数运算器": {
        "display_name": "反三角函数运算器",
        "internal_names": ["ATAN", "ATA2"],
        "max_instances": 2,
        "purpose": "CORDIC-based arctangent calculator. Converts sine/cosine "
                   "amplitudes back to phase.",
        "category": "math",
        "inputs": [
            {"index": 0, "name": "SIN", "display": "正弦信号输入",
             "signal": ["level"],
             "description": "Sine amplitude input."},
            {"index": 1, "name": "COS", "display": "余弦信号输入",
             "signal": ["level"],
             "description": "Cosine amplitude input."},
        ],
        "outputs": [
            {"index": 0, "name": "OUT", "display": "相位信号输出",
             "signal": ["phase"],
             "description": "Computed phase output."},
        ],
        "direct_params": [],
        "indirect_params": [],
        "typical_connections": [
            "A_.SIN <— 混频器 output (I component)",
            "A_.COS <— 混频器 output (Q component)",
            "A_.OUT —> PID controller error input",
        ],
    },

    "线性缩放器": {
        "display_name": "线性缩放器",
        "internal_names": ["SCLR", "SCL2", "SCL3", "SCL4"],
        "max_instances": 4,
        "purpose": "Linear signal scaler with gain, bias, and output limiting. "
                   "Useful for signal conditioning between modules.",
        "category": "conditioning",
        "inputs": [
            {"index": 0, "name": "IN", "display": "信号输入",
             "signal": ["level", "phase", "differential"],
             "description": "Generic physical signal input."},
        ],
        "outputs": [
            {"index": 0, "name": "OUT", "display": "信号输出",
             "signal": ["level", "phase", "differential"],
             "description": "Scaled signal output."},
        ],
        "direct_params": [
            {"key": "scale", "label": "缩放系数", "type": "int",
             "min": -8388608, "max": 8388607},
            {"key": "bias", "label": "偏置量", "type": "int",
             "min": -32768, "max": 32767},
            {"key": "upper_limit", "label": "输出上限", "type": "int",
             "min": -32768, "max": 32767},
            {"key": "lower_limit", "label": "输出下限", "type": "int",
             "min": -32768, "max": 32767},
            {"key": "enable_wrapping", "label": "环绕使能", "type": "bool"},
        ],
        "indirect_params": [
            {"key": "gain", "label": "增益", "type": "float", "unit": "dB"},
        ],
        "typical_connections": [
            "S_.IN <— any physical signal source",
            "S_.OUT —> any physical signal consumer",
        ],
    },

    "FIR滤波器": {
        "display_name": "FIR滤波器",
        "internal_names": ["FIRF", "FIR2", "FIR3", "FIR4"],
        "max_instances": 4,
        "purpose": "64-tap FIR filter with programmable coefficients. "
                   "Supports lowpass, highpass, bandpass design via scipy.",
        "category": "filter",
        "inputs": [
            {"index": 0, "name": "IN", "display": "信号输入",
             "signal": ["level", "differential"],
             "description": "Signal to be filtered."},
        ],
        "outputs": [
            {"index": 0, "name": "OUT", "display": "信号输出",
             "signal": ["level", "differential"],
             "description": "Filtered signal output."},
        ],
        "direct_params": [],
        "indirect_params": [],
        "special_methods": [
            {"name": "design_lowpass",
             "description": "Design a lowpass FIR filter",
             "params": {
                 "freq_pass": {"type": "float", "description": "Passband cutoff (Hz)"},
                 "freq_stop": {"type": "float", "description": "Stopband cutoff (Hz)"},
                 "freq_sample": {"type": "float", "description": "Sample rate (Hz)"},
                 "weight": {"type": "float", "description": "Stopband weight (default 1)"},
                 "taps": {"type": "int", "description": "Tap count: 16, 32, or 64"},
             }},
        ],
        "typical_connections": [
            "F_.IN <— signal source (mixer output, ADC, etc.)",
            "F_.OUT —> next processing stage",
        ],
    },

    "IIR滤波器": {
        "display_name": "IIR滤波器",
        "internal_names": ["IIRF", "IIR2", "IIR3", "IIR4"],
        "max_instances": 4,
        "purpose": "IIR biquad filter (2 second-order sections). Supports "
                   "Butterworth, Chebyshev I/II, and Elliptic designs.",
        "category": "filter",
        "inputs": [
            {"index": 0, "name": "IN", "display": "信号输入",
             "signal": ["level", "differential"],
             "description": "Signal to be filtered."},
        ],
        "outputs": [
            {"index": 0, "name": "OUT", "display": "信号输出",
             "signal": ["level", "differential"],
             "description": "Filtered signal output."},
        ],
        "direct_params": [],
        "indirect_params": [],
        "special_methods": [
            {"name": "design_lowpass",
             "description": "Design an IIR lowpass filter",
             "params": {
                 "filter_type": {"type": "str",
                                 "enum": ["butter", "cheby1", "cheby2", "ellip"],
                                 "description": "Filter type"},
                 "freq_pass": {"type": "float", "description": "Passband cutoff (Hz)"},
                 "freq_sample": {"type": "float", "description": "Sample rate (Hz)"},
             }},
        ],
        "typical_connections": [
            "I_.IN <— signal source",
            "I_.OUT —> next processing stage",
        ],
    },

    "线性变换器": {
        "display_name": "线性变换器",
        "internal_names": ["LTRN", "LTR2"],
        "max_instances": 2,
        "purpose": "2×2 linear transformation (matrix multiply). Transforms "
                   "two input signals A,B into two outputs via a 2×2 matrix.",
        "category": "math",
        "inputs": [
            {"index": 0, "name": "IN_A", "display": "信号A输入",
             "signal": ["level", "differential"],
             "description": "First input channel."},
            {"index": 1, "name": "IN_B", "display": "信号B输入",
             "signal": ["level", "differential"],
             "description": "Second input channel."},
        ],
        "outputs": [
            {"index": 0, "name": "OUT_A", "display": "信号A输出",
             "signal": ["level", "differential"],
             "description": "Transformed output A."},
            {"index": 1, "name": "OUT_B", "display": "信号B输出",
             "signal": ["level", "differential"],
             "description": "Transformed output B."},
        ],
        "direct_params": [],
        "indirect_params": [
            {"key": "a00", "label": "矩阵元素00", "type": "float",
             "min": -1.0, "max": 1.0},
            {"key": "a01", "label": "矩阵元素01", "type": "float",
             "min": -1.0, "max": 1.0},
            {"key": "a10", "label": "矩阵元素10", "type": "float",
             "min": -1.0, "max": 1.0},
            {"key": "a11", "label": "矩阵元素11", "type": "float",
             "min": -1.0, "max": 1.0},
        ],
        "typical_connections": [
            "For I/Q rotation: IN_A=cos, IN_B=sin, set matrix to rotation angles",
        ],
    },

    "混频器": {
        "display_name": "混频器",
        "internal_names": ["MIXR", "MIX2", "MIX3", "MIX4"],
        "max_instances": 4,
        "purpose": "Signal multiplier/mixer. Multiplies two input signals. "
                   "Used for modulation, demodulation, and phase detection.",
        "category": "math",
        "inputs": [
            {"index": 0, "name": "IN_A", "display": "信号A输入",
             "signal": ["level"],
             "description": "First multiplicand."},
            {"index": 1, "name": "IN_B", "display": "信号B输入",
             "signal": ["level"],
             "description": "Second multiplicand."},
        ],
        "outputs": [
            {"index": 0, "name": "OUT", "display": "混频信号输出",
             "signal": ["level", "differential"],
             "description": "Product output (A × B)."},
        ],
        "direct_params": [],
        "indirect_params": [],
        "typical_connections": [
            "M_.IN_A <— signal input (e.g. PDH photodetector)",
            "M_.IN_B <— local oscillator (e.g. TRIG.COS reference)",
            "M_.OUT —> lowpass filter —> PID error input",
        ],
        "connections_with": ["三角函数运算器", "FIR滤波器", "IIR滤波器",
                             "PID控制器", "线性缩放器"],
    },

    "解卷绕器": {
        "display_name": "解卷绕器",
        "internal_names": ["UNWR"],
        "max_instances": 1,
        "purpose": "Phase unwrapper. Removes 2π discontinuities from a phase "
                   "signal, producing a continuous phase output.",
        "category": "conditioning",
        "inputs": [
            {"index": 0, "name": "IN", "display": "相位信号输入",
             "signal": ["phase"],
             "description": "Wrapped phase input."},
        ],
        "outputs": [
            {"index": 0, "name": "OUT", "display": "解卷绕相位信号输出",
             "signal": ["phase"],
             "description": "Unwrapped continuous phase output."},
        ],
        "direct_params": [],
        "indirect_params": [],
        "typical_connections": [
            "U_.IN <— 反三角函数运算器.OUT",
            "U_.OUT —> next stage",
        ],
    },

    "PDH状态机": {
        "display_name": "PDH状态机",
        "internal_names": ["PDHS"],
        "max_instances": 1,
        "purpose": "Pound-Drever-Hall lock state machine. Manages the locking "
                   "sequence: idle → scan → lock → hold → unlock on signal loss.",
        "category": "control",
        "inputs": [
            {"index": 0, "name": "IN_POWER", "display": "透射光强信号输入",
             "signal": ["level"],
             "description": "Transmitted optical power / cavity transmission."},
            {"index": 1, "name": "IN_SCAN", "display": "锯齿波扫描输入",
             "signal": ["level"],
             "description": "Sawtooth scan signal for monitoring."},
        ],
        "outputs": [
            {"index": 0, "name": "PID_RESET_CTRL", "display": "PID复位信号",
             "signal": ["bool"],
             "description": "PID reset/enable control. HIGH = PID active."},
            {"index": 1, "name": "MIXER_RESET_CTRL", "display": "混频器复位信号",
             "signal": ["bool"],
             "description": "Mixer gating control."},
            {"index": 2, "name": "SCAN_RESET_CTRL", "display": "扫描复位信号",
             "signal": ["bool"],
             "description": "Scan accumulator reset."},
        ],
        "direct_params": [
            {"key": "pc_cmd", "label": "工作模式", "type": "int",
             "min": 0, "max": 3,
             "note": "0=idle, 1=manual scan, 2=auto cal, 3=auto lock"},
        ],
        "indirect_params": [],
        "typical_connections": [
            "P.PID_RESET_CTRL —> PID.RESET",
            "P.MIXER_RESET_CTRL —> MIXER gating",
            "P.SCAN_RESET_CTRL —> ACC.RESET",
            "P.IN_POWER <— photodetector signal",
            "P.IN_SCAN <— ACC.FAST_OUT (sawtooth)",
        ],
        "connections_with": ["PID控制器", "累加器", "混频器"],
    },

    "LO自动校准状态机": {
        "display_name": "LO自动校准状态机",
        "internal_names": ["SCLO", "SLO2"],
        "max_instances": 2,
        "purpose": "Local oscillator auto-calibration state machine. Samples "
                   "residual phase and generates bias correction.",
        "category": "control",
        "inputs": [
            {"index": 0, "name": "PHASE_IN", "display": "剩余相位输入",
             "signal": ["phase"],
             "description": "Residual phase error from phase detector."},
        ],
        "outputs": [
            {"index": 0, "name": "BIAS_OUT", "display": "相位校准值输出",
             "signal": ["differential"],
             "description": "Phase bias correction value."},
            {"index": 1, "name": "PID_RESET_CTRL", "display": "PID复位信号",
             "signal": ["bool"],
             "description": "PID reset control."},
        ],
        "direct_params": [
            {"key": "lock", "label": "锁定指令", "type": "bool",
             "note": "Rising edge: update calibration + enable PID"},
            {"key": "clear", "label": "清除指令", "type": "bool",
             "note": "Rising edge: clear calibration to zero"},
        ],
        "indirect_params": [],
        "typical_connections": [
            "S.PHASE_IN <— phase detector output",
            "S.BIAS_OUT —> accumulator BIAS_IN",
            "S.PID_RESET_CTRL —> PID.RESET",
        ],
    },
}

# ---------------------------------------------------------------------------
# Special nodes (not FPGA modules, but present on canvas)
# ---------------------------------------------------------------------------

SPECIAL_NODES: dict[str, dict] = {
    "布尔值：是": {
        "display_name": "布尔值：是",
        "internal_names": ["HIGH1", "HIGH2", "HIGH3", "HIGH4", "HIGH5"],
        "max_instances": -1,  # unlimited
        "purpose": "Constant boolean HIGH (True/1) source for control ports.",
        "category": "constant",
        "inputs": [],
        "outputs": [
            {"index": 0, "name": "OUT", "display": "输出",
             "signal": ["bool"],
             "description": "Constant HIGH."},
        ],
        "direct_params": [],
        "indirect_params": [],
    },
    "布尔值：否": {
        "display_name": "布尔值：否",
        "internal_names": ["LOW1", "LOW2", "LOW3", "LOW4", "LOW5"],
        "max_instances": -1,
        "purpose": "Constant boolean LOW (False/0) source for control ports.",
        "category": "constant",
        "inputs": [],
        "outputs": [
            {"index": 0, "name": "OUT", "display": "输出",
             "signal": ["bool"],
             "description": "Constant LOW."},
        ],
        "direct_params": [],
        "indirect_params": [],
    },
}

# ---------------------------------------------------------------------------
# Composite modules
# ---------------------------------------------------------------------------

COMPOSITE_MODULES: dict[str, dict] = {
    "正弦波发生器": {
        "display_name": "正弦波发生器",
        "purpose": "Composite: 累加器 + 三角函数运算器. Outputs sine/cosine "
                   "at a configurable frequency.",
        "sub_modules": ["累加器", "三角函数运算器"],
        "auto_connections": [
            {"src_sub_idx": 0, "src_port": 0, "dst_sub_idx": 1, "dst_port": 0,
             "note": "累加器.SLOW_OUT → 三角函数运算器.IN"},
        ],
        "params": ["freq", "enable_auto_reset"],
    },
    "数字控制振荡器": {
        "display_name": "数字控制振荡器",
        "purpose": "Composite: 累加器 + 2×三角函数运算器. NCO with I/Q outputs.",
        "sub_modules": ["累加器", "三角函数运算器", "三角函数运算器"],
        "auto_connections": [],
    },
}

# ---------------------------------------------------------------------------
# Border ports (system ADC/DAC channels)
# ---------------------------------------------------------------------------

BORDER_PORTS = {
    "inputs": [  # DAC outputs from FPGA = "输入通道" (sources on canvas)
        {"name": f"Border_out_{i}", "display": f"输入通道{chr(65+i)}",
         "signal": ["bool", "level", "phase", "differential"],
         "port_type": "out"}
        for i in range(8)
    ],
    "outputs": [  # ADC inputs to FPGA = "输出通道" (sinks on canvas)
        {"name": f"Border_in_{i}", "display": f"输出通道{chr(65+i)}",
         "signal": ["bool", "level", "phase", "differential"],
         "port_type": "in"}
        for i in range(8)
    ],
}


# ---------------------------------------------------------------------------
# Signal type compatibility matrix
# ---------------------------------------------------------------------------

SIGNAL_COMPAT = {
    "level":       {"level", "phase", "differential"},
    "phase":       {"phase"},
    "differential": {"level", "differential"},
    "bool":        {"bool"},
}

# ---------------------------------------------------------------------------
# PDH locking reference pattern
# ---------------------------------------------------------------------------

PDH_LOCKING_PATTERN = """
## PDH Locking Standard Topology

PDH locking requires the following modules and connections:

1. **Signal generation chain:**
   - `累加器` (ACCM): frequency accumulator, produces sawtooth phase
   - `三角函数运算器` (TRIG): CORDIC, converts phase to sin/cos
   - Connect: ACCM.SLOW_OUT(port 0) → TRIG.IN(port 0)

2. **Error signal chain:**
   - `混频器` (MIXR): demodulates PDH error signal
   - Connect: TRIG.COS(port 1) → MIXR.IN_A(port 0) [modulation reference]
   - Connect: [photodetector signal, e.g. via ADC] → MIXR.IN_B(port 1)

3. **Feedback chain:**
   - `PID控制器` (PIDC): computes correction from error
   - Connect: MIXR.OUT(port 0) → PIDC.IN(port 1) [error signal]
   - Connect: PIDC.OUT(port 0) → ACCM.ERROR_IN(port 0)

4. **State machine control:**
   - `PDH状态机` (PDHS): manages lock sequence
   - Connect: PDHS.PID_RESET_CTRL(port 0) → PIDC.RESET(port 0)
   - Connect: PDHS.SCAN_RESET_CTRL(port 2) → ACCM.RESET(port 2)
   - Connect: PDHS.MIXER_RESET_CTRL(port 1) → MIXR.IN_B gating
   - Connect: ACCM.FAST_OUT(port 1) → PDHS.IN_SCAN(port 1)

5. **Output monitoring:**
   - Connect: ACCM.FAST_OUT(port 1) → 输出通道 (DAC monitor)
   - Connect: PIDC.OUT(port 0) → 输出通道 (error monitor)
"""


def get_module(name: str) -> dict | None:
    """Look up a module by its Chinese display name."""
    if name in MODULE_REGISTRY:
        return MODULE_REGISTRY[name]
    if name in SPECIAL_NODES:
        return SPECIAL_NODES[name]
    if name in COMPOSITE_MODULES:
        return COMPOSITE_MODULES[name]
    return None


def list_all_modules() -> list[str]:
    """Return all placeable module type names."""
    names = list(MODULE_REGISTRY.keys())
    names += list(SPECIAL_NODES.keys())
    names += list(COMPOSITE_MODULES.keys())
    return names


def get_internal_name(display_name: str, index: int = 0) -> str:
    """Get the internal (short) name for a module instance."""
    mod = get_module(display_name)
    if mod and "internal_names" in mod:
        names = mod["internal_names"]
        if index < len(names):
            return names[index]
        return f"{names[0]}{index + 1}"
    return display_name


def check_signal_compat(out_signals: list[str],
                        in_signals: list[str],
                        developer_mode: bool = False) -> bool:
    """Check if two port signal type lists are compatible."""
    if set(out_signals) & set(in_signals):
        return True
    if developer_mode:
        physical = {"level", "phase", "differential"}
        if (set(out_signals) & physical) and (set(in_signals) & physical):
            return True
    return False


def build_llm_context(include_patterns: bool = True) -> str:
    """Format all modules as LLM-readable markdown context."""
    lines = ["# Available FPGA Signal Processing Modules\n"]

    lines.append("## Basic Modules\n")
    for name, mod in MODULE_REGISTRY.items():
        lines.append(f"### {name} ({', '.join(mod['internal_names'])})")
        lines.append(f"**Purpose**: {mod['purpose']}")
        lines.append(f"**Max instances**: {mod['max_instances']}")
        lines.append(f"**Category**: {mod['category']}")

        if mod["inputs"]:
            lines.append("**Inputs**:")
            for p in mod["inputs"]:
                lines.append(f"  - [{p['index']}] {p['name']} ({p['display']}) "
                             f"— signals: {p['signal']}")
        if mod["outputs"]:
            lines.append("**Outputs**:")
            for p in mod["outputs"]:
                lines.append(f"  - [{p['index']}] {p['name']} ({p['display']}) "
                             f"— signals: {p['signal']}")
        lines.append("")

    lines.append("## Constant / Special Nodes\n")
    for name, mod in SPECIAL_NODES.items():
        lines.append(f"### {name}")
        lines.append(f"**Purpose**: {mod['purpose']}")
        if mod["outputs"]:
            for p in mod["outputs"]:
                lines.append(f"  - [{p['index']}] {p['name']} "
                             f"— signals: {p['signal']}")
        lines.append("")

    lines.append("## Composite Modules\n")
    for name, mod in COMPOSITE_MODULES.items():
        lines.append(f"### {name}")
        lines.append(f"**Purpose**: {mod['purpose']}")
        lines.append(f"**Contains**: {', '.join(mod['sub_modules'])}")
        lines.append("")

    lines.append("## System I/O (Border Ports)\n")
    lines.append("- **输入通道A-H** (Border_out_0..7): "
                 "External signal sources (e.g., ADC inputs). "
                 "Appear as output ports on the left edge of canvas.")
    lines.append("- **输出通道A-H** (Border_in_0..7): "
                 "External signal sinks (e.g., DAC outputs). "
                 "Appear as input ports on the right edge of canvas.")
    lines.append("")

    if include_patterns:
        lines.append(PDH_LOCKING_PATTERN)

    return "\n".join(lines)
