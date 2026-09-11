"""FIR/IIR design models and response workbench widgets."""

import math

import numpy as np
from scipy import signal as scipy_signal
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QComboBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QToolButton, QVBoxLayout, QWidget,
)

import IIR
from qt_quantity_edit import QuantityLineEdit

__all__ = [
    "FIRDesignModel",
    "FIRResponseCanvas",
    "FIRDesignerWidget",
    "FIRDesignerWindow",
    "IIRDesignModel",
    "IIRResponseCanvas",
    "IIRDesignerWidget",
    "IIRDesignerWindow",
]


def _dispatch_workspace_open(source, key, title, widget):
    """Offer an expanded tool to the owning browser-style workspace."""
    top_level = source.window() if source is not None else None
    handler = getattr(top_level, "open_workspace_window", None)
    if not callable(handler):
        return False
    try:
        return bool(handler(key, title, widget, source=source))
    except Exception as exc:
        print(f"[workspace] open tab failed: {exc}")
        return False


def _log_frequency_grid(freq_sample, points):
    """Return a four-decade plotting grid ending at Nyquist."""
    nyquist = float(freq_sample) / 2.0
    return np.geomspace(nyquist * 1e-4, nyquist, int(points))


class FIRDesignModel:
    """Design and analyse the same low-pass FIR loaded by ``ModuleFIRFilter``."""

    DEFAULT_SPECS = {
        "freq_pass": 1_000_000.0,
        "freq_stop": 10_000_000.0,
        "freq_sample": 250_000_000.0,
        "weight": 1.0,
        "taps": 64,
    }

    @classmethod
    def normalized_specs(cls, specifications=None):
        specs = dict(cls.DEFAULT_SPECS)
        specs.update(dict(specifications or {}))
        try:
            specs["freq_pass"] = float(specs["freq_pass"])
            specs["freq_stop"] = float(specs["freq_stop"])
            specs["freq_sample"] = float(specs["freq_sample"])
            specs["weight"] = float(specs["weight"])
            specs["taps"] = int(specs["taps"])
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("FIR 规格包含无效数值") from exc
        return specs

    @classmethod
    def validate(cls, specifications=None):
        specs = cls.normalized_specs(specifications)
        values = (specs["freq_pass"], specs["freq_stop"], specs["freq_sample"], specs["weight"])
        if not all(math.isfinite(value) for value in values):
            raise ValueError("FIR 规格必须为有限数值")
        if specs["taps"] not in (16, 32, 64):
            raise ValueError("抽头数仅支持 16、32 或 64")
        if specs["freq_sample"] <= 0.0:
            raise ValueError("采样频率必须大于 0")
        if specs["freq_pass"] <= 0.0:
            raise ValueError("通带边缘必须大于 0")
        if specs["freq_stop"] <= specs["freq_pass"]:
            raise ValueError("阻带边缘必须大于通带边缘")
        if specs["freq_stop"] >= specs["freq_sample"] / 2.0:
            raise ValueError("阻带边缘必须低于 Nyquist 频率")
        if specs["weight"] <= 0.0:
            raise ValueError("阻带权重必须大于 0")
        return specs

    @classmethod
    def design(cls, specifications=None):
        specs = cls.validate(specifications)
        taps = specs["taps"]
        try:
            coefficients = scipy_signal.remez(
                taps,
                [0.0, specs["freq_pass"], specs["freq_stop"], specs["freq_sample"] / 2.0],
                [1.0, 0.0],
                fs=specs["freq_sample"],
                weight=[1.0, specs["weight"]],
            )
        except Exception as exc:
            raise ValueError(f"Remez 设计未收敛：{exc}") from exc

        peak = float(np.max(np.abs(coefficients)))
        if peak <= 0.0 or not math.isfinite(peak):
            raise ValueError("滤波器系数无法归一化")
        coefficients = np.asarray(coefficients, dtype=float) / peak * 0.98
        l1_norm = float(np.sum(np.abs(coefficients)))
        normalization = taps / 2.0 / l1_norm * 0.98
        max_normalization = 1024.0 / taps
        if normalization < 1.0 or normalization > max_normalization:
            raise ValueError(
                f"归一化系数 {normalization:.3f} 超出 FPGA 范围 1–{max_normalization:g}；"
                "请减小通带频率、增大阻带频率或增加抽头数"
            )

        q23_scale = float((2**23) - 1)
        coefficient_words = np.rint(coefficients * q23_scale).astype(np.int64)
        quantized = coefficient_words.astype(float) / q23_scale
        frequencies, response = scipy_signal.freqz(
            quantized,
            worN=768,
            fs=specs["freq_sample"],
        )
        amplitude = np.abs(response)
        pass_mask = frequencies <= specs["freq_pass"]
        reference = float(np.max(amplitude[pass_mask])) if np.any(pass_mask) else float(np.max(amplitude))
        reference = max(reference, 1e-18)
        magnitude_db = 20.0 * np.log10(np.maximum(amplitude / reference, 1e-9))
        phase_degrees = np.unwrap(np.angle(response)) * 180.0 / math.pi
        pass_values = magnitude_db[pass_mask]
        stop_values = magnitude_db[frequencies >= specs["freq_stop"]]
        passband_ripple = float(np.max(pass_values) - np.min(pass_values)) if pass_values.size else 0.0
        stopband_attenuation = float(max(0.0, -np.max(stop_values))) if stop_values.size else 0.0

        plot_frequencies = _log_frequency_grid(specs["freq_sample"], 1024)
        plot_angular = 2.0 * math.pi * plot_frequencies / specs["freq_sample"]
        plot_response = scipy_signal.freqz(quantized, worN=plot_angular)[1]
        plot_amplitude = np.abs(plot_response)
        plot_magnitude_db = 20.0 * np.log10(
            np.maximum(plot_amplitude / reference, 1e-9)
        )
        plot_phase_radians = np.unwrap(np.angle(plot_response))
        plot_phase_degrees = plot_phase_radians * 180.0 / math.pi
        plot_group_delay_seconds = (
            -np.gradient(plot_phase_radians, plot_angular) / specs["freq_sample"]
        )

        roots = np.roots(quantized) if len(quantized) > 1 else np.array([], dtype=complex)
        return {
            **specs,
            "coefficients": tuple(float(value) for value in coefficients),
            "coefficient_words": tuple(int(value) for value in coefficient_words),
            "quantized_coefficients": tuple(float(value) for value in quantized),
            "normalization": float(normalization),
            "frequencies_hz": tuple(float(value) for value in frequencies),
            "magnitude_db": tuple(float(value) for value in magnitude_db),
            "phase_degrees": tuple(float(value) for value in phase_degrees),
            "plot_frequencies_hz": tuple(float(value) for value in plot_frequencies),
            "plot_magnitude_db": tuple(float(value) for value in plot_magnitude_db),
            "plot_phase_degrees": tuple(float(value) for value in plot_phase_degrees),
            "plot_group_delay_seconds": tuple(
                float(value) for value in plot_group_delay_seconds
            ),
            "zeros": tuple((float(value.real), float(value.imag)) for value in roots),
            "passband_ripple_db": passband_ripple,
            "stopband_attenuation_db": stopband_attenuation,
            "transition_width_hz": specs["freq_stop"] - specs["freq_pass"],
            "group_delay_seconds": (taps - 1) / (2.0 * specs["freq_sample"]),
        }


