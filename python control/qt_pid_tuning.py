"""PID response visualization and manual tuning controls."""

import math
from dataclasses import dataclass

from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QSlider,
    QToolButton, QVBoxLayout, QWidget,
)

__all__ = [
    "PIDParamCanvas",
    "PIDSliderSpec",
    "PIDManualTuningPanel",
    "PIDResponseWindow",
]


class PIDParamCanvas(QWidget):
    """Live Bode magnitude preview using the same scaling as ``ModulePID``."""

    parameter_changed = Signal(str, float)
    _DIRECT_KEYS = {"gain_p", "gain_i", "gain_d", "leak_digit"}
    _MAX_PLOT_FREQUENCY_HZ = 125_000_000.0
    _FREQUENCY_DRAG_KEYS = (
        "saturation_turning_frequency",
        "pi_corner",
        "pd_corner",
    )

    def __init__(self, parent=None, allow_expand=True, compact=True):
        super().__init__(parent)
        self._parameters = {}
        self._changed_key = None
        self._expanded_window = None
        self._plot_metrics = None
        self._handle_positions = {}
        self._hover_key = None
        self._drag_key = None
        self._drag_transform = None
        self._drag_origin_position = None
        self._drag_origin_value = None
        self._last_drag_value = None
        self._response = self.calculate_response({}, self._logspace(1.0, 100_000_000.0, 180))
        if compact:
            self.setMinimumSize(340, 205)
            self.setFixedHeight(220)
        else:
            self.setMinimumSize(600, 360)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setAccessibleName("PID 实时频率响应，可拖动 P、PI、PD 和泄漏标记调参")
        self.setToolTip("拖动 P 基准线调节整体增益；横向拖动 PI、PD、泄漏标记调节对应频率")

        self._expand_button = None
        if allow_expand:
            self._expand_button = QToolButton(self)
            self._expand_button.setObjectName("pid_response_expand_button")
            self._expand_button.setAccessibleName("放大 PID 实时曲线")
            self._expand_button.setToolTip("在独立窗口中查看实时曲线")
            self._expand_button.setText("↗")
            self._expand_button.setCursor(Qt.PointingHandCursor)
            self._expand_button.setFixedSize(26, 26)
            self._expand_button.setStyleSheet(
                "QToolButton { color: #243447; background: #FFFFFF; border: 1px solid #C7CDD6; "
                "border-radius: 5px; font-size: 15px; font-weight: 600; padding: 0; }"
                "QToolButton:hover { color: #9B0036; border-color: #9B0036; background: #FFF5F8; }"
                "QToolButton:pressed { background: #F3DDE5; }"
            )
            self._expand_button.clicked.connect(self.open_expanded_window)
            self._position_expand_button()

    def _position_expand_button(self):
        if self._expand_button is not None:
            self._expand_button.move(max(0, self.width() - self._expand_button.width() - 9), 6)
            self._expand_button.raise_()

    def resizeEvent(self, event):
        self._position_expand_button()
        super().resizeEvent(event)

    def open_expanded_window(self):
        if self._expanded_window is not None:
            try:
                if self._expanded_window.isVisible():
                    self._expanded_window.raise_()
                    self._expanded_window.activateWindow()
                    return self._expanded_window
            except RuntimeError:
                self._expanded_window = None

        window = PIDResponseWindow(
            self._parameters,
            changed_key=self._changed_key,
            parent=self.window(),
        )
        window._canvas.parameter_changed.connect(self.parameter_changed.emit)
        window.destroyed.connect(self._clear_expanded_window)
        self._expanded_window = window
        window.show()
        window.raise_()
        window.activateWindow()
        return window

    def _clear_expanded_window(self, *_):
        self._expanded_window = None

    @staticmethod
    def _finite_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError, OverflowError):
            return float(default)

    @staticmethod
    def _signed(value, fallback=1.0):
        number = PIDParamCanvas._finite_float(value, 0.0)
        if number > 0:
            return 1.0
        if number < 0:
            return -1.0
        return float(fallback)

    @staticmethod
    def _amplitude_to_db(amplitude):
        try:
            magnitude = abs(float(amplitude))
        except (TypeError, ValueError, OverflowError):
            return None
        if magnitude <= 0.0:
            return None
        if math.isinf(magnitude):
            return float("inf")
        return 20.0 * math.log10(magnitude)

    @staticmethod
    def _db_to_amplitude(gain_db):
        gain_db = PIDParamCanvas._finite_float(gain_db, -160.0)
        if math.isnan(gain_db):
            return 0.0
        if gain_db == float("-inf"):
            return 0.0
        if gain_db == float("inf"):
            return 1e30
        return 10.0 ** (max(-600.0, min(600.0, gain_db)) / 20.0)

    @staticmethod
    def _logspace(low, high, count):
        low = max(float(low), 1e-12)
        high = max(float(high), low * 1.0001)
        if count <= 1:
            return (low,)
        start = math.log10(low)
        step = (math.log10(high) - start) / (count - 1)
        return tuple(10.0 ** (start + step * index) for index in range(count))

    @classmethod
    def _channel_model(cls, parameters, changed_key=None):
        parameters = parameters if isinstance(parameters, dict) else {}
        has_indirect = any(
            key in parameters
            for key in ("overall_gain", "pi_corner", "pd_corner", "saturation_turning_frequency")
        )
        has_direct_channels = all(key in parameters for key in ("gain_p", "gain_i", "gain_d"))
        has_nonfinite_indirect = any(
            not math.isfinite(cls._finite_float(parameters.get(key), 0.0))
            for key in ("overall_gain", "pi_corner", "pd_corner", "saturation_gain")
            if key in parameters
        )
        use_direct = (
            changed_key in cls._DIRECT_KEYS
            or not has_indirect
            or (changed_key is None and has_direct_channels and has_nonfinite_indirect)
        )

        if use_direct:
            gain_p = cls._finite_float(parameters.get("gain_p"), 0.0)
            gain_i = cls._finite_float(parameters.get("gain_i"), 0.0)
            gain_d = cls._finite_float(parameters.get("gain_d"), 0.0)
            p_amplitude = gain_p / (2.0**16)
            i_numerator = gain_i * 125_000_000.0 / (2.0 * math.pi * (2.0**32))
            d_slope = gain_d * 2.0 * math.pi / (250_000_000.0 * (2.0**16))

            if "leak_digit" in parameters:
                leak_digit = cls._finite_float(parameters.get("leak_digit"), 0.0)
                leak_frequency = (
                    125_000_000.0 / (leak_digit * 256.0 * 2.0 * math.pi)
                    if leak_digit > 0.0
                    else 0.0
                )
            else:
                leak_frequency = max(
                    0.0,
                    cls._finite_float(parameters.get("saturation_turning_frequency"), 0.0),
                )
        else:
            overall_gain = cls._finite_float(parameters.get("overall_gain"), -160.0)
            p_magnitude = cls._db_to_amplitude(overall_gain)
            p_sign = cls._signed(parameters.get("gain_p"), 1.0)
            i_sign = cls._signed(parameters.get("gain_i"), p_sign)
            d_sign = cls._signed(parameters.get("gain_d"), p_sign)
            pi_corner = max(0.0, cls._finite_float(parameters.get("pi_corner"), 0.0))
            pd_corner = cls._finite_float(parameters.get("pd_corner"), float("inf"))

            p_amplitude = p_sign * p_magnitude
            i_numerator = i_sign * p_magnitude * pi_corner
            d_slope = d_sign * p_magnitude / pd_corner if pd_corner > 0.0 and math.isfinite(pd_corner) else 0.0

            if changed_key == "saturation_gain" and pi_corner > 0.0:
                saturation_gain = cls._finite_float(parameters.get("saturation_gain"), float("inf"))
                if math.isfinite(saturation_gain):
                    leak_frequency = pi_corner * cls._db_to_amplitude(overall_gain - saturation_gain)
                else:
                    leak_frequency = 0.0
            else:
                leak_frequency = max(
                    0.0,
                    cls._finite_float(parameters.get("saturation_turning_frequency"), 0.0),
                )

        p_magnitude = abs(p_amplitude)
        pi_corner = abs(i_numerator / p_amplitude) if p_amplitude != 0.0 else None
        pd_corner = abs(p_amplitude / d_slope) if d_slope != 0.0 else None
        saturation_gain = (
            cls._amplitude_to_db(abs(i_numerator) / leak_frequency)
            if leak_frequency > 0.0 and i_numerator != 0.0
            else None
        )
        return {
            "source": "direct" if use_direct else "indirect",
            "p_amplitude": p_amplitude,
            "i_numerator": i_numerator,
            "d_slope": d_slope,
            "overall_gain_db": cls._amplitude_to_db(p_magnitude),
            "pi_corner_hz": pi_corner,
            "pd_corner_hz": pd_corner,
            "leak_frequency_hz": leak_frequency,
            "saturation_gain_db": saturation_gain,
        }

    @classmethod
    def calculate_response(cls, parameters, frequencies_hz, changed_key=None):
        """Return P/I/D and combined magnitude responses in dB.

        The equations mirror ``ModulePID``: P is Q16, I runs at 125 MHz
        with a leaky pole, and D uses the 250 MHz sample difference scaling.
        """
        model = cls._channel_model(parameters, changed_key=changed_key)
        frequencies = tuple(float(frequency) for frequency in frequencies_hz)
        proportional_db = []
        integral_db = []
        derivative_db = []
        total_db = []

        p_amplitude = model["p_amplitude"]
        i_numerator = model["i_numerator"]
        d_slope = model["d_slope"]
        leak_frequency = model["leak_frequency_hz"]

        for frequency in frequencies:
            if frequency <= 0.0 or not math.isfinite(frequency):
                proportional_db.append(None)
                integral_db.append(None)
                derivative_db.append(None)
                total_db.append(None)
                continue

            p_channel = complex(p_amplitude, 0.0)
            i_channel = (
                i_numerator / complex(leak_frequency, frequency)
                if i_numerator != 0.0
                else 0j
            )
            d_channel = complex(0.0, d_slope * frequency)
            combined = p_channel + i_channel + d_channel

            proportional_db.append(cls._amplitude_to_db(abs(p_channel)))
            integral_db.append(cls._amplitude_to_db(abs(i_channel)))
            derivative_db.append(cls._amplitude_to_db(abs(d_channel)))
            total_db.append(cls._amplitude_to_db(abs(combined)))

        return {
            "frequencies_hz": frequencies,
            "proportional_db": tuple(proportional_db),
            "integral_db": tuple(integral_db),
            "derivative_db": tuple(derivative_db),
            "total_db": tuple(total_db),
            "overall_gain_db": model["overall_gain_db"],
            "pi_corner_hz": model["pi_corner_hz"],
            "pd_corner_hz": model["pd_corner_hz"],
            "leak_frequency_hz": model["leak_frequency_hz"],
            "saturation_gain_db": model["saturation_gain_db"],
            "source": model["source"],
        }

    @classmethod
    def _frequency_range(cls, parameters, changed_key=None):
        model = cls._channel_model(parameters, changed_key=changed_key)
        markers = [
            marker
            for marker in (
                model["leak_frequency_hz"],
                model["pi_corner_hz"],
                model["pd_corner_hz"],
            )
            if marker is not None and marker > 0.0 and math.isfinite(marker)
        ]
        if not markers:
            return 1.0, 100_000_000.0

        low = max(1e-3, min(markers) / 100.0)
        high = min(cls._MAX_PLOT_FREQUENCY_HZ, max(markers) * 100.0)
        if high <= low:
            high = min(cls._MAX_PLOT_FREQUENCY_HZ, low * 10_000.0)
        if high / low < 10_000.0:
            expansion = math.sqrt(10_000.0 / (high / low))
            low = max(1e-3, low / expansion)
            high = min(cls._MAX_PLOT_FREQUENCY_HZ, high * expansion)
        return low, max(high, low * 10.0)

    def set_parameters(self, parameters, changed_key=None):
        self._parameters = dict(parameters or {})
        self._changed_key = changed_key
        if self._drag_key and self._response.get("frequencies_hz"):
            frequencies = self._response["frequencies_hz"]
        else:
            low, high = self._frequency_range(self._parameters, changed_key=changed_key)
            frequencies = self._logspace(low, high, 200)
        self._response = self.calculate_response(
            self._parameters,
            frequencies,
            changed_key=changed_key,
        )
        self.update()
        if self._expanded_window is not None:
            try:
                self._expanded_window.set_parameters(self._parameters, changed_key=changed_key)
            except RuntimeError:
                self._expanded_window = None

    def interactive_handle_positions(self):
        """Return the currently rendered graph handles for UI automation."""
        return {
            key: QPointF(position)
            for key, position in self._handle_positions.items()
        }

    def _hit_test_drag_target(self, position):
        metrics = self._plot_metrics
        if not metrics:
            return None
        plot_rect = metrics["plot_rect"]
        if not plot_rect.adjusted(-12, -12, 12, 12).contains(position):
            return None

        for key, handle in self._handle_positions.items():
            if abs(position.x() - handle.x()) <= 11 and abs(position.y() - handle.y()) <= 11:
                return key

        for key in self._FREQUENCY_DRAG_KEYS:
            handle = self._handle_positions.get(key)
            frequency = self._response.get(
                {
                    "saturation_turning_frequency": "leak_frequency_hz",
                    "pi_corner": "pi_corner_hz",
                    "pd_corner": "pd_corner_hz",
                }[key]
            )
            if (
                handle is not None
                and frequency is not None
                and frequency > 0.0
                and abs(position.x() - handle.x()) <= 9
                and plot_rect.top() <= position.y() <= plot_rect.bottom()
            ):
                return key

        gain_handle = self._handle_positions.get("overall_gain")
        if (
            gain_handle is not None
            and abs(position.y() - gain_handle.y()) <= 9
            and plot_rect.left() <= position.x() <= plot_rect.right()
        ):
            return "overall_gain"
        return None

    def _dragged_parameter_value(self, position):
        if not self._drag_key or not self._drag_transform:
            return None
        transform = self._drag_transform
        plot_rect = transform["plot_rect"]

        if self._drag_key == "overall_gain":
            pixels = self._drag_origin_position.y() - position.y()
            db_per_pixel = (
                (transform["y_max"] - transform["y_min"])
                / max(1.0, plot_rect.height())
            )
            value = self._drag_origin_value + pixels * db_per_pixel
            return round(max(-180.0, min(180.0, value)), 1)

        fraction = (position.x() - plot_rect.left()) / max(1.0, plot_rect.width())
        fraction = max(0.0, min(1.0, fraction))
        value = 10.0 ** (
            transform["log_low"] + fraction * transform["log_span"]
        )
        return float(f"{value:.7g}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            key = self._hit_test_drag_target(event.position())
            if key is not None:
                self._drag_key = key
                self._hover_key = key
                self._drag_transform = dict(self._plot_metrics)
                self._drag_transform["plot_rect"] = QRectF(self._plot_metrics["plot_rect"])
                self._drag_origin_position = QPointF(event.position())
                if key == "overall_gain":
                    value = self._parameters.get(
                        "overall_gain",
                        self._response.get("overall_gain_db", 0.0),
                    )
                    self._drag_origin_value = self._finite_float(value, 0.0)
                else:
                    self._drag_origin_value = None
                self._last_drag_value = None
                self.setCursor(Qt.ClosedHandCursor)
                self.update()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_key is not None:
            value = self._dragged_parameter_value(event.position())
            if value is not None and (
                self._last_drag_value is None
                or not math.isclose(value, self._last_drag_value, rel_tol=1e-9, abs_tol=1e-9)
            ):
                self._last_drag_value = value
                self.parameter_changed.emit(self._drag_key, value)
            event.accept()
            return

        hover_key = self._hit_test_drag_target(event.position())
        if hover_key != self._hover_key:
            self._hover_key = hover_key
            self.setCursor(Qt.OpenHandCursor if hover_key else Qt.ArrowCursor)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drag_key is not None:
            changed_key = self._drag_key
            self._drag_key = None
            self._drag_transform = None
            self._drag_origin_position = None
            self._drag_origin_value = None
            self._last_drag_value = None
            self.setCursor(Qt.OpenHandCursor)
            self.set_parameters(self._parameters, changed_key=changed_key)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        if self._drag_key is None and self._hover_key is not None:
            self._hover_key = None
            self.unsetCursor()
            self.update()
        super().leaveEvent(event)

    def response_data(self):
        return dict(self._response)

    @staticmethod
    def _format_frequency(value):
        if value == float("inf"):
            return "∞"
        if value == float("-inf"):
            return "−∞"
        if value is None or not math.isfinite(value):
            return "—"
        for scale, suffix in ((1e9, "GHz"), (1e6, "MHz"), (1e3, "kHz")):
            if abs(value) >= scale:
                return f"{value / scale:.3g}{suffix}"
        return f"{value:.3g}Hz"

    @staticmethod
    def _clamped_db(value):
        if value is None or math.isnan(value):
            return None
        if value == float("inf"):
            return 180.0
        if value == float("-inf"):
            return -180.0
        return max(-180.0, min(180.0, float(value)))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(1, 1, -1, -1)
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
            "PID 实时频率响应",
        )

        body_font = QFont()
        body_font.setPointSize(6)
        painter.setFont(body_font)
        painter.setPen(QColor("#7B8492"))
        painter.drawText(
            QRectF(rect.right() - 150, rect.top() + 7, 110, 16),
            Qt.AlignRight | Qt.AlignVCenter,
            "拖动标记 · LIVE",
        )

        plot_rect = QRectF(rect.left() + 45, rect.top() + 46, rect.width() - 60, rect.height() - 75)
        painter.fillRect(plot_rect, QColor("#FFFFFF"))
        painter.setPen(QPen(QColor("#D7DCE4"), 1))
        painter.drawRect(plot_rect)

        response = self._response
        frequencies = response.get("frequencies_hz", ())
        if not frequencies:
            painter.end()
            return

        all_values = [0.0]
        for name in ("proportional_db", "integral_db", "derivative_db", "total_db"):
            all_values.extend(
                value
                for value in (self._clamped_db(item) for item in response.get(name, ()))
                if value is not None
            )
        data_min = min(all_values)
        data_max = max(all_values)
        y_min = max(-180.0, math.floor((data_min - 8.0) / 20.0) * 20.0)
        y_max = min(180.0, math.ceil((data_max + 8.0) / 20.0) * 20.0)
        if y_max - y_min < 40.0:
            center = (y_max + y_min) / 2.0
            y_min = max(-180.0, center - 20.0)
            y_max = min(180.0, center + 20.0)
        if y_max <= y_min:
            y_min, y_max = -20.0, 20.0
        if self._drag_key is not None and self._drag_transform is not None:
            y_min = self._drag_transform["y_min"]
            y_max = self._drag_transform["y_max"]

        low_frequency = frequencies[0]
        high_frequency = frequencies[-1]
        log_low = math.log10(low_frequency)
        log_span = max(1e-9, math.log10(high_frequency) - log_low)
        self._plot_metrics = {
            "plot_rect": QRectF(plot_rect),
            "y_min": y_min,
            "y_max": y_max,
            "log_low": log_low,
            "log_span": log_span,
        }

        def map_x(frequency):
            return plot_rect.left() + (math.log10(frequency) - log_low) / log_span * plot_rect.width()

        def map_y(gain_db):
            gain_db = self._clamped_db(gain_db)
            if gain_db is None:
                return None
            return plot_rect.bottom() - (gain_db - y_min) / (y_max - y_min) * plot_rect.height()

        painter.setPen(QPen(QColor("#E6E9EE"), 1, Qt.DotLine))
        for index in range(5):
            fraction = index / 4.0
            y = plot_rect.bottom() - fraction * plot_rect.height()
            gain = y_min + fraction * (y_max - y_min)
            painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))
            painter.setPen(QColor("#6C7685"))
            painter.drawText(
                QRectF(rect.left() + 2, y - 6, 39, 12),
                Qt.AlignRight | Qt.AlignVCenter,
                f"{gain:.0f}",
            )
            painter.setPen(QPen(QColor("#E6E9EE"), 1, Qt.DotLine))

        first_decade = math.ceil(log_low)
        last_decade = math.floor(math.log10(high_frequency))
        for exponent in range(first_decade, last_decade + 1):
            frequency = 10.0**exponent
            x = map_x(frequency)
            painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))
            if last_decade - first_decade <= 7 or (exponent - first_decade) % 2 == 0:
                painter.setPen(QColor("#6C7685"))
                painter.drawText(
                    QRectF(x - 24, plot_rect.bottom() + 3, 48, 12),
                    Qt.AlignCenter | Qt.AlignVCenter,
                    self._format_frequency(frequency),
                )
                painter.setPen(QPen(QColor("#E6E9EE"), 1, Qt.DotLine))

        marker_specs = (
            ("saturation_turning_frequency", "leak_frequency_hz", "泄漏", QColor("#A670D6")),
            ("pi_corner", "pi_corner_hz", "PI", QColor("#E9953E")),
            ("pd_corner", "pd_corner_hz", "PD", QColor("#25A8A2")),
        )
        self._handle_positions = {}
        rendered_markers = []
        disabled_index = 0
        for parameter_key, response_key, label, color in marker_specs:
            frequency = response.get(response_key)
            visible = (
                frequency is not None
                and math.isfinite(frequency)
                and low_frequency <= frequency <= high_frequency
            )
            if visible:
                x = map_x(frequency)
                handle = QPointF(x, plot_rect.top() + 19)
                painter.setPen(QPen(
                    color,
                    2 if parameter_key in {self._hover_key, self._drag_key} else 1,
                    Qt.DashLine,
                ))
                painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))
                painter.setPen(color)
                painter.drawText(
                    QRectF(x - 18, plot_rect.top() + 2, 36, 11),
                    Qt.AlignCenter,
                    label,
                )
            else:
                handle = QPointF(
                    plot_rect.left() + 5,
                    plot_rect.top() + 17 + disabled_index * 17,
                )
                disabled_index += 1
                painter.setPen(color)
                state_text = "∞" if frequency is not None and math.isinf(frequency) else "关闭"
                painter.drawText(
                    QRectF(handle.x() + 8, handle.y() - 6, 46, 12),
                    Qt.AlignLeft | Qt.AlignVCenter,
                    f"{label} {state_text}",
                )
            self._handle_positions[parameter_key] = handle
            rendered_markers.append((parameter_key, color, handle))

        def draw_series(key, color, width, style=Qt.SolidLine):
            painter.setPen(QPen(color, width, style, Qt.RoundCap, Qt.RoundJoin))
            path = QPainterPath()
            active = False
            for frequency, gain_db in zip(frequencies, response.get(key, ())):
                y = map_y(gain_db)
                if y is None:
                    active = False
                    continue
                point = QPointF(map_x(frequency), y)
                if not active:
                    path.moveTo(point)
                    active = True
                else:
                    path.lineTo(point)
            painter.drawPath(path)

        draw_series("proportional_db", QColor("#7D8795"), 1, Qt.DashLine)
        draw_series("integral_db", QColor("#E9953E"), 1)
        draw_series("derivative_db", QColor("#25A8A2"), 1)
        draw_series("total_db", QColor("#1769FF"), 2)

        overall_gain = response.get("overall_gain_db")
        overall_gain_y = map_y(overall_gain if overall_gain is not None else 0.0)
        if overall_gain_y is not None:
            overall_gain_y = max(plot_rect.top(), min(plot_rect.bottom(), overall_gain_y))
            gain_handle = QPointF(plot_rect.left() + 13, overall_gain_y)
            self._handle_positions["overall_gain"] = gain_handle
            gain_active = "overall_gain" in {self._hover_key, self._drag_key}
            painter.setPen(QPen(QColor("#9B0036" if gain_active else "#7D8795"), 2))
            painter.setBrush(QColor("#FFF2F6" if gain_active else "#FFFFFF"))
            radius = 6 if gain_active else 4.5
            painter.drawEllipse(gain_handle, radius, radius)
            painter.drawText(
                QRectF(gain_handle.x() + 7, gain_handle.y() - 7, 22, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                "P",
            )

        for parameter_key, color, handle in rendered_markers:
            active = parameter_key in {self._hover_key, self._drag_key}
            painter.setPen(QPen(color, 2 if active else 1.5))
            painter.setBrush(QColor("#FFF2F6" if active else "#FFFFFF"))
            radius = 6 if active else 4.5
            painter.drawEllipse(handle, radius, radius)

        legend = (("总响应", "#1769FF"), ("P", "#7D8795"), ("I", "#E9953E"), ("D", "#25A8A2"))
        legend_x = rect.left() + 12
        for label, color in legend:
            painter.setPen(QPen(QColor(color), 2))
            painter.drawLine(QPointF(legend_x, rect.top() + 34), QPointF(legend_x + 12, rect.top() + 34))
            painter.setPen(QColor("#586273"))
            painter.drawText(QRectF(legend_x + 15, rect.top() + 27, 35, 14), Qt.AlignLeft | Qt.AlignVCenter, label)
            legend_x += 52

        painter.setPen(QColor("#7B8492"))
        painter.drawText(QRectF(rect.left() + 2, plot_rect.top() - 1, 38, 12), Qt.AlignRight, "dB")
        painter.drawText(
            QRectF(plot_rect.left(), rect.bottom() - 14, plot_rect.width(), 11),
            Qt.AlignCenter | Qt.AlignVCenter,
            "对数频率 (Hz)",
        )
        painter.end()


@dataclass(frozen=True)
class PIDSliderSpec:
    key: str
    title: str
    accessible_name: str
    scale: str
    minimum: float
    maximum: float
    finite_intervals: int
    unit: str
    low_endpoint: float | None = None
    high_endpoint: float | None = None
    low_meaning: str = ""
    high_meaning: str = ""


class PIDManualTuningPanel(QFrame):
    """High-level PID controls that map normalized sliders to real parameters."""

    parameter_changed = Signal(str, float)
    _FREQUENCY_MIN_HZ = 0.1
    _FREQUENCY_MAX_HZ = 100_000_000.0
    _PI_MAX_HZ = 1_000_000.0
    _PD_MIN_HZ = 10_000.0
    _LEAK_MAX_HZ = 125_000_000.0 / (256.0 * 2.0 * math.pi)
    _CONTROL_SPECS = (
        PIDSliderSpec(
            key="overall_gain",
            title="P · 整体增益",
            accessible_name="滑动调节 P 整体增益",
            scale="linear",
            minimum=-80.0,
            maximum=40.0,
            finite_intervals=1200,
            unit="dB",
            low_endpoint=float("-inf"),
            low_meaning="关闭 P、I、D 通道",
        ),
        PIDSliderSpec(
            key="pi_corner",
            title="I · PI 交点",
            accessible_name="滑动调节 I 通道 PI 交点频率",
            scale="log",
            minimum=_FREQUENCY_MIN_HZ,
            maximum=_PI_MAX_HZ,
            finite_intervals=999,
            unit="Hz",
            low_endpoint=0.0,
            low_meaning="关闭 I 通道",
        ),
        PIDSliderSpec(
            key="pd_corner",
            title="D · PD 交点",
            accessible_name="滑动调节 D 通道 PD 交点频率",
            scale="log",
            minimum=_PD_MIN_HZ,
            maximum=_FREQUENCY_MAX_HZ,
            finite_intervals=999,
            unit="Hz",
            high_endpoint=float("inf"),
            high_meaning="关闭 D 通道",
        ),
        PIDSliderSpec(
            key="saturation_gain",
            title="I · 饱和增益",
            accessible_name="滑动调节积分通道饱和增益",
            scale="linear",
            minimum=-80.0,
            maximum=80.0,
            finite_intervals=1600,
            unit="dB",
            high_endpoint=float("inf"),
            high_meaning="无泄漏",
        ),
        PIDSliderSpec(
            key="saturation_turning_frequency",
            title="I · 泄漏拐点",
            accessible_name="滑动调节积分泄漏拐点频率",
            scale="log",
            minimum=_FREQUENCY_MIN_HZ,
            maximum=_LEAK_MAX_HZ,
            finite_intervals=999,
            unit="Hz",
            low_endpoint=0.0,
            low_meaning="无泄漏",
        ),
    )

    def __init__(self, parent=None, available_keys=None):
        super().__init__(parent)
        self.setObjectName("pid_manual_tuning_panel")
        self.setAccessibleName("PID 实时滑动调参")
        self._available_keys = set(available_keys or ())
        self._sliders = {}
        self._value_labels = {}
        self._specs = {spec.key: spec for spec in self._CONTROL_SPECS}
        self._syncing = False

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(9)

        header = QHBoxLayout()
        title = QLabel("实时滑动调参")
        title.setObjectName("pid_tuning_title")
        hint = QLabel("拖动即应用 · 曲线实时更新")
        hint.setObjectName("pid_tuning_hint")
        hint.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(hint)
        root.addLayout(header)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        root.addLayout(grid)

        visible_specs = [
            spec for spec in self._CONTROL_SPECS
            if not self._available_keys or spec.key in self._available_keys
        ]
        for index, spec in enumerate(visible_specs):
            key = spec.key
            card = QFrame(self)
            card.setObjectName("pid_tuning_card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 7)
            card_layout.setSpacing(5)

            label_row = QHBoxLayout()
            label_row.setContentsMargins(0, 0, 0, 0)
            label = QLabel(spec.title)
            label.setObjectName("pid_tuning_label")
            value_label = QLabel("—")
            value_label.setObjectName("pid_tuning_value")
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label_row.addWidget(label)
            label_row.addStretch()
            label_row.addWidget(value_label)
            card_layout.addLayout(label_row)

            slider = QSlider(Qt.Horizontal, card)
            slider.setObjectName(f"pid_tune_{key}")
            slider.setAccessibleName(spec.accessible_name)
            meanings = "；".join(filter(None, (spec.low_meaning, spec.high_meaning)))
            meaning_hint = f"；{meanings}" if meanings else ""
            slider.setToolTip(
                f"{spec.title}：拖动实时更新数值与频率响应{meaning_hint}；精确值可在下方输入"
            )
            slider.setRange(0, self._maximum_position(spec))
            slider.setSingleStep(1)
            slider.setPageStep(25)
            slider.setTracking(True)
            slider.valueChanged.connect(
                lambda position, parameter_key=key: self._slider_value_changed(
                    parameter_key,
                    position,
                )
            )
            card_layout.addWidget(slider)

            range_row = QHBoxLayout()
            range_row.setContentsMargins(0, 0, 0, 0)
            low_label = QLabel(self._format_value(key, self._low_boundary(spec)))
            low_label.setObjectName("pid_tuning_range")
            high_label = QLabel(self._format_value(key, self._high_boundary(spec)))
            high_label.setObjectName("pid_tuning_range")
            high_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            range_row.addWidget(low_label)
            range_row.addStretch()
            range_row.addWidget(high_label)
            card_layout.addLayout(range_row)

            self._sliders[key] = slider
            self._value_labels[key] = value_label
            grid.addWidget(card, index // 2, index % 2)

        self.setStyleSheet(
            "QFrame#pid_manual_tuning_panel { background: #FFFFFF; border: 1px solid #C7CDD6; "
            "border-radius: 9px; }"
            "QFrame#pid_tuning_card { background: #F7F8FA; border: 1px solid #E1E5EB; "
            "border-radius: 7px; }"
            "QLabel#pid_tuning_title { color: #243447; font-size: 13px; font-weight: 700; "
            "border: none; background: transparent; }"
            "QLabel#pid_tuning_hint { color: #7B8492; font-size: 10px; border: none; "
            "background: transparent; }"
            "QLabel#pid_tuning_label { color: #4B5563; font-size: 11px; font-weight: 600; "
            "border: none; background: transparent; }"
            "QLabel#pid_tuning_value { color: #9B0036; font-size: 12px; font-weight: 700; "
            "border: none; background: transparent; }"
            "QLabel#pid_tuning_range { color: #929AA6; font-size: 9px; border: none; "
            "background: transparent; }"
            "QSlider::groove:horizontal { height: 6px; background: #DDE2E8; border-radius: 3px; }"
            "QSlider::sub-page:horizontal { background: #9B0036; border-radius: 3px; }"
            "QSlider::handle:horizontal { width: 18px; height: 18px; margin: -6px 0; "
            "background: #FFFFFF; border: 2px solid #9B0036; border-radius: 9px; }"
            "QSlider::handle:horizontal:hover { background: #FFF2F6; border-color: #B0003E; }"
            "QSlider::handle:horizontal:pressed { background: #F3DDE5; }"
            "QSlider:focus { outline: none; }"
        )

    @staticmethod
    def _has_low_endpoint(spec):
        return spec.low_endpoint is not None

    @staticmethod
    def _has_high_endpoint(spec):
        return spec.high_endpoint is not None

    @classmethod
    def _finite_start_position(cls, spec):
        return 1 if cls._has_low_endpoint(spec) else 0

    @classmethod
    def _finite_end_position(cls, spec):
        return cls._finite_start_position(spec) + spec.finite_intervals

    @classmethod
    def _maximum_position(cls, spec):
        return cls._finite_end_position(spec) + (1 if cls._has_high_endpoint(spec) else 0)

    @staticmethod
    def _low_boundary(spec):
        return spec.low_endpoint if spec.low_endpoint is not None else spec.minimum

    @staticmethod
    def _high_boundary(spec):
        return spec.high_endpoint if spec.high_endpoint is not None else spec.maximum

    @staticmethod
    def _endpoint_matches(value, endpoint):
        return endpoint is not None and value == endpoint

    @staticmethod
    def _format_frequency(value):
        value = float(value)
        if math.isinf(value):
            return ("−" if value < 0.0 else "+") + "∞ Hz"
        value = max(0.0, value)
        if value == 0.0:
            return "0 Hz"
        for scale, suffix in ((1e6, "MHz"), (1e3, "kHz")):
            if value >= scale:
                return f"{value / scale:.4g} {suffix}"
        return f"{value:.4g} Hz"

    @staticmethod
    def _finite_value(spec, fraction):
        fraction = max(0.0, min(1.0, float(fraction)))
        if spec.scale == "linear":
            return spec.minimum + (spec.maximum - spec.minimum) * fraction
        return 10.0 ** (
            math.log10(spec.minimum)
            + fraction * (math.log10(spec.maximum) - math.log10(spec.minimum))
        )

    @staticmethod
    def _finite_fraction(spec, value):
        value = max(spec.minimum, min(spec.maximum, float(value)))
        if spec.scale == "linear":
            return (value - spec.minimum) / (spec.maximum - spec.minimum)
        return (
            (math.log10(value) - math.log10(spec.minimum))
            / (math.log10(spec.maximum) - math.log10(spec.minimum))
        )

    def _position_to_value(self, key, position):
        spec = self._specs[key]
        maximum_position = self._maximum_position(spec)
        position = max(0, min(maximum_position, int(position)))

        if self._has_low_endpoint(spec) and position == 0:
            return spec.low_endpoint
        if self._has_high_endpoint(spec) and position == maximum_position:
            return spec.high_endpoint

        finite_position = position - self._finite_start_position(spec)
        fraction = finite_position / max(1, spec.finite_intervals)
        value = self._finite_value(spec, fraction)
        return round(value, 1) if spec.scale == "linear" else value

    def _value_to_position(self, key, value):
        spec = self._specs[key]
        try:
            value = float(value)
        except (TypeError, ValueError, OverflowError):
            value = spec.low_endpoint if self._has_low_endpoint(spec) else spec.minimum

        if self._endpoint_matches(value, spec.low_endpoint):
            return 0
        if self._endpoint_matches(value, spec.high_endpoint):
            return self._maximum_position(spec)

        if not math.isfinite(value):
            value = spec.maximum if value > 0.0 else spec.minimum
        if spec.scale == "log" and value <= 0.0:
            value = spec.minimum

        fraction = self._finite_fraction(spec, value)
        return self._finite_start_position(spec) + round(fraction * spec.finite_intervals)

    def _format_value(self, key, value):
        spec = self._specs[key]
        value = float(value)
        if math.isinf(value):
            sign = "−" if value < 0.0 else "+"
            return f"{sign}∞ {spec.unit}"
        if spec.unit == "dB":
            return f"{value:+.1f} dB"
        return self._format_frequency(value)

    def _slider_value_changed(self, key, position):
        if self._syncing:
            return
        value = self._position_to_value(key, position)
        self._value_labels[key].setText(self._format_value(key, value))
        self.parameter_changed.emit(key, value)

    def set_parameters(self, parameters):
        parameters = dict(parameters or {})
        self._syncing = True
        try:
            for key, slider in self._sliders.items():
                value = parameters.get(key, 0.0)
                slider.blockSignals(True)
                slider.setValue(self._value_to_position(key, value))
                slider.blockSignals(False)
                self._value_labels[key].setText(self._format_value(key, value))
        finally:
            self._syncing = False


class PIDResponseWindow(QDialog):
    """Resizable standalone view kept in sync with the PID parameter canvas."""

    def __init__(self, parameters=None, changed_key=None, parent=None):
        super().__init__(parent)
        self.setObjectName("pid_response_window")
        self.setAccessibleName("PID 实时频率响应独立窗口")
        self.setWindowTitle("PID 实时频率响应 · 独立窗口")
        self.setModal(False)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setMinimumSize(640, 400)
        self.resize(900, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        self._canvas = PIDParamCanvas(self, allow_expand=False, compact=False)
        self._canvas.setObjectName("pid_response_expanded_canvas")
        layout.addWidget(self._canvas, 1)
        self.set_parameters(parameters or {}, changed_key=changed_key)

    def set_parameters(self, parameters, changed_key=None):
        self._canvas.set_parameters(parameters, changed_key=changed_key)