class FIRResponseCanvas(QWidget):
    """Four-view scientific plot for an FPGA FIR design result."""

    VIEW_LABELS = {
        "magnitude": "幅频响应",
        "phase": "相位响应",
        "group_delay": "群时延",
        "impulse": "冲激响应",
        "zplane": "零极点图",
    }

    def __init__(self, parent=None, compact=True):
        super().__init__(parent)
        self._result = None
        self._view_mode = "magnitude"
        self.setObjectName("fir_response_canvas")
        self.setAccessibleName("FIR 响应分析图")
        self.setMinimumSize(310, 245)
        if compact:
            self.setFixedHeight(275)
        else:
            self.setMinimumSize(620, 420)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_design_result(self, result):
        self._result = dict(result) if isinstance(result, dict) else None
        self.update()

    def design_result(self):
        return dict(self._result) if self._result is not None else None

    def set_view_mode(self, view_mode):
        if view_mode not in self.VIEW_LABELS:
            raise ValueError(f"Unknown FIR view mode: {view_mode}")
        self._view_mode = view_mode
        self.update()

    @staticmethod
    def _format_frequency(value):
        for scale, suffix in ((1e9, "GHz"), (1e6, "MHz"), (1e3, "kHz")):
            if abs(value) >= scale:
                return f"{value / scale:.3g}{suffix}"
        return f"{value:.3g}Hz"

    @staticmethod
    def _format_duration(value):
        absolute = abs(value)
        for scale, suffix in ((1.0, "s"), (1e-3, "ms"), (1e-6, "μs"), (1e-9, "ns")):
            if absolute >= scale:
                return f"{value / scale:.3g}{suffix}"
        return f"{value / 1e-12:.3g}ps"

    @staticmethod
    def _map_linear(value, low, high, pixel_low, pixel_high):
        span = max(1e-12, high - low)
        return pixel_low + (value - low) / span * (pixel_high - pixel_low)

    @staticmethod
    def _map_log(value, low, high, pixel_low, pixel_high):
        log_low = math.log10(low)
        span = max(1e-12, math.log10(high) - log_low)
        return pixel_low + (math.log10(max(low, value)) - log_low) / span * (
            pixel_high - pixel_low
        )

    @classmethod
    def _frequency_axis(cls, result):
        frequencies = result.get("plot_frequencies_hz", result["frequencies_hz"])
        positive = [float(value) for value in frequencies if value > 0.0]
        nyquist = float(result["freq_sample"]) / 2.0
        return positive, min(positive), nyquist

    @classmethod
    def _log_frequency_labels(cls, low, high, max_labels=6):
        candidates = [low]
        first_decade = math.ceil(math.log10(low))
        last_decade = math.floor(math.log10(high))
        candidates.extend(
            10.0**exponent
            for exponent in range(first_decade, last_decade + 1)
            if low < 10.0**exponent < high
        )
        candidates.append(high)
        if len(candidates) > max_labels:
            indices = np.rint(np.linspace(0, len(candidates) - 1, max_labels)).astype(int)
            candidates = [candidates[index] for index in dict.fromkeys(indices)]
        log_low = math.log10(low)
        log_span = max(1e-12, math.log10(high) - log_low)
        # Always retain both axis endpoints. Drop an adjacent decade label when
        # it would collide with either endpoint (for example 100 and 125 MHz).
        minimum_spacing = 0.10
        while len(candidates) > 2:
            first_gap = (math.log10(candidates[1]) - log_low) / log_span
            if first_gap >= minimum_spacing:
                break
            del candidates[1]
        while len(candidates) > 2:
            last_gap = (
                math.log10(high) - math.log10(candidates[-2])
            ) / log_span
            if last_gap >= minimum_spacing:
                break
            del candidates[-2]
        return [
            ((math.log10(value) - log_low) / log_span, cls._format_frequency(value))
            for value in candidates
        ]

    def _draw_frame(self, painter, rect):
        painter.fillRect(rect, QColor("#F7F8FA"))
        painter.setPen(QPen(QColor("#C7CDD6"), 1))
        painter.drawRoundedRect(rect, 8, 8)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(8)
        painter.setFont(title_font)
        painter.setPen(QColor("#243447"))
        painter.drawText(
            QRectF(rect.left() + 12, rect.top() + 7, rect.width() - 24, 16),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"FIR · {self.VIEW_LABELS[self._view_mode]}",
        )
        painter.setPen(QColor("#7B8492"))
        painter.drawText(
            QRectF(rect.right() - 145, rect.top() + 7, 133, 16),
            Qt.AlignRight | Qt.AlignVCenter,
            "Q1.23 · FPGA PREVIEW",
        )

    def _draw_grid(self, painter, plot_rect, x_labels, y_labels):
        painter.setPen(QPen(QColor("#E2E6EB"), 1, Qt.DotLine))
        label_font = QFont()
        label_font.setPointSize(6)
        painter.setFont(label_font)
        for fraction, text in x_labels:
            x = plot_rect.left() + fraction * plot_rect.width()
            painter.setPen(QPen(QColor("#E2E6EB"), 1, Qt.DotLine))
            painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))
            painter.setPen(QColor("#6C7685"))
            painter.drawText(QRectF(x - 30, plot_rect.bottom() + 3, 60, 13), Qt.AlignCenter, text)
        for fraction, text in y_labels:
            y = plot_rect.bottom() - fraction * plot_rect.height()
            painter.setPen(QPen(QColor("#E2E6EB"), 1, Qt.DotLine))
            painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))
            painter.setPen(QColor("#6C7685"))
            painter.drawText(QRectF(plot_rect.left() - 43, y - 7, 38, 14), Qt.AlignRight | Qt.AlignVCenter, text)
        painter.setPen(QPen(QColor("#C7CDD6"), 1))
        painter.drawRect(plot_rect)

    def _draw_magnitude(self, painter, plot_rect, result):
        frequencies, axis_low, nyquist = self._frequency_axis(result)
        pass_x = self._map_log(
            result["freq_pass"], axis_low, nyquist, plot_rect.left(), plot_rect.right()
        )
        stop_x = self._map_log(
            result["freq_stop"], axis_low, nyquist, plot_rect.left(), plot_rect.right()
        )
        pass_color = QColor("#DFF3EC")
        transition_color = QColor("#FFF1D8")
        stop_color = QColor("#F3E4E9")
        painter.fillRect(QRectF(plot_rect.left(), plot_rect.top(), pass_x - plot_rect.left(), plot_rect.height()), pass_color)
        painter.fillRect(
            QRectF(pass_x, plot_rect.top(), stop_x - pass_x, plot_rect.height()),
            transition_color,
        )
        painter.fillRect(
            QRectF(stop_x, plot_rect.top(), plot_rect.right() - stop_x, plot_rect.height()),
            stop_color,
        )
        self._draw_grid(
            painter,
            plot_rect,
            self._log_frequency_labels(axis_low, nyquist),
            [(fraction, f"{-100 + fraction * 105:.0f}") for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)],
        )
        for frequency, label, color in (
            (result["freq_pass"], "FP", QColor("#1F8F75")),
            (result["freq_stop"], "FS", QColor("#A4003B")),
        ):
            x = self._map_log(frequency, axis_low, nyquist, plot_rect.left(), plot_rect.right())
            painter.setPen(QPen(color, 1, Qt.DashLine))
            painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))
            painter.setPen(color)
            painter.drawText(QRectF(x - 15, plot_rect.top() + 3, 30, 12), Qt.AlignCenter, label)

        path = QPainterPath()
        active = False
        magnitudes = result.get("plot_magnitude_db", result["magnitude_db"])
        for frequency, magnitude in zip(frequencies, magnitudes):
            clipped = max(-100.0, min(5.0, magnitude))
            point = QPointF(
                self._map_log(frequency, axis_low, nyquist, plot_rect.left(), plot_rect.right()),
                self._map_linear(clipped, -100.0, 5.0, plot_rect.bottom(), plot_rect.top()),
            )
            if not active:
                path.moveTo(point)
                active = True
            else:
                path.lineTo(point)
        painter.setPen(QPen(QColor("#1769FF"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)
        painter.setPen(QColor("#6C7685"))
        painter.drawText(QRectF(plot_rect.left() - 40, plot_rect.top() - 15, 36, 12), Qt.AlignRight, "dB")

    def _draw_phase(self, painter, plot_rect, result):
        frequencies, axis_low, nyquist = self._frequency_axis(result)
        phases = result.get("plot_phase_degrees", result["phase_degrees"])
        phase_min = math.floor(min(phases) / 180.0) * 180.0
        phase_max = max(0.0, math.ceil(max(phases) / 180.0) * 180.0)
        if phase_max <= phase_min:
            phase_max = phase_min + 360.0
        self._draw_grid(
            painter,
            plot_rect,
            self._log_frequency_labels(axis_low, nyquist),
            [(fraction, f"{phase_min + fraction * (phase_max - phase_min):.0f}°") for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)],
        )
        path = QPainterPath()
        for index, (frequency, phase) in enumerate(zip(frequencies, phases)):
            point = QPointF(
                self._map_log(frequency, axis_low, nyquist, plot_rect.left(), plot_rect.right()),
                self._map_linear(phase, phase_min, phase_max, plot_rect.bottom(), plot_rect.top()),
            )
            path.moveTo(point) if index == 0 else path.lineTo(point)
        painter.setPen(QPen(QColor("#25A8A2"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)

    def _draw_group_delay(self, painter, plot_rect, result):
        frequencies, axis_low, nyquist = self._frequency_axis(result)
        delays = np.asarray(result["plot_group_delay_seconds"], dtype=float)
        finite_delays = delays[np.isfinite(delays)]
        if not finite_delays.size:
            painter.setPen(QColor("#7B8492"))
            painter.drawText(plot_rect, Qt.AlignCenter, "群时延不可用")
            return

        magnitudes = np.asarray(result.get("plot_magnitude_db", ()), dtype=float)
        reliable = np.isfinite(delays)
        if magnitudes.shape == delays.shape:
            # Phase derivatives become ill-conditioned near deep stopband
            # zeros. They remain in the curve, but do not dictate the scale.
            reliable &= np.isfinite(magnitudes) & (magnitudes >= -40.0)
        axis_delays = delays[reliable]
        if axis_delays.size >= 20:
            robust_min, robust_max = np.percentile(axis_delays, (1.0, 99.0))
        elif axis_delays.size:
            robust_min = float(np.min(axis_delays))
            robust_max = float(np.max(axis_delays))
        else:
            robust_min = float(np.min(finite_delays))
            robust_max = float(np.max(finite_delays))
        delay_min = min(0.0, float(robust_min))
        delay_max = max(0.0, float(robust_max))
        delay_span = delay_max - delay_min
        if delay_span <= 0.0:
            delay_span = max(abs(delay_min), abs(delay_max), 1e-15)
        padding = delay_span * 0.05
        delay_min -= padding
        delay_max += padding

        cutoff_x = self._map_log(
            result["freq_pass"], axis_low, nyquist, plot_rect.left(), plot_rect.right()
        )
        painter.fillRect(
            QRectF(
                plot_rect.left(),
                plot_rect.top(),
                cutoff_x - plot_rect.left(),
                plot_rect.height(),
            ),
            QColor("#DFF3EC"),
        )
        y_fractions = (0.0, 0.25, 0.5, 0.75, 1.0)
        y_labels = [
            (
                fraction,
                self._format_duration(delay_min + (delay_max - delay_min) * fraction),
            )
            for fraction in y_fractions
        ]
        self._draw_grid(
            painter,
            plot_rect,
            self._log_frequency_labels(axis_low, nyquist),
            y_labels,
        )

        path = QPainterPath()
        active = False
        for frequency, delay in zip(frequencies, delays):
            if not math.isfinite(delay):
                active = False
                continue
            point = QPointF(
                self._map_log(frequency, axis_low, nyquist, plot_rect.left(), plot_rect.right()),
                self._map_linear(
                    delay,
                    delay_min,
                    delay_max,
                    plot_rect.bottom(),
                    plot_rect.top(),
                ),
            )
            if active:
                path.lineTo(point)
            else:
                path.moveTo(point)
                active = True
        painter.setPen(QPen(QColor("#7A4CC2"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.save()
        painter.setClipRect(plot_rect)
        painter.drawPath(path)
        painter.restore()
        painter.setPen(QColor("#6C7685"))
        painter.drawText(
            QRectF(plot_rect.left() - 44, plot_rect.top() - 15, 40, 12),
            Qt.AlignRight,
            "τg",
        )

    def _draw_impulse(self, painter, plot_rect, result):
        coefficients = result["quantized_coefficients"]
        peak = max(1e-9, max(abs(value) for value in coefficients))
        y_limit = peak * 1.12
        self._draw_grid(
            painter,
            plot_rect,
            [(fraction, str(round((len(coefficients) - 1) * fraction))) for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)],
            [(fraction, f"{-y_limit + fraction * 2.0 * y_limit:.2f}") for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)],
        )
        zero_y = self._map_linear(0.0, -y_limit, y_limit, plot_rect.bottom(), plot_rect.top())
        painter.setPen(QPen(QColor("#A4003B"), 1))
        painter.setBrush(QColor("#A4003B"))
        for index, coefficient in enumerate(coefficients):
            x = self._map_linear(index, 0, max(1, len(coefficients) - 1), plot_rect.left(), plot_rect.right())
            y = self._map_linear(coefficient, -y_limit, y_limit, plot_rect.bottom(), plot_rect.top())
            painter.drawLine(QPointF(x, zero_y), QPointF(x, y))
            painter.drawEllipse(QPointF(x, y), 1.8, 1.8)

    def _draw_zplane(self, painter, plot_rect, result):
        side = min(plot_rect.width(), plot_rect.height())
        square = QRectF(
            plot_rect.center().x() - side / 2.0,
            plot_rect.center().y() - side / 2.0,
            side,
            side,
        )
        painter.fillRect(plot_rect, QColor("#FFFFFF"))
        painter.setPen(QPen(QColor("#D7DCE4"), 1))
        painter.drawRect(plot_rect)
        center = square.center()
        radius = side * 0.42
        painter.setPen(QPen(QColor("#AEB6C1"), 1, Qt.DashLine))
        painter.drawEllipse(center, radius, radius)
        painter.drawLine(QPointF(center.x() - radius * 1.15, center.y()), QPointF(center.x() + radius * 1.15, center.y()))
        painter.drawLine(QPointF(center.x(), center.y() - radius * 1.15), QPointF(center.x(), center.y() + radius * 1.15))
        painter.setPen(QPen(QColor("#1769FF"), 1.5))
        for real, imaginary in result["zeros"]:
            x = center.x() + max(-1.2, min(1.2, real)) * radius
            y = center.y() - max(-1.2, min(1.2, imaginary)) * radius
            painter.drawEllipse(QPointF(x, y), 3.2, 3.2)
        painter.setPen(QPen(QColor("#A4003B"), 2))
        painter.drawLine(QPointF(center.x() - 4, center.y() - 4), QPointF(center.x() + 4, center.y() + 4))
        painter.drawLine(QPointF(center.x() - 4, center.y() + 4), QPointF(center.x() + 4, center.y() - 4))
        painter.setPen(QColor("#6C7685"))
        painter.drawText(QRectF(square.right() - 18, center.y() + 3, 30, 13), Qt.AlignLeft, "Re")
        painter.drawText(QRectF(center.x() + 4, square.top() - 2, 30, 13), Qt.AlignLeft, "Im")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(1, 1, -1, -1)
        self._draw_frame(painter, rect)
        plot_rect = QRectF(rect.left() + 48, rect.top() + 42, rect.width() - 62, rect.height() - 70)
        painter.fillRect(plot_rect, QColor("#FFFFFF"))
        if self._result is None:
            painter.setPen(QColor("#7B8492"))
            painter.drawText(plot_rect, Qt.AlignCenter, "输入有效规格后生成 FPGA 预览")
            painter.end()
            return

        if self._view_mode == "magnitude":
            self._draw_magnitude(painter, plot_rect, self._result)
        elif self._view_mode == "phase":
            self._draw_phase(painter, plot_rect, self._result)
        elif self._view_mode == "group_delay":
            self._draw_group_delay(painter, plot_rect, self._result)
        elif self._view_mode == "impulse":
            self._draw_impulse(painter, plot_rect, self._result)
        else:
            self._draw_zplane(painter, plot_rect, self._result)
        painter.end()


class FIRDesignerWidget(QWidget):
    """MATLAB-inspired FIR workbench adapted to the narrow FPGA inspector."""

    def __init__(self, parent=None, apply_callback=None, initial_values=None, compact=True, allow_expand=True):
        super().__init__(parent)
        self.setObjectName("fir_designer_widget")
        self.setAccessibleName("FIR 可视化设计器")
        self._apply_callback = apply_callback
        self._initial_values = dict(initial_values or {})
        self._result = None
        self._expanded_window = None
        initial_specs = self._initial_values.get("design_lowpass", FIRDesignModel.DEFAULT_SPECS)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(9)

        header = QHBoxLayout()
        header.setSpacing(7)
        title = QLabel("FIR FILTER DESIGNER")
        title.setObjectName("fir_designer_title")
        method_chip = QLabel("REMEZ · Q1.23")
        method_chip.setObjectName("fir_method_chip")
        header.addWidget(title)
        header.addWidget(method_chip)
        header.addStretch()
        if allow_expand:
            expand_button = QToolButton(self)
            expand_button.setObjectName("fir_designer_expand_button")
            expand_button.setAccessibleName("在独立窗口中打开 FIR 设计器")
            expand_button.setToolTip("在独立窗口中打开 FIR 设计工作台")
            expand_button.setText("↗")
            expand_button.setCursor(Qt.PointingHandCursor)
            expand_button.clicked.connect(self.open_expanded_window)
            header.addWidget(expand_button)
        root.addLayout(header)

        specification_panel = QWidget(self)
        specification_panel.setObjectName("fir_specification_panel")
        spec_layout = QGridLayout(specification_panel)
        spec_layout.setContentsMargins(0, 0, 0, 0)
        spec_layout.setHorizontalSpacing(8)
        spec_layout.setVerticalSpacing(6)

        response_combo = QComboBox()
        response_combo.setObjectName("fir_response_type_combo")
        response_combo.setAccessibleName("FIR 响应类型")
        response_combo.addItem("低通 / Low-pass", "lowpass")
        spec_layout.addWidget(QLabel("响应类型"), 0, 0)
        spec_layout.addWidget(response_combo, 0, 1)

        self._taps_combo = QComboBox()
        self._taps_combo.setObjectName("fir_taps_combo")
        self._taps_combo.setAccessibleName("FIR 抽头数")
        for taps in (16, 32, 64):
            self._taps_combo.addItem(f"{taps} taps", taps)
        spec_layout.addWidget(QLabel("抽头数"), 1, 0)
        spec_layout.addWidget(self._taps_combo, 1, 1)

        field_specs = (
            ("freq_sample", "采样频率", 1.0, 1e12, "Hz"),
            ("freq_pass", "通带边缘 FP", 0.0, 1e12, "Hz"),
            ("freq_stop", "阻带边缘 FS", 0.0, 1e12, "Hz"),
            ("weight", "阻带权重", 1e-6, 1e6, ""),
        )
        self._editors = {}
        for row, (key, label, minimum, maximum, unit) in enumerate(field_specs, start=2):
            field = {
                "key": key,
                "label": label,
                "type": "float",
                "min": minimum,
                "max": maximum,
                "unit": unit,
            }
            editor = QuantityLineEdit(value=float(initial_specs.get(key, FIRDesignModel.DEFAULT_SPECS[key])), field=field)
            editor.setObjectName(f"fir_{key}_edit")
            editor.setAccessibleName(label)
            self._editors[key] = editor
            spec_layout.addWidget(QLabel(label), row, 0)
            spec_layout.addWidget(editor, row, 1)

        taps_index = self._taps_combo.findData(int(initial_specs.get("taps", 64)))
        self._taps_combo.setCurrentIndex(max(0, taps_index))

        analysis_panel = QWidget(self)
        analysis_layout = QVBoxLayout(analysis_panel)
        analysis_layout.setContentsMargins(0, 0, 0, 0)
        analysis_layout.setSpacing(7)
        view_row = QHBoxLayout()
        view_label = QLabel("ANALYSIS")
        view_label.setObjectName("fir_analysis_label")
        self._view_combo = QComboBox()
        self._view_combo.setObjectName("fir_analysis_view_combo")
        self._view_combo.setAccessibleName("FIR 分析视图")
        for key, label in FIRResponseCanvas.VIEW_LABELS.items():
            self._view_combo.addItem(label, key)
        view_row.addWidget(view_label)
        view_row.addStretch()
        view_row.addWidget(self._view_combo)
        analysis_layout.addLayout(view_row)

        self._canvas = FIRResponseCanvas(self, compact=compact)
        analysis_layout.addWidget(self._canvas, 1)
        self._metrics_label = QLabel("—")
        self._metrics_label.setObjectName("fir_metric_summary")
        self._metrics_label.setWordWrap(True)
        analysis_layout.addWidget(self._metrics_label)

        if compact:
            root.addWidget(specification_panel)
            root.addWidget(analysis_panel)
        else:
            body = QHBoxLayout()
            body.setSpacing(14)
            specification_panel.setFixedWidth(300)
            body.addWidget(specification_panel, 0)
            body.addWidget(analysis_panel, 1)
            root.addLayout(body, 1)

        footer = QHBoxLayout()
        self._status_label = QLabel("正在计算…")
        self._status_label.setObjectName("fir_design_status")
        self._status_label.setWordWrap(True)
        self._apply_btn = QPushButton("应用到 FIR")
        self._apply_btn.setObjectName("fir_design_apply_button")
        self._apply_btn.setAccessibleName("应用 FIR 设计")
        self._apply_btn.setProperty("variant", "primary")
        footer.addWidget(self._status_label, 1)
        footer.addWidget(self._apply_btn, 0)
        root.addLayout(footer)

        self.setStyleSheet(
            "#fir_designer_title { color: #243447; font-weight: 700; letter-spacing: 1px; }"
            "#fir_method_chip { color: #8F123D; background: #F5E6EB; border: 1px solid #E5C7D2; "
            "border-radius: 8px; padding: 2px 7px; font-size: 10px; }"
            "#fir_analysis_label { color: #6C7685; font-size: 10px; font-weight: 700; letter-spacing: 1px; }"
            "#fir_metric_summary { color: #586273; background: #F1F3F6; border-radius: 5px; "
            "padding: 6px; font-size: 10px; }"
            "#fir_design_status { color: #667180; font-size: 10px; }"
            "#fir_designer_expand_button { color: #243447; background: #FFFFFF; border: 1px solid #C7CDD6; "
            "border-radius: 5px; font-size: 15px; font-weight: 600; min-width: 26px; min-height: 26px; }"
            "#fir_designer_expand_button:hover { color: #9B0036; border-color: #9B0036; background: #FFF5F8; }"
        )

        for editor in self._editors.values():
            editor.textChanged.connect(self._refresh_preview)
        self._taps_combo.currentIndexChanged.connect(self._refresh_preview)
        self._view_combo.currentIndexChanged.connect(self._change_view)
        self._apply_btn.clicked.connect(self._apply_design)
        self._refresh_preview()

    def _collect_specs(self):
        specs = {}
        for key, editor in self._editors.items():
            value = editor.preview_quantity_value()
            if value is None:
                raise ValueError(f"{editor.accessibleName()}输入无效")
            specs[key] = float(value)
        specs["taps"] = int(self._taps_combo.currentData())
        return FIRDesignModel.validate(specs)

    def specifications(self):
        try:
            return self._collect_specs()
        except ValueError:
            return dict(FIRDesignModel.DEFAULT_SPECS)

    def design_result(self):
        return dict(self._result) if self._result is not None else None

    def set_specifications(self, specifications):
        specs = FIRDesignModel.normalized_specs(specifications)
        for key, editor in self._editors.items():
            editor.blockSignals(True)
            editor.set_quantity_value(specs[key])
            editor.blockSignals(False)
        self._taps_combo.blockSignals(True)
        index = self._taps_combo.findData(specs["taps"])
        if index >= 0:
            self._taps_combo.setCurrentIndex(index)
        self._taps_combo.blockSignals(False)
        self._refresh_preview()

    def _refresh_preview(self, *_):
        try:
            self._result = FIRDesignModel.design(self._collect_specs())
            self._canvas.set_design_result(self._result)
            self._metrics_label.setText(
                f"通带纹波  {self._result['passband_ripple_db']:.2f} dB   ·   "
                f"阻带抑制  {self._result['stopband_attenuation_db']:.1f} dB\n"
                f"过渡带  {self._format_frequency(self._result['transition_width_hz'])}   ·   "
                f"群时延  {self._result['group_delay_seconds'] * 1e9:.1f} ns   ·   "
                f"归一化  {self._result['normalization']:.3f}"
            )
            self._status_label.setText("FPGA 规格有效 · 预览已同步")
            self._status_label.setStyleSheet("color: #1F7A64;")
            self._apply_btn.setEnabled(True)
        except Exception as exc:
            self._result = None
            self._canvas.set_design_result(None)
            self._metrics_label.setText("等待有效设计规格")
            self._status_label.setText(str(exc))
            self._status_label.setStyleSheet("color: #A4003B;")
            self._apply_btn.setEnabled(False)

    def _change_view(self, *_):
        self._canvas.set_view_mode(self._view_combo.currentData())

    def _apply_design(self):
        if self._apply_callback is None:
            return
        try:
            specs = self._collect_specs()
            FIRDesignModel.design(specs)
            self._apply_callback("design_lowpass", specs)
            self._initial_values["design_lowpass"] = dict(specs)
            self._status_label.setText("设计已提交到现有 FIR 硬件写入链路")
            self._status_label.setStyleSheet("color: #1F7A64;")
        except Exception as exc:
            self._status_label.setText(f"应用失败：{exc}")
            self._status_label.setStyleSheet("color: #A4003B;")

    @staticmethod
    def _format_frequency(value):
        return FIRResponseCanvas._format_frequency(value)

    def open_expanded_window(self):
        workspace_key = f"fir-designer:{id(self)}"
        workspace_title = self.property("workspaceTitle") or "FIR 滤波器设计"
        if self._expanded_window is not None:
            try:
                if _dispatch_workspace_open(
                    self,
                    workspace_key,
                    workspace_title,
                    self._expanded_window,
                ):
                    return self._expanded_window
                if self._expanded_window.isVisible():
                    self._expanded_window.raise_()
                    self._expanded_window.activateWindow()
                    return self._expanded_window
            except RuntimeError:
                self._expanded_window = None
        self._expanded_window = FIRDesignerWindow(
            self.specifications(),
            apply_callback=self._apply_from_expanded_window,
            parent=self.window(),
        )
        self._expanded_window.destroyed.connect(self._clear_expanded_window)
        if _dispatch_workspace_open(
            self,
            workspace_key,
            workspace_title,
            self._expanded_window,
        ):
            return self._expanded_window
        self._expanded_window.show()
        self._expanded_window.raise_()
        self._expanded_window.activateWindow()
        return self._expanded_window

    def _apply_from_expanded_window(self, method_name, specs):
        if self._apply_callback is not None:
            self._apply_callback(method_name, specs)
        self.set_specifications(specs)

    def _clear_expanded_window(self, *_):
        self._expanded_window = None


class FIRDesignerWindow(QDialog):
    def __init__(self, specifications=None, apply_callback=None, parent=None):
        super().__init__(parent)
        self.setObjectName("fir_designer_window")
        self.setAccessibleName("FIR 可视化设计独立窗口")
        self.setWindowTitle("FIR Filter Designer · FPGA 工作台")
        self.setModal(False)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setMinimumSize(900, 580)
        self.resize(1120, 720)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        initial = {"design_lowpass": dict(specifications or FIRDesignModel.DEFAULT_SPECS)}
        self._designer = FIRDesignerWidget(
            self,
            apply_callback=apply_callback,
            initial_values=initial,
            compact=False,
            allow_expand=False,
        )
        layout.addWidget(self._designer)


class IIRDesignModel:
    """Design and analyse the quantized parallel-biquad IIR used by the FPGA."""

    DEFAULT_SPECS = {
        "filter_type": "butter",
        "freq_pass": 1_000_000.0,
        "freq_sample": 250_000_000.0,
    }
    FILTER_LABELS = {
        "butter": "Butterworth · 平坦幅频",
        "ellip": "Elliptic · 最陡过渡",
        "cheby1": "Chebyshev I · 通带等波纹",
        "cheby2": "Chebyshev II · 阻带等波纹",
        "bessel": "Bessel · 平坦群时延",
    }

    @classmethod
    def normalized_specs(cls, specifications=None):
        specs = dict(cls.DEFAULT_SPECS)
        specs.update(dict(specifications or {}))
        specs["filter_type"] = str(specs.get("filter_type", "butter")).strip().lower()
        try:
            specs["freq_pass"] = float(specs["freq_pass"])
            specs["freq_sample"] = float(specs["freq_sample"])
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("IIR 规格包含无效数值") from exc
        return specs

    @classmethod
    def validate(cls, specifications=None):
        specs = cls.normalized_specs(specifications)
        if specs["filter_type"] not in cls.FILTER_LABELS:
            raise ValueError("不支持的 IIR 滤波器类型")
        if not all(math.isfinite(specs[key]) for key in ("freq_pass", "freq_sample")):
            raise ValueError("IIR 规格必须为有限数值")
        if specs["freq_sample"] <= 0.0:
            raise ValueError("采样频率必须大于 0")
        if specs["freq_pass"] <= 0.0:
            raise ValueError("通带截止频率必须大于 0")
        if specs["freq_pass"] >= specs["freq_sample"] / 2.0:
            raise ValueError("通带截止频率必须低于 Nyquist 频率")
        return specs

    @staticmethod
    def _quantize(values, fractional_bits):
        scale = float(2**fractional_bits)
        words = np.rint(np.asarray(values, dtype=float) * scale).astype(np.int64)
        if np.any(words < -(2**26)) or np.any(words >= 2**26):
            raise ValueError("IIR 系数超出 FPGA 27 位定点数范围")
        return words, words.astype(float) / scale

    @classmethod
    def design(cls, specifications=None):
        specs = cls.validate(specifications)
        try:
            b1, a1, b2, a2 = IIR.get_IIR_parameters(
                specs["filter_type"], specs["freq_pass"], specs["freq_sample"]
            )
        except Exception as exc:
            raise ValueError(f"IIR 设计失败：{exc}") from exc

        branch_b = (np.asarray(b1, dtype=float), np.asarray(b2, dtype=float))
        feedback_a = (
            np.asarray(a1[4::4], dtype=float),
            np.asarray(a2[4::4], dtype=float),
        )
        b_words = []
        b_quantized = []
        a_words = []
        a_quantized = []
        for branch in branch_b:
            words, values = cls._quantize(branch, 24)
            b_words.append(words)
            b_quantized.append(values)
        for feedback in feedback_a:
            words, values = cls._quantize(feedback, 25)
            a_words.append(words)
            a_quantized.append(values)

        # The FPGA stores positive recurrence coefficients. scipy.signal uses
        # the equivalent transfer denominator 1 - a4*z^-4 - a8*z^-8.
        denominators = []
        for feedback in a_quantized:
            denominator = np.zeros(9, dtype=float)
            denominator[0] = 1.0
            denominator[4] = -feedback[0]
            denominator[8] = -feedback[1]
            denominators.append(denominator)

        frequencies = np.linspace(0.0, specs["freq_sample"] / 2.0, 1024)
        angular = 2.0 * math.pi * frequencies / specs["freq_sample"]
        branch_responses = [
            scipy_signal.freqz(b, a, worN=angular)[1]
            for b, a in zip(b_quantized, denominators)
        ]
        response = branch_responses[0] + branch_responses[1]
        amplitude = np.abs(response)
        dc_reference = max(float(amplitude[0]), 1e-18)
        magnitude_db = 20.0 * np.log10(np.maximum(amplitude / dc_reference, 1e-9))
        phase_radians = np.unwrap(np.angle(response))
        phase_degrees = phase_radians * 180.0 / math.pi

        plot_frequencies = _log_frequency_grid(specs["freq_sample"], 1536)
        plot_angular = 2.0 * math.pi * plot_frequencies / specs["freq_sample"]
        plot_branch_responses = [
            scipy_signal.freqz(b, a, worN=plot_angular)[1]
            for b, a in zip(b_quantized, denominators)
        ]
        plot_response = plot_branch_responses[0] + plot_branch_responses[1]
        plot_magnitude_db = 20.0 * np.log10(
            np.maximum(np.abs(plot_response) / dc_reference, 1e-9)
        )
        plot_phase_radians = np.unwrap(np.angle(plot_response))
        plot_phase_degrees = plot_phase_radians * 180.0 / math.pi
        plot_group_delay_seconds = (
            -np.gradient(plot_phase_radians, plot_angular) / specs["freq_sample"]
        )

        pass_mask = frequencies <= specs["freq_pass"]
        pass_values = magnitude_db[pass_mask]
        passband_ripple = (
            float(np.max(pass_values) - np.min(pass_values)) if pass_values.size else 0.0
        )
        analysis_stop_hz = min(
            specs["freq_sample"] / 2.0,
            max(specs["freq_pass"] * 4.0, specs["freq_sample"] * 0.10),
        )
        stop_mask = frequencies >= analysis_stop_hz
        stop_values = magnitude_db[stop_mask]
        stopband_attenuation = (
            float(max(0.0, -np.max(stop_values))) if stop_values.size else 0.0
        )

        combined_denominator = np.convolve(denominators[0], denominators[1])
        combined_numerator = (
            np.convolve(b_quantized[0], denominators[1])
            + np.convolve(b_quantized[1], denominators[0])
        )
        poles = np.roots(combined_denominator)
        zeros = np.roots(combined_numerator)
        max_pole_radius = float(np.max(np.abs(poles))) if poles.size else 0.0
        stable = bool(max_pole_radius < 1.0)

        # Follow the slowest implemented pole until its envelope has decayed
        # by 80 dB. Keep interactive previews bounded for marginal designs.
        impulse_target_ratio = 1e-4
        if 0.0 < max_pole_radius < 1.0:
            settling_samples = math.ceil(
                math.log(impulse_target_ratio) / math.log(max_pole_radius)
            )
            impulse_length = min(8192, max(96, settling_samples + 1))
            impulse_truncated = settling_samples + 1 > impulse_length
        else:
            impulse_length = 8192 if max_pole_radius >= 1.0 else 96
            impulse_truncated = max_pole_radius >= 1.0
        impulse_input = np.zeros(impulse_length, dtype=float)
        impulse_input[0] = 1.0
        impulse_response = (
            scipy_signal.lfilter(b_quantized[0], denominators[0], impulse_input)
            + scipy_signal.lfilter(b_quantized[1], denominators[1], impulse_input)
        )

        cutoff_indices = np.flatnonzero(magnitude_db <= -3.0)
        measured_cutoff = (
            float(frequencies[cutoff_indices[0]])
            if cutoff_indices.size
            else specs["freq_sample"] / 2.0
        )
        group_delay = -np.gradient(phase_radians, angular)
        group_mask = frequencies <= max(specs["freq_pass"] * 0.5, frequencies[1])
        mean_group_delay_samples = float(np.median(group_delay[group_mask]))

        return {
            **specs,
            "order": 4,
            "section_count": 2,
            "branch_b": tuple(tuple(float(value) for value in branch) for branch in branch_b),
            "feedback_a": tuple(tuple(float(value) for value in branch) for branch in feedback_a),
            "coefficient_words_b": tuple(tuple(int(value) for value in branch) for branch in b_words),
            "coefficient_words_a": tuple(tuple(int(value) for value in branch) for branch in a_words),
            "quantized_branch_b": tuple(tuple(float(value) for value in branch) for branch in b_quantized),
            "quantized_feedback_a": tuple(tuple(float(value) for value in branch) for branch in a_quantized),
            "frequencies_hz": tuple(float(value) for value in frequencies),
            "magnitude_db": tuple(float(value) for value in magnitude_db),
            "phase_degrees": tuple(float(value) for value in phase_degrees),
            "plot_frequencies_hz": tuple(float(value) for value in plot_frequencies),
            "plot_magnitude_db": tuple(float(value) for value in plot_magnitude_db),
            "plot_phase_degrees": tuple(float(value) for value in plot_phase_degrees),
            "plot_group_delay_seconds": tuple(
                float(value) for value in plot_group_delay_seconds
            ),
            "impulse_response": tuple(float(value) for value in impulse_response),
            "impulse_response_truncated": impulse_truncated,
            "impulse_response_target_db": -80.0,
            "zeros": tuple((float(value.real), float(value.imag)) for value in zeros),
            "poles": tuple((float(value.real), float(value.imag)) for value in poles),
            "stable": stable,
            "max_pole_radius": max_pole_radius,
            "stability_margin": 1.0 - max_pole_radius,
            "passband_ripple_db": passband_ripple,
            "stopband_attenuation_db": stopband_attenuation,
            "analysis_stop_hz": analysis_stop_hz,
            "measured_cutoff_hz": measured_cutoff,
            "group_delay_seconds": mean_group_delay_samples / specs["freq_sample"],
        }


class IIRResponseCanvas(FIRResponseCanvas):
    """Scientific response canvas for the implemented parallel IIR topology."""

    def __init__(self, parent=None, compact=True):
        super().__init__(parent=parent, compact=compact)
        self.setObjectName("iir_response_canvas")
        self.setAccessibleName("IIR 响应分析图")

    def set_view_mode(self, view_mode):
        if view_mode not in self.VIEW_LABELS:
            raise ValueError(f"Unknown IIR view mode: {view_mode}")
        self._view_mode = view_mode
        self.update()

    def _draw_frame(self, painter, rect):
        painter.fillRect(rect, QColor("#F7F8FA"))
        painter.setPen(QPen(QColor("#C7CDD6"), 1))
        painter.drawRoundedRect(rect, 8, 8)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(8)
        painter.setFont(title_font)
        painter.setPen(QColor("#243447"))
        painter.drawText(
            QRectF(rect.left() + 12, rect.top() + 7, rect.width() - 24, 16),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"IIR · {self.VIEW_LABELS[self._view_mode]}",
        )
        painter.setPen(QColor("#7B8492"))
        painter.drawText(
            QRectF(rect.right() - 180, rect.top() + 7, 168, 16),
            Qt.AlignRight | Qt.AlignVCenter,
            "PARALLEL SOS · FPGA PREVIEW",
        )

    def _draw_magnitude(self, painter, plot_rect, result):
        frequencies, axis_low, nyquist = self._frequency_axis(result)
        pass_x = self._map_log(
            result["freq_pass"], axis_low, nyquist, plot_rect.left(), plot_rect.right()
        )
        stop_x = self._map_log(
            result["analysis_stop_hz"], axis_low, nyquist, plot_rect.left(), plot_rect.right()
        )
        painter.fillRect(
            QRectF(plot_rect.left(), plot_rect.top(), pass_x - plot_rect.left(), plot_rect.height()),
            QColor("#DFF3EC"),
        )
        painter.fillRect(
            QRectF(
                pass_x,
                plot_rect.top(),
                max(0.0, stop_x - pass_x),
                plot_rect.height(),
            ),
            QColor("#FFF1D8"),
        )
        painter.fillRect(
            QRectF(
                stop_x,
                plot_rect.top(),
                max(0.0, plot_rect.right() - stop_x),
                plot_rect.height(),
            ),
            QColor("#F3E4E9"),
        )
        self._draw_grid(
            painter,
            plot_rect,
            self._log_frequency_labels(axis_low, nyquist),
            [(fraction, f"{-100 + fraction * 105:.0f}") for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)],
        )
        for frequency, label, color in (
            (result["freq_pass"], "FC", QColor("#1F8F75")),
            (result["analysis_stop_hz"], "STOP", QColor("#A4003B")),
        ):
            x = self._map_log(frequency, axis_low, nyquist, plot_rect.left(), plot_rect.right())
            painter.setPen(QPen(color, 1, Qt.DashLine))
            painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))
            painter.setPen(color)
            painter.drawText(QRectF(x - 20, plot_rect.top() + 3, 40, 12), Qt.AlignCenter, label)

        path = QPainterPath()
        magnitudes = result.get("plot_magnitude_db", result["magnitude_db"])
        for index, (frequency, magnitude) in enumerate(zip(frequencies, magnitudes)):
            clipped = max(-100.0, min(5.0, magnitude))
            point = QPointF(
                self._map_log(frequency, axis_low, nyquist, plot_rect.left(), plot_rect.right()),
                self._map_linear(clipped, -100.0, 5.0, plot_rect.bottom(), plot_rect.top()),
            )
            path.moveTo(point) if index == 0 else path.lineTo(point)
        painter.setPen(QPen(QColor("#1769FF"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)
        painter.setPen(QColor("#6C7685"))
        painter.drawText(QRectF(plot_rect.left() - 40, plot_rect.top() - 15, 36, 12), Qt.AlignRight, "dB")

    def _draw_impulse(self, painter, plot_rect, result):
        samples = result["impulse_response"]
        peak = max(1e-9, max(abs(value) for value in samples))
        y_limit = peak * 1.12
        self._draw_grid(
            painter,
            plot_rect,
            [(fraction, str(round((len(samples) - 1) * fraction))) for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)],
            [(fraction, f"{-y_limit + fraction * 2.0 * y_limit:.2f}") for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)],
        )
        zero_y = self._map_linear(0.0, -y_limit, y_limit, plot_rect.bottom(), plot_rect.top())
        painter.setPen(QPen(QColor("#A4003B"), 1))
        painter.setBrush(QColor("#A4003B"))
        for index, value in enumerate(samples):
            x = self._map_linear(index, 0, max(1, len(samples) - 1), plot_rect.left(), plot_rect.right())
            y = self._map_linear(value, -y_limit, y_limit, plot_rect.bottom(), plot_rect.top())
            painter.drawLine(QPointF(x, zero_y), QPointF(x, y))
            painter.drawEllipse(QPointF(x, y), 1.5, 1.5)
        if result.get("impulse_response_truncated"):
            painter.setPen(QColor("#A4003B"))
            painter.drawText(
                QRectF(plot_rect.right() - 150, plot_rect.top() + 4, 144, 14),
                Qt.AlignRight | Qt.AlignVCenter,
                f"尾部超过 {len(samples)} 点，已截断",
            )

    def _draw_zplane(self, painter, plot_rect, result):
        side = min(plot_rect.width(), plot_rect.height())
        square = QRectF(
            plot_rect.center().x() - side / 2.0,
            plot_rect.center().y() - side / 2.0,
            side,
            side,
        )
        painter.fillRect(plot_rect, QColor("#FFFFFF"))
        painter.setPen(QPen(QColor("#D7DCE4"), 1))
        painter.drawRect(plot_rect)
        center = square.center()
        radius = side * 0.39
        painter.setPen(QPen(QColor("#AEB6C1"), 1, Qt.DashLine))
        painter.drawEllipse(center, radius, radius)
        painter.drawLine(QPointF(center.x() - radius * 1.18, center.y()), QPointF(center.x() + radius * 1.18, center.y()))
        painter.drawLine(QPointF(center.x(), center.y() - radius * 1.18), QPointF(center.x(), center.y() + radius * 1.18))
        painter.setPen(QPen(QColor("#1769FF"), 1.5))
        for real, imaginary in result["zeros"]:
            x = center.x() + max(-1.2, min(1.2, real)) * radius
            y = center.y() - max(-1.2, min(1.2, imaginary)) * radius
            painter.drawEllipse(QPointF(x, y), 3.2, 3.2)
        painter.setPen(QPen(QColor("#A4003B"), 1.8))
        for real, imaginary in result["poles"]:
            x = center.x() + max(-1.2, min(1.2, real)) * radius
            y = center.y() - max(-1.2, min(1.2, imaginary)) * radius
            painter.drawLine(QPointF(x - 3.2, y - 3.2), QPointF(x + 3.2, y + 3.2))
            painter.drawLine(QPointF(x - 3.2, y + 3.2), QPointF(x + 3.2, y - 3.2))
        painter.setPen(QColor("#6C7685"))
        painter.drawText(QRectF(square.right() - 18, center.y() + 3, 30, 13), Qt.AlignLeft, "Re")
        painter.drawText(QRectF(center.x() + 4, square.top() - 2, 30, 13), Qt.AlignLeft, "Im")
        painter.setPen(QColor("#1769FF"))
        painter.drawText(QRectF(plot_rect.left() + 8, plot_rect.bottom() - 18, 90, 13), Qt.AlignLeft, "○ 零点")
        painter.setPen(QColor("#A4003B"))
        painter.drawText(QRectF(plot_rect.left() + 65, plot_rect.bottom() - 18, 90, 13), Qt.AlignLeft, "× 极点")


class IIRDesignerWidget(QWidget):
    """Live FPGA IIR workbench using the existing low-pass write contract."""

    def __init__(self, parent=None, apply_callback=None, initial_values=None, compact=True, allow_expand=True):
        super().__init__(parent)
        self.setObjectName("iir_designer_widget")
        self.setAccessibleName("IIR 可视化设计器")
        self._apply_callback = apply_callback
        self._initial_values = dict(initial_values or {})
        self._result = None
        self._expanded_window = None
        initial_specs = self._initial_values.get("design_lowpass", IIRDesignModel.DEFAULT_SPECS)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(9)

        header = QHBoxLayout()
        header.setSpacing(7)
        title = QLabel("IIR FILTER DESIGNER")
        title.setObjectName("iir_designer_title")
        method_chip = QLabel("PARALLEL SOS ×2 · Q3.24/Q2.25")
        method_chip.setObjectName("iir_method_chip")
        header.addWidget(title)
        header.addWidget(method_chip)
        header.addStretch()
        if allow_expand:
            expand_button = QToolButton(self)
            expand_button.setObjectName("iir_designer_expand_button")
            expand_button.setAccessibleName("在独立窗口中打开 IIR 设计器")
            expand_button.setToolTip("在独立窗口中打开 IIR 设计工作台")
            expand_button.setText("↗")
            expand_button.setCursor(Qt.PointingHandCursor)
            expand_button.clicked.connect(self.open_expanded_window)
            header.addWidget(expand_button)
        root.addLayout(header)

        specification_panel = QWidget(self)
        specification_panel.setObjectName("iir_specification_panel")
        spec_layout = QGridLayout(specification_panel)
        spec_layout.setContentsMargins(0, 0, 0, 0)
        spec_layout.setHorizontalSpacing(8)
        spec_layout.setVerticalSpacing(6)

        response_combo = QComboBox()
        response_combo.setObjectName("iir_response_type_combo")
        response_combo.setAccessibleName("IIR 响应类型")
        response_combo.addItem("低通 / Low-pass", "lowpass")
        spec_layout.addWidget(QLabel("响应类型"), 0, 0)
        spec_layout.addWidget(response_combo, 0, 1)

        self._filter_type_combo = QComboBox()
        self._filter_type_combo.setObjectName("iir_filter_type_combo")
        self._filter_type_combo.setAccessibleName("IIR 滤波器族")
        for key, label in IIRDesignModel.FILTER_LABELS.items():
            self._filter_type_combo.addItem(label, key)
        family_index = self._filter_type_combo.findData(str(initial_specs.get("filter_type", "butter")))
        self._filter_type_combo.setCurrentIndex(max(0, family_index))
        spec_layout.addWidget(QLabel("滤波器族"), 1, 0)
        spec_layout.addWidget(self._filter_type_combo, 1, 1)

        order_value = QLabel("4th order · 2 parallel sections")
        order_value.setObjectName("iir_order_value")
        order_value.setAccessibleName("IIR 固定阶数")
        order_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        spec_layout.addWidget(QLabel("FPGA 结构"), 2, 0)
        spec_layout.addWidget(order_value, 2, 1)

        field_specs = (
            ("freq_sample", "采样频率", 1.0, 1e12, "Hz"),
            ("freq_pass", "截止频率 FC", 0.0, 1e12, "Hz"),
        )
        self._editors = {}
        for row, (key, label, minimum, maximum, unit) in enumerate(field_specs, start=3):
            field = {
                "key": key,
                "label": label,
                "type": "float",
                "min": minimum,
                "max": maximum,
                "unit": unit,
            }
            editor = QuantityLineEdit(value=float(initial_specs.get(key, IIRDesignModel.DEFAULT_SPECS[key])), field=field)
            editor.setObjectName(f"iir_{key}_edit")
            editor.setAccessibleName(label)
            self._editors[key] = editor
            spec_layout.addWidget(QLabel(label), row, 0)
            spec_layout.addWidget(editor, row, 1)

        analysis_panel = QWidget(self)
        analysis_layout = QVBoxLayout(analysis_panel)
        analysis_layout.setContentsMargins(0, 0, 0, 0)
        analysis_layout.setSpacing(7)
        view_row = QHBoxLayout()
        view_label = QLabel("ANALYSIS")
        view_label.setObjectName("iir_analysis_label")
        self._stability_badge = QLabel("CHECKING")
        self._stability_badge.setObjectName("iir_stability_badge")
        self._view_combo = QComboBox()
        self._view_combo.setObjectName("iir_analysis_view_combo")
        self._view_combo.setAccessibleName("IIR 分析视图")
        for key, label in IIRResponseCanvas.VIEW_LABELS.items():
            self._view_combo.addItem(label, key)
        view_row.addWidget(view_label)
        view_row.addWidget(self._stability_badge)
        view_row.addStretch()
        view_row.addWidget(self._view_combo)
        analysis_layout.addLayout(view_row)

        self._canvas = IIRResponseCanvas(self, compact=compact)
        analysis_layout.addWidget(self._canvas, 1)
        self._metrics_label = QLabel("—")
        self._metrics_label.setObjectName("iir_metric_summary")
        self._metrics_label.setWordWrap(True)
        analysis_layout.addWidget(self._metrics_label)

        if compact:
            root.addWidget(specification_panel)
            root.addWidget(analysis_panel)
        else:
            body = QHBoxLayout()
            body.setSpacing(14)
            specification_panel.setFixedWidth(330)
            specification_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
            body.addWidget(specification_panel, 0, Qt.AlignTop)
            body.addWidget(analysis_panel, 1)
            root.addLayout(body, 1)

        footer = QHBoxLayout()
        self._status_label = QLabel("正在计算…")
        self._status_label.setObjectName("iir_design_status")
        self._status_label.setWordWrap(True)
        self._apply_btn = QPushButton("应用到 IIR")
        self._apply_btn.setObjectName("iir_design_apply_button")
        self._apply_btn.setAccessibleName("应用 IIR 设计")
        self._apply_btn.setProperty("variant", "primary")
        footer.addWidget(self._status_label, 1)
        footer.addWidget(self._apply_btn, 0)
        root.addLayout(footer)

        self.setStyleSheet(
            "#iir_designer_title { color: #243447; font-weight: 700; letter-spacing: 1px; }"
            "#iir_method_chip { color: #8F123D; background: #F5E6EB; border: 1px solid #E5C7D2; "
            "border-radius: 8px; padding: 2px 7px; font-size: 9px; }"
            "#iir_order_value { color: #586273; background: #F1F3F6; border: 1px solid #DDE1E7; "
            "border-radius: 5px; padding: 5px 7px; font-size: 10px; }"
            "#iir_analysis_label { color: #6C7685; font-size: 10px; font-weight: 700; letter-spacing: 1px; }"
            "#iir_stability_badge { border-radius: 7px; padding: 2px 7px; font-size: 9px; font-weight: 700; }"
            "#iir_metric_summary { color: #586273; background: #F1F3F6; border-radius: 5px; "
            "padding: 6px; font-size: 10px; }"
            "#iir_design_status { color: #667180; font-size: 10px; }"
            "#iir_designer_expand_button { color: #243447; background: #FFFFFF; border: 1px solid #C7CDD6; "
            "border-radius: 5px; font-size: 15px; font-weight: 600; min-width: 26px; min-height: 26px; }"
            "#iir_designer_expand_button:hover { color: #9B0036; border-color: #9B0036; background: #FFF5F8; }"
        )

        for editor in self._editors.values():
            editor.textChanged.connect(self._refresh_preview)
        self._filter_type_combo.currentIndexChanged.connect(self._refresh_preview)
        self._view_combo.currentIndexChanged.connect(self._change_view)
        self._apply_btn.clicked.connect(self._apply_design)
        self._refresh_preview()

    def _collect_specs(self):
        specs = {"filter_type": str(self._filter_type_combo.currentData())}
        for key, editor in self._editors.items():
            value = editor.preview_quantity_value()
            if value is None:
                raise ValueError(f"{editor.accessibleName()}输入无效")
            specs[key] = float(value)
        return IIRDesignModel.validate(specs)

    def specifications(self):
        try:
            return self._collect_specs()
        except ValueError:
            return dict(IIRDesignModel.DEFAULT_SPECS)

    def design_result(self):
        return dict(self._result) if self._result is not None else None

    def set_specifications(self, specifications):
        specs = IIRDesignModel.normalized_specs(specifications)
        for key, editor in self._editors.items():
            editor.blockSignals(True)
            editor.set_quantity_value(specs[key])
            editor.blockSignals(False)
        self._filter_type_combo.blockSignals(True)
        index = self._filter_type_combo.findData(specs["filter_type"])
        if index >= 0:
            self._filter_type_combo.setCurrentIndex(index)
        self._filter_type_combo.blockSignals(False)
        self._refresh_preview()

    def _refresh_preview(self, *_):
        try:
            self._result = IIRDesignModel.design(self._collect_specs())
            self._canvas.set_design_result(self._result)
            self._metrics_label.setText(
                f"最大极点半径  {self._result['max_pole_radius']:.6f}   ·   "
                f"稳定裕量  {self._result['stability_margin']:.6f}\n"
                f"通带变化  {self._result['passband_ripple_db']:.2f} dB   ·   "
                f"高频抑制  {self._result['stopband_attenuation_db']:.1f} dB   ·   "
                f"群时延  {self._result['group_delay_seconds'] * 1e9:.1f} ns"
            )
            if self._result["stable"]:
                self._stability_badge.setText("STABLE")
                self._stability_badge.setStyleSheet("color: #1F7A64; background: #DFF3EC;")
                self._status_label.setText("量化系数稳定 · FPGA 预览已同步")
                self._status_label.setStyleSheet("color: #1F7A64;")
                self._apply_btn.setEnabled(True)
            else:
                self._stability_badge.setText("UNSTABLE")
                self._stability_badge.setStyleSheet("color: #A4003B; background: #F5E6EB;")
                self._status_label.setText("量化后极点越过单位圆，禁止写入 FPGA")
                self._status_label.setStyleSheet("color: #A4003B;")
                self._apply_btn.setEnabled(False)
        except Exception as exc:
            self._result = None
            self._canvas.set_design_result(None)
            self._metrics_label.setText("等待有效设计规格")
            self._stability_badge.setText("INVALID")
            self._stability_badge.setStyleSheet("color: #A4003B; background: #F5E6EB;")
            self._status_label.setText(str(exc))
            self._status_label.setStyleSheet("color: #A4003B;")
            self._apply_btn.setEnabled(False)

    def _change_view(self, *_):
        self._canvas.set_view_mode(self._view_combo.currentData())

    def _apply_design(self):
        if self._apply_callback is None:
            return
        try:
            specs = self._collect_specs()
            result = IIRDesignModel.design(specs)
            if not result["stable"]:
                raise ValueError("量化后滤波器不稳定")
            self._apply_callback("design_lowpass", specs)
            self._initial_values["design_lowpass"] = dict(specs)
            self._status_label.setText("设计已提交到现有 IIR 硬件写入链路")
            self._status_label.setStyleSheet("color: #1F7A64;")
        except Exception as exc:
            self._status_label.setText(f"应用失败：{exc}")
            self._status_label.setStyleSheet("color: #A4003B;")

    def open_expanded_window(self):
        workspace_key = f"iir-designer:{id(self)}"
        workspace_title = self.property("workspaceTitle") or "IIR 滤波器设计"
        if self._expanded_window is not None:
            try:
                if _dispatch_workspace_open(
                    self,
                    workspace_key,
                    workspace_title,
                    self._expanded_window,
                ):
                    return self._expanded_window
                if self._expanded_window.isVisible():
                    self._expanded_window.raise_()
                    self._expanded_window.activateWindow()
                    return self._expanded_window
            except RuntimeError:
                self._expanded_window = None
        self._expanded_window = IIRDesignerWindow(
            self.specifications(),
            apply_callback=self._apply_from_expanded_window,
            parent=self.window(),
        )
        self._expanded_window.destroyed.connect(self._clear_expanded_window)
        if _dispatch_workspace_open(
            self,
            workspace_key,
            workspace_title,
            self._expanded_window,
        ):
            return self._expanded_window
        self._expanded_window.show()
        self._expanded_window.raise_()
        self._expanded_window.activateWindow()
        return self._expanded_window

    def _apply_from_expanded_window(self, method_name, specs):
        if self._apply_callback is not None:
            self._apply_callback(method_name, specs)
        self.set_specifications(specs)

    def _clear_expanded_window(self, *_):
        self._expanded_window = None


class IIRDesignerWindow(QDialog):
    def __init__(self, specifications=None, apply_callback=None, parent=None):
        super().__init__(parent)
        self.setObjectName("iir_designer_window")
        self.setAccessibleName("IIR 可视化设计独立窗口")
        self.setWindowTitle("IIR Filter Designer · FPGA 工作台")
        self.setModal(False)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setMinimumSize(900, 580)
        self.resize(1120, 720)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        initial = {"design_lowpass": dict(specifications or IIRDesignModel.DEFAULT_SPECS)}
        self._designer = IIRDesignerWidget(
            self,
            apply_callback=apply_callback,
            initial_values=initial,
            compact=False,
            allow_expand=False,
        )
        layout.addWidget(self._designer)
