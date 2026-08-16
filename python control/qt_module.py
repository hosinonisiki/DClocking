from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QListWidget, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem,
                               QSplitter, QGraphicsEllipseItem, QDialog, QFormLayout,
                               QSpinBox, QDoubleSpinBox, QLineEdit,
                               QCheckBox, QPushButton, QToolButton, QToolTip, QComboBox,
                               QMessageBox, QLabel, QSizePolicy, QFrame)
# 导入PySide6的QtCore模块中的相关类
from PySide6.QtCore import Qt, QMimeData, QPointF, QRectF, Signal, QObject, QByteArray, QPoint
# 导入PySide6.QtGui模块中的相关类
from PySide6.QtGui import QDrag, QPainter, QPen, QBrush, QPainterPath, QColor, QFont, QPixmap, QImage, QCursor
import math
import re
import numpy as np
from scipy import signal as scipy_signal
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from qt_module_schema import PID_SCHEMA, ACCM_SCHEMA, SCLR_SCHEMA, FIRF_SCHEMA, LTRN_SCHEMA, PDH_SCHEMA, SCLO_SCHEMA, IIR_SCHEMA
from quantity_entry_core import QuantityEntryCore, QuantityFormat
from qt_ui_theme import UiColors, draw_node_chrome

_PARAM_APPLY_HANDLER = None
_PARAM_OPEN_HANDLER = None
_CACHE_MISSING = object()

def set_param_apply_handler(handler):
    global _PARAM_APPLY_HANDLER
    _PARAM_APPLY_HANDLER = handler

def set_param_open_handler(handler):
    global _PARAM_OPEN_HANDLER
    _PARAM_OPEN_HANDLER = handler

def _dispatch_param_apply(node, params):
    if _PARAM_APPLY_HANDLER:
        _PARAM_APPLY_HANDLER(node, params)

def _dispatch_param_open(node):
    if _PARAM_OPEN_HANDLER:
        try:
            return bool(_PARAM_OPEN_HANDLER(node))
        except Exception as exc:
            print(f"[param] open panel failed: {exc}")
    return False


class QuantityLineEdit(QLineEdit):
    STATE_STYLE = {
        "unchanged": "",
        "changed": "QLineEdit { background-color: #fff2a8; }",
        "rolling": "",
        "disabled": "QLineEdit { background-color: #d9d9d9; color: #606060; }",
    }
    KEY_MAP = {
        Qt.Key_Return: "Return",
        Qt.Key_Enter: "Return",
        Qt.Key_Left: "Left",
        Qt.Key_Right: "Right",
        Qt.Key_Up: "Up",
        Qt.Key_Down: "Down",
    }
    PREFIX_UNITS = {"Hz", "V", "s", "A", "W"}
    SIGNED_16BIT_FULL_SCALE = Decimal("32768")
    SIGNED_16BIT_DISPLAY_FULL_SCALE = Decimal("5")

    def __init__(self, value=0, field=None, parent=None, report_callback=None, roll_finished_callback=None):
        super().__init__(parent)
        self._field = dict(field or {})
        self._syncing = False
        self._report_callback = report_callback
        self._roll_finished_callback = roll_finished_callback
        self._deferred_external_value = None
        self._format = self._build_format(self._field)
        self.core = QuantityEntryCore(
            formater=self._format,
            report=self._report_quantity_change if report_callback else None,
        )

        self.textEdited.connect(self._sync_core_from_widget)
        self._set_initial_value(value)
        self._refresh_view()

    @staticmethod
    def _field_unit(field: dict) -> str:
        if QuantityLineEdit._uses_voltage_display(field):
            return "V"
        unit = field.get("unit", "")
        if unit:
            return unit
        label = str(field.get("label", ""))
        match = re.search(r"\(([^()]+)\)\s*$", label)
        return match.group(1) if match else ""

    @staticmethod
    def _uses_voltage_display(field: dict) -> bool:
        return bool(field.get("display_voltage"))

    @classmethod
    def _prefix_map_for_field(cls, field: dict) -> dict[str, float]:
        if cls._uses_voltage_display(field):
            return {}
        prefix = field.get("prefix")
        if isinstance(prefix, dict):
            return dict(prefix)
        if prefix is True:
            return dict(QuantityFormat.default_prefix)
        if prefix is False:
            return {}
        if cls._field_unit(field) in cls.PREFIX_UNITS:
            return dict(QuantityFormat.default_prefix)
        return {}

    @staticmethod
    def _integer_digits_for_value(value) -> int:
        magnitude = abs(Decimal(str(value)))
        if magnitude < 1:
            return 1
        return magnitude.adjusted() + 1

    @classmethod
    def _build_format(cls, field: dict) -> QuantityFormat:
        unit = cls._field_unit(field)
        if cls._uses_voltage_display(field):
            return QuantityFormat(
                digits_limit=(1, 6, 0),
                prefix={},
                unit=unit,
            )
        digits_limit = field.get("digits_limit")
        if digits_limit is not None:
            int_limit, frac_limit, min_frac = digits_limit
            return QuantityFormat(
                digits_limit=(int(int_limit), int(frac_limit), int(min_frac)),
                prefix=cls._prefix_map_for_field(field),
                unit=unit,
            )

        ftype = field.get("type", "str")
        frac_limit = 0 if ftype == "int" else int(max(0, field.get("decimals", 6)))
        min_frac = 0 if ftype == "int" else int(max(0, field.get("min_decimals", 0)))
        int_limit = int(max(1, field.get("int_digits", 1))) if "int_digits" in field else 1

        if "int_digits" not in field:
            for key in ("min", "max", "default"):
                value = field.get(key)
                if isinstance(value, bool) or value is None:
                    continue
                if isinstance(value, (int, float)):
                    int_limit = max(int_limit, cls._integer_digits_for_value(value))

        return QuantityFormat(
            digits_limit=(int_limit, frac_limit, min_frac),
            prefix=cls._prefix_map_for_field(field),
            unit=unit,
        )

    @classmethod
    def _raw_signed_16bit_to_display_voltage(cls, value) -> Decimal:
        raw = Decimal(str(value))
        return raw * cls.SIGNED_16BIT_DISPLAY_FULL_SCALE / cls.SIGNED_16BIT_FULL_SCALE

    @classmethod
    def _display_voltage_to_raw_signed_16bit(cls, value) -> int:
        raw = Decimal(str(value)) * cls.SIGNED_16BIT_FULL_SCALE / cls.SIGNED_16BIT_DISPLAY_FULL_SCALE
        raw = raw.to_integral_value(rounding=ROUND_HALF_UP)
        if raw < Decimal("-32768"):
            raw = Decimal("-32768")
        if raw > Decimal("32767"):
            raw = Decimal("32767")
        return int(raw)

    def _display_value_from_raw(self, value):
        if self._uses_voltage_display(self._field):
            return self._raw_signed_16bit_to_display_voltage(value)
        return value

    def _raw_value_from_display(self, value):
        if self._uses_voltage_display(self._field):
            return self._display_voltage_to_raw_signed_16bit(value)
        return value

    def _format_numeric_text(self, value) -> str:
        frac_limit = int(self._format.digits_limit[1])
        min_frac = int(self._format.digits_limit[2])

        try:
            number = Decimal(str(self._display_value_from_raw(value)))
        except Exception:
            raise ValueError(f"Invalid numeric value: {value!r}")

        if not number.is_finite():
            if number.is_nan():
                raise ValueError("NaN is not a supported parameter value")
            if number.is_signed():
                return "-inf" + self._format.unit
            return "inf" + self._format.unit

        frac_limit = int(self._format.digits_limit[1])

        try:
            with localcontext() as ctx:
                ctx.prec = max(len(number.as_tuple().digits) + frac_limit + 4, 32)
                if frac_limit == 0:
                    number = number.quantize(Decimal("1"))
                else:
                    number = number.quantize(Decimal(1).scaleb(-frac_limit))
        except InvalidOperation:
            raise ValueError(f"Unable to format numeric value: {value!r}")

        if number == 0:
            number = Decimal("0")

        text = format(number, "f")
        if "." in text:
            integer, fraction = text.split(".", 1)
            fraction = fraction.rstrip("0")
            if len(fraction) < min_frac:
                fraction = fraction + ("0" * (min_frac - len(fraction)))
            if fraction:
                text = integer + "." + fraction
            else:
                text = integer
        elif min_frac > 0:
            text = text + "." + ("0" * min_frac)

        if text in {"", "-0"}:
            text = "0" if min_frac == 0 else "0." + ("0" * min_frac)
        return text + self._format.unit

    def _set_nonfinite_display(self, text: str, value: float) -> None:
        self.core.text = text
        self.core.stored = text
        self.core.state = self.core.UNCHANGED
        self.core.result = None
        self.core.value = value
        self.core.formalized = text
        self.core.selected = None

    def _set_initial_value(self, value) -> None:
        text = self._format_numeric_text(value)
        if text in {"inf" + self._format.unit, "-inf" + self._format.unit}:
            self._set_nonfinite_display(text, float(value))
            return
        self.core.set_text(text, mark_changed=False)
        self.core.store()

    def set_quantity_value(self, value) -> None:
        self._deferred_external_value = None
        self._set_initial_value(value)
        self._refresh_view()

    def defer_external_value(self, value) -> None:
        self._deferred_external_value = value

    def apply_deferred_external_value(self) -> bool:
        if self._deferred_external_value is None:
            return False
        value = self._deferred_external_value
        self._deferred_external_value = None
        self.set_quantity_value(value)
        return True

    def should_defer_external_update(self, value) -> bool:
        if self.core.state != self.core.ROLLING:
            return False

        current_value = self.core.get_value()
        result = self.core.result
        if current_value is None or result is None:
            result, current_value, _formalized = self._format.match(self.core.get_text())
            if result is None:
                return False

        try:
            current_text = self._format_numeric_text(current_value)
            external_text = self._format_numeric_text(value)
        except Exception:
            return False
        if current_text == external_text:
            return True

        try:
            prefix = result.group("prefix") or ""
            prefix_scale = Decimal(str(self._format.prefix.get(prefix, 1)))
            step = abs(self.core._selected_place_step() * prefix_scale)
            tolerance = step * Decimal("0.1")
            current_decimal = Decimal(str(current_value))
            external_decimal = Decimal(str(self._display_value_from_raw(value)))
        except Exception:
            return False

        if not current_decimal.is_finite() or not external_decimal.is_finite():
            return False

        return abs(external_decimal - current_decimal) <= tolerance

    def _set_widget_text(self, text: str) -> None:
        self._syncing = True
        try:
            self.setText(text)
        finally:
            self._syncing = False

    def _sync_core_from_widget(self) -> None:
        if self._syncing or self.core.state == self.core.ROLLING:
            return
        self.core.set_text(self.text())
        self._refresh_view()

    def _refresh_view(self) -> None:
        text = self.core.get_text()
        if self.text() != text:
            self._set_widget_text(text)

        self.setStyleSheet(self.STATE_STYLE.get(self.core.visual_state, ""))

        selected = self.core.selected_range
        if selected is None:
            self.deselect()
        else:
            start, end = selected
            self.setSelection(start, max(0, end - start))

    def _report_quantity_change(self, *_args) -> None:
        if self._report_callback:
            self._report_callback()

    def quantity_value(self, preserve_roll=False):
        if self.core.state == self.core.CHANGED:
            if not self.core.store():
                return None
        elif self.core.state == self.core.ROLLING:
            if preserve_roll:
                self.core.result, self.core.value, self.core.formalized = self._format.match(self.core.get_text())
                if self.core.result is None:
                    return None
            else:
                if not self.core.exit_roll(report=False):
                    return None
        self._refresh_view()
        return self._raw_value_from_display(self.core.get_value())

    def preview_quantity_value(self):
        """Parse the visible text without committing it or changing editor state."""
        text = self.text().strip()
        unit = self._format.unit
        numeric_text = text[:-len(unit)] if unit and text.endswith(unit) else text
        if numeric_text in {"inf", "+inf"}:
            return self._raw_value_from_display(float("inf"))
        if numeric_text == "-inf":
            return self._raw_value_from_display(float("-inf"))

        result, value, _formalized = self._format.match(text)
        if result is None:
            return None
        return self._raw_value_from_display(value)

    def setEnabled(self, enabled):
        self.core.set_enabled(bool(enabled))
        super().setEnabled(enabled)
        self._refresh_view()

    def keyPressEvent(self, event):
        key_name = self.KEY_MAP.get(event.key())
        if key_name is not None and self.core.handle_key(key_name):
            self._refresh_view()
            event.accept()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        handled = self.core.handle_click()
        super().mousePressEvent(event)
        if handled:
            self._refresh_view()

    def focusOutEvent(self, event):
        if self.core.state == self.core.CHANGED:
            self.core.set_text(self.core.stored, mark_changed=False)
            self.core.refresh_state()
        elif self.core.state == self.core.ROLLING:
            self.core.exit_roll(report=False)
            applied = self.apply_deferred_external_value()
            if self._roll_finished_callback and not applied:
                self._roll_finished_callback()
        self._refresh_view()
        super().focusOutEvent(event)

class PIDParamCanvas(QWidget):
    """Live Bode magnitude preview using the same scaling as ``ModulePID``."""

    _DIRECT_KEYS = {"gain_p", "gain_i", "gain_d", "leak_digit"}
    _MAX_PLOT_FREQUENCY_HZ = 125_000_000.0

    def __init__(self, parent=None, allow_expand=True, compact=True):
        super().__init__(parent)
        self._parameters = {}
        self._changed_key = None
        self._expanded_window = None
        self._response = self.calculate_response({}, self._logspace(1.0, 100_000_000.0, 180))
        if compact:
            self.setMinimumSize(340, 205)
            self.setFixedHeight(220)
        else:
            self.setMinimumSize(600, 360)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setToolTip("依据 FPGA PID 定标实时计算：P、I、D 分量及其复数合成幅频响应")

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
        use_direct = changed_key in cls._DIRECT_KEYS or not has_indirect

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

    def response_data(self):
        return dict(self._response)

    @staticmethod
    def _format_frequency(value):
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
            "LIVE · FPGA MODEL",
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

        low_frequency = frequencies[0]
        high_frequency = frequencies[-1]
        log_low = math.log10(low_frequency)
        log_span = max(1e-9, math.log10(high_frequency) - log_low)

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
            ("leak_frequency_hz", "泄漏", QColor("#A670D6")),
            ("pi_corner_hz", "PI", QColor("#E9953E")),
            ("pd_corner_hz", "PD", QColor("#25A8A2")),
        )
        for key, label, color in marker_specs:
            frequency = response.get(key)
            if frequency is None or not math.isfinite(frequency) or not (low_frequency <= frequency <= high_frequency):
                continue
            x = map_x(frequency)
            painter.setPen(QPen(color, 1, Qt.DashLine))
            painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))
            painter.setPen(color)
            painter.drawText(QRectF(x - 18, plot_rect.top() + 2, 36, 11), Qt.AlignCenter, label)

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
                "请增大通带频率或调整抽头数"
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
    def _map_linear(value, low, high, pixel_low, pixel_high):
        span = max(1e-12, high - low)
        return pixel_low + (value - low) / span * (pixel_high - pixel_low)

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
        nyquist = result["freq_sample"] / 2.0
        pass_fraction = result["freq_pass"] / nyquist
        stop_fraction = result["freq_stop"] / nyquist
        pass_color = QColor("#DFF3EC")
        transition_color = QColor("#FFF1D8")
        stop_color = QColor("#F3E4E9")
        painter.fillRect(QRectF(plot_rect.left(), plot_rect.top(), plot_rect.width() * pass_fraction, plot_rect.height()), pass_color)
        painter.fillRect(
            QRectF(plot_rect.left() + plot_rect.width() * pass_fraction, plot_rect.top(),
                   plot_rect.width() * (stop_fraction - pass_fraction), plot_rect.height()),
            transition_color,
        )
        painter.fillRect(
            QRectF(plot_rect.left() + plot_rect.width() * stop_fraction, plot_rect.top(),
                   plot_rect.width() * (1.0 - stop_fraction), plot_rect.height()),
            stop_color,
        )
        self._draw_grid(
            painter,
            plot_rect,
            [(fraction, self._format_frequency(nyquist * fraction)) for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)],
            [(fraction, f"{-100 + fraction * 105:.0f}") for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)],
        )
        for frequency, label, color in (
            (result["freq_pass"], "FP", QColor("#1F8F75")),
            (result["freq_stop"], "FS", QColor("#A4003B")),
        ):
            x = self._map_linear(frequency, 0.0, nyquist, plot_rect.left(), plot_rect.right())
            painter.setPen(QPen(color, 1, Qt.DashLine))
            painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))
            painter.setPen(color)
            painter.drawText(QRectF(x - 15, plot_rect.top() + 3, 30, 12), Qt.AlignCenter, label)

        path = QPainterPath()
        active = False
        for frequency, magnitude in zip(result["frequencies_hz"], result["magnitude_db"]):
            clipped = max(-100.0, min(5.0, magnitude))
            point = QPointF(
                self._map_linear(frequency, 0.0, nyquist, plot_rect.left(), plot_rect.right()),
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
        phases = result["phase_degrees"]
        phase_min = math.floor(min(phases) / 180.0) * 180.0
        phase_max = max(0.0, math.ceil(max(phases) / 180.0) * 180.0)
        if phase_max <= phase_min:
            phase_max = phase_min + 360.0
        nyquist = result["freq_sample"] / 2.0
        self._draw_grid(
            painter,
            plot_rect,
            [(fraction, self._format_frequency(nyquist * fraction)) for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)],
            [(fraction, f"{phase_min + fraction * (phase_max - phase_min):.0f}°") for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)],
        )
        path = QPainterPath()
        for index, (frequency, phase) in enumerate(zip(result["frequencies_hz"], phases)):
            point = QPointF(
                self._map_linear(frequency, 0.0, nyquist, plot_rect.left(), plot_rect.right()),
                self._map_linear(phase, phase_min, phase_max, plot_rect.bottom(), plot_rect.top()),
            )
            path.moveTo(point) if index == 0 else path.lineTo(point)
        painter.setPen(QPen(QColor("#25A8A2"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)

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
        if self._expanded_window is not None:
            try:
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

class ParamDialog(QDialog):
    def __init__(self, schema: list[dict], values: dict, parent = None, apply_callback = None, companion_widget_factory = None):
        super().__init__(parent)
        self.setWindowTitle("参数修改")
        self._editors = {}
        self._fields = {}
        self._apply_callback = apply_callback
        self._committed_values = {}
        self._enter_committed_keys = set()
        self._companion_widget = None
        self._companion_refresh_suspended = False

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)
        form_host = QWidget(self)
        layout = QFormLayout(form_host)
        root.addWidget(form_host, 0)

        if callable(companion_widget_factory):
            self._companion_widget = companion_widget_factory(self)
            if self._companion_widget is not None:
                root.addWidget(self._companion_widget, 0)

        for field in schema:
            key = field["key"]
            label = field.get("label", key)
            ftype = field.get("type", "str")
            self._fields[key] = field

            control_mode = field.get("ui_control")
            if control_mode == "flip_toggle":
                w = QPushButton()
                w.setCheckable(True)
                w.setChecked(bool(values.get(key, field.get("default", False))))
                self._set_toggle_button_text(w, label, w.isChecked())
                w.toggled.connect(lambda checked, k=key, t=label, btn=w: self._apply_toggle_field(k, t, btn, checked))
                self._editors[key] = ("flip_toggle", w)
                layout.addRow(label, w)
                continue

            if control_mode == "flip_pulse":
                w = QPushButton(label)
                w.setCheckable(False)
                w.clicked.connect(lambda _checked=False, k=key: self._apply_pulse_field(k))
                self._editors[key] = ("flip_pulse", w)
                layout.addRow(label, w)
                continue

            if ftype == "int":
                w = QuantityLineEdit(
                    value=int(values.get(key, field.get("default", 0))),
                    field=field,
                    report_callback=lambda k=key: self._apply_field(k, preserve_roll=True),
                    roll_finished_callback=lambda k=key: self._apply_field(k),
                )
                self._editors[key] = ("int_qty", w)
            elif ftype == "float":
                w = QuantityLineEdit(
                    value=float(values.get(key, field.get("default", 0.0))),
                    field=field,
                    report_callback=lambda k=key: self._apply_field(k, preserve_roll=True),
                    roll_finished_callback=lambda k=key: self._apply_field(k),
                )
                self._editors[key] = ("float_qty", w)
            elif ftype == "bool":
                w = QCheckBox()
                w.setChecked(bool(values.get(key, field.get("default", False))))
                w.toggled.connect(lambda _checked=False, k=key: self._apply_field(k))
                self._editors[key] = (ftype, w)
            else:
                w = QLineEdit()
                w.setText(str(values.get(key, field.get("default", ""))))
                self._bind_text_events(key, w)
                self._editors[key] = (ftype, w)

            layout.addRow(label, w)
            if isinstance(w, QLineEdit):
                w.textChanged.connect(lambda _text, k=key: self._refresh_companion(k))
            elif isinstance(w, QCheckBox):
                w.toggled.connect(lambda _checked, k=key: self._refresh_companion(k))

        for key in self._editors.keys():
            try:
                self._committed_values[key] = self._value_from_editor(key)
            except Exception:
                continue
        self._refresh_companion()

    def _preview_value_from_editor(self, key: str):
        ftype, widget = self._editors[key]
        if ftype in {"int_qty", "float_qty"}:
            value = widget.preview_quantity_value()
            if value is None:
                raise ValueError("Invalid quantity input")
            return int(value) if ftype == "int_qty" and float(value).is_integer() else float(value)
        if ftype in {"bool", "flip_toggle"}:
            return bool(widget.isChecked())
        if ftype == "flip_pulse":
            return None
        return widget.text()

    def _refresh_companion(self, changed_key=None) -> None:
        if self._companion_refresh_suspended or self._companion_widget is None:
            return
        setter = getattr(self._companion_widget, "set_parameters", None)
        if not callable(setter):
            return

        preview_values = dict(self._committed_values)
        for key in self._editors:
            try:
                preview_values[key] = self._preview_value_from_editor(key)
            except Exception:
                continue
        setter(preview_values, changed_key=changed_key)

    def _bind_text_events(self, key: str, widget: QLineEdit) -> None:
        widget.returnPressed.connect(lambda k=key: self._apply_field_on_enter(k))
        widget.editingFinished.connect(lambda k=key: self._revert_if_not_committed(k))

    def _apply_field_on_enter(self, key: str) -> None:
        if self._apply_field(key):
            self._enter_committed_keys.add(key)
        else:
            self._restore_committed_value(key)

    def _revert_if_not_committed(self, key: str) -> None:
        if key in self._enter_committed_keys:
            self._enter_committed_keys.discard(key)
            return
        self._restore_committed_value(key)

    def _restore_committed_value(self, key: str) -> None:
        if key not in self._committed_values or key not in self._editors:
            return

        ftype, widget = self._editors[key]
        value = self._committed_values[key]

        if ftype == "bool":
            widget.blockSignals(True)
            widget.setChecked(bool(value))
            widget.blockSignals(False)
            return

        if ftype == "flip_toggle":
            checked = bool(value)
            widget.blockSignals(True)
            widget.setChecked(checked)
            widget.blockSignals(False)
            label = self._fields.get(key, {}).get("label", key)
            self._set_toggle_button_text(widget, label, checked)
            return

        if ftype == "flip_pulse":
            return

        if ftype in {"int_qty", "float_qty"}:
            return

        widget.setText("" if value is None else str(value))

    def _value_from_editor(self, key: str, preserve_roll: bool = False):
        ftype, w = self._editors[key]
        field = self._fields.get(key, {})
        min_v = field.get("min", None)
        max_v = field.get("max", None)

        if ftype == "int_qty":
            si = w.quantity_value(preserve_roll=preserve_roll)
            if si is None:
                raise ValueError("Invalid quantity input")
            integer_value = Decimal(str(si))
            if integer_value != integer_value.to_integral_value():
                raise ValueError("Integer parameter requires an integer value")
            value = int(integer_value)
            if min_v is not None and value < min_v:
                raise ValueError(f"Value is below minimum {min_v}")
            if max_v is not None and value > max_v:
                raise ValueError(f"Value is above maximum {max_v}")
            return value

        if ftype == "float_qty":
            si = w.quantity_value(preserve_roll=preserve_roll)
            if si is None:
                raise ValueError("Invalid quantity input")
            value = float(si)
            if min_v is not None and value < min_v:
                raise ValueError(f"Value is below minimum {min_v}")
            if max_v is not None and value > max_v:
                raise ValueError(f"Value is above maximum {max_v}")
            return value

        if ftype == "bool":
            return bool(w.isChecked())
        if ftype == "flip_toggle":
            return bool(w.isChecked())
        if ftype == "flip_pulse":
            return None
        return w.text()

    def _set_toggle_button_text(self, button: QPushButton, label: str, checked: bool):
        state_text = "按下" if checked else "弹起"
        button.setText(f"{label}: {state_text}")

    def _apply_toggle_field(self, key: str, label: str, button: QPushButton, checked: bool):
        self._set_toggle_button_text(button, label, checked)
        if not self._apply_callback:
            return
        self._apply_callback({key: bool(checked)})
        self._committed_values[key] = bool(checked)

    def _apply_pulse_field(self, key: str):
        if not self._apply_callback:
            return
        self._apply_callback({key: None})

    def _apply_field(self, key: str, preserve_roll: bool = False) -> bool:
        if not self._apply_callback:
            return False
        try:
            value = self._value_from_editor(key, preserve_roll=preserve_roll)
            self._apply_callback({key: value})
            self._committed_values[key] = value
            return True
        except Exception as exc:
            QMessageBox.warning(self, "参数错误", str(exc))
            return False

    def _apply_all_fields(self) -> None:
        if not self._apply_callback:
            return
        try:
            payload = {}
            for key in self._batch_keys:
                payload[key] = self._value_from_editor(key)
            if payload:
                self._apply_callback(payload)
                self._committed_values.update(payload)
        except Exception as exc:
            QMessageBox.warning(self, "参数错误", str(exc))

    def values(self) -> dict:
        out = {}
        for key in self._editors.keys():
            try:
                out[key] = self._value_from_editor(key)
            except Exception:
                continue
        return out

    def set_values(self, values: dict) -> None:
        if not isinstance(values, dict):
            return

        self._companion_refresh_suspended = True
        try:
            for key, value in values.items():
                editor = self._editors.get(key)
                if editor is None:
                    continue

                ftype, widget = editor
                if ftype == "bool":
                    widget.blockSignals(True)
                    widget.setChecked(bool(value))
                    widget.blockSignals(False)
                elif ftype == "flip_toggle":
                    checked = bool(value)
                    widget.blockSignals(True)
                    widget.setChecked(checked)
                    widget.blockSignals(False)
                    label = self._fields.get(key, {}).get("label", key)
                    self._set_toggle_button_text(widget, label, checked)
                elif ftype == "flip_pulse":
                    pass
                elif ftype in {"int_qty", "float_qty"}:
                    if widget.should_defer_external_update(value):
                        widget.defer_external_value(value)
                        self._committed_values[key] = value
                        continue
                    widget.set_quantity_value(0 if value is None else value)
                else:
                    widget.setText("" if value is None else str(value))

                self._committed_values[key] = value
        finally:
            self._companion_refresh_suspended = False

        self._enter_committed_keys.clear()
        self._refresh_companion()

class SpecialMethodDialog(QDialog):
    def __init__(self, methods: list[dict], parent=None, apply_callback=None, initial_values=None):
        super().__init__(parent)
        self.setWindowTitle("特殊方法")
        self._methods = methods or []
        self._apply_callback = apply_callback
        self._method_map = {m["name"]: m for m in self._methods if "name" in m}
        self._initial_values = initial_values or {}
        self._param_editors = {}

        root = QVBoxLayout(self)
        self._method_combo = QComboBox()
        for m in self._methods:
            method_name = m.get("name")
            method_label = m.get("label", method_name)
            self._method_combo.addItem(method_label, method_name)
        root.addWidget(self._method_combo)

        self._form = QFormLayout()
        root.addLayout(self._form)

        btn_row = QHBoxLayout()
        self._apply_btn = QPushButton("应用")
        self._apply_btn.clicked.connect(self._apply_selected_method)
        btn_row.addWidget(self._apply_btn)
        root.addLayout(btn_row)

        self._method_combo.currentIndexChanged.connect(self._rebuild_param_form)
        self._rebuild_param_form()

    def _clear_form(self):
        while self._form.rowCount() > 0:
            self._form.removeRow(0)
        self._param_editors.clear()

    def _current_method(self):
        name = self._method_combo.currentData()
        return self._method_map.get(name)

    def _rebuild_param_form(self):
        self._clear_form()
        method = self._current_method()
        if not method:
            return

        method_name = method.get("name")
        method_initials = self._initial_values.get(method_name, {}) if method_name else {}

        for field in method.get("params", []):
            key = field["key"]
            label = field.get("label", key)
            ftype = field.get("type", "str")
            init_value = method_initials.get(key, field.get("default"))

            if ftype == "int":
                w = QuantityLineEdit(value=int(init_value if init_value is not None else 0), field=field)
            elif ftype == "float":
                w = QuantityLineEdit(value=float(init_value if init_value is not None else 0.0), field=field)
            elif ftype == "choice":
                w = QComboBox()
                for option in field.get("options", []):
                    if isinstance(option, dict):
                        w.addItem(str(option.get("label", option.get("value", ""))), option.get("value"))
                    else:
                        w.addItem(str(option), option)
                default_value = init_value
                if default_value is not None:
                    idx = w.findData(default_value)
                    if idx >= 0:
                        w.setCurrentIndex(idx)
            else:
                w = QLineEdit()
                w.setText(str(init_value if init_value is not None else ""))

            self._param_editors[key] = (ftype, w)
            self._form.addRow(label, w)

    def _collect_args(self):
        args = {}
        for key, (ftype, w) in self._param_editors.items():
            if ftype == "int":
                si = w.quantity_value()
                if si is None:
                    raise ValueError(f"Invalid value for {key}")
                integer_value = Decimal(str(si))
                if integer_value != integer_value.to_integral_value():
                    raise ValueError(f"Integer parameter {key} requires an integer value")
                args[key] = int(integer_value)
            elif ftype == "float":
                si = w.quantity_value()
                if si is None:
                    raise ValueError(f"Invalid value for {key}")
                args[key] = float(si)
            elif ftype == "choice":
                args[key] = w.currentData()
            else:
                args[key] = w.text()
        return args

    def _apply_selected_method(self):
        method = self._current_method()
        if not method or not self._apply_callback:
            return
        try:
            method_name = method["name"]
            args = self._collect_args()
            self._apply_callback(method_name, args)
            self._initial_values[method_name] = dict(args)
            QMessageBox.information(self, "成功", "特殊方法已应用")
        except Exception as exc:
            QMessageBox.critical(self, "失败", f"特殊方法执行失败:\n{exc}")

class PortItem(QGraphicsItem):
    """
    表示节点上的输入/输出端口的图形项类
    """
    COLOR_POOL = [
        "#E74C3C",  "#3498DB",  "#2ECC71",  "#F39C12",  "#9B59B6",
        "#1ABC9C",  "#E91E63",  "#FF5722",  "#00BCD4",  "#FFEB3B",
        "#8BC34A",  "#FF9800",  "#673AB7",  "#03A9F4",  "#CDDC39",
        "#FFC107",  "#009688",  "#795548",  "#607D8B",
    ]

    def __init__(self, parent, port_type, index, signals = [""], radius=6):
        super().__init__(parent)
        self.parent_node = parent
        self.port_type = port_type
        self.index = index
        self.radius = radius
        self.connections = []
        self.signals = signals
        self.manual_turn_distance = None
        self.manual_bypass_y = None
        self.manual_reverse_h_extend = None

        if self.port_type == 'out':
            self.line_color = self._assign_unique_color()
        else:
            self.line_color = None

        if self.port_type == 'in':
            self.brush = QBrush(QColor("#3CE75B"))
        else:
            self.brush = QBrush(QColor("#E74C3C"))

        self.setAcceptHoverEvents(True)
        self.setZValue(10)
        self._update_tooltip()

        # amount to extend the visible line out from the port circle
        self._line_extend = 40

    def _assign_unique_color(self):
        if self.parent_node:
            unique_id = id(self.parent_node) + self.index
        else:
            unique_id = id(self) + self.index
        color_index = unique_id % len(self.COLOR_POOL)
        return self.COLOR_POOL[color_index]

    def boundingRect(self):
        # 给信号标记留出足够的边界，避免被裁剪
        extra_x = 16   # 覆盖 marker_x 附近 + 图形宽度 + 笔宽余量
        extra_y = 18   # 覆盖 top_y=-10 的上方半径、以及下方菱形/方块

        if self.port_type == 'out':
            return QRectF(
                -self.radius,
                -self.radius - extra_y,
                2 * self.radius + self._line_extend + extra_x,
                2 * self.radius + 2 * extra_y
            )
        else:
            return QRectF(
                -self._line_extend - self.radius - extra_x,
                -self.radius - extra_y,
                2 * self.radius + self._line_extend + extra_x,
                2 * self.radius + 2 * extra_y
            )
    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(QPen(QColor(UiColors.TEXT_ON_DARK), 1))
        painter.drawEllipse(-self.radius, -self.radius, 2*self.radius, 2*self.radius)

        # draw the outward short wire from the port center
        painter.save()
        line_pen = QPen(QColor(self.line_color) if self.line_color else Qt.gray, 2)
        line_pen.setCapStyle(Qt.RoundCap)
        line_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(line_pen)
        line_y = self.radius + 4   # 你可以改成 +3/+6 来微调高度
        if self.port_type == 'out':
            x2 = self._line_extend
            painter.drawLine(line_y-1, 0, x2, 0)
            marker_x = x2 - 6
        else:
            x2 = -self._line_extend
            painter.drawLine(line_y-17, 0, x2, 0)
            marker_x = x2 + 6

        # draw markers for signal types above/below the wire
        self._draw_signal_markers(painter, marker_x,line_y,side="top")
        painter.restore()

    def _draw_signal_markers(self, painter, x_pos, line_y, side="top"):
        """
        将所有信号标记绘制在横线同一侧（默认上方）。
        x_pos: 标记中心的参考x
        line_y: 横线y坐标
        side: "top" 或 "bottom"
        """
        # 统一画在同一侧
        if side == "bottom":
            y_base = line_y + 10
        else:
            y_base = line_y - 20

        # 不再�� top/bottom，两侧规则合并
        kind_map = {
            "level": "tick",          # 五角星
            "phase": "circle",        # 圆形
            "differential": "diamond",# 菱形
            "bool": "square",         # 方形
        }

        signals = self.signals if isinstance(self.signals, (list, tuple, set)) else [self.signals]
        items = []
        unknown = []
        for s in signals:
            if not s:
                continue
            key = str(s).lower()
            kind = kind_map.get(key)
            if kind:
                items.append((key, kind))
            else:
                unknown.append(key)

        pen = QPen(Qt.white, 1)
        brush = QBrush(Qt.white)
        painter.setPen(pen)
        painter.setBrush(brush)

        # 同一侧横向排布
        h_step = 10
        n = len(items)
        if n:
            start_x = x_pos - (n - 1) * h_step / 2
            for i, (k, kind) in enumerate(items):
                sx = start_x + i * h_step

                if kind == "tick":
                    outer_r = 4
                    inner_r = 1.6
                    path = QPainterPath()
                    for j in range(10):
                        angle_deg = -90 + j * 36
                        r = outer_r if j % 2 == 0 else inner_r
                        angle = math.radians(angle_deg)
                        px = sx + r * math.cos(angle)
                        py = y_base + r * math.sin(angle)
                        if j == 0:
                            path.moveTo(px, py)
                        else:
                            path.lineTo(px, py)
                    path.closeSubpath()
                    painter.drawPath(path)
                    painter.fillPath(path, brush)

                elif kind == "circle":
                    painter.drawEllipse(sx - 3, y_base - 3, 6, 6)

                elif kind == "square":
                    painter.drawRect(sx - 3, y_base - 3, 6, 6)

                elif kind == "diamond":
                    pts = [
                        QPointF(sx, y_base - 4),
                        QPointF(sx + 4, y_base),
                        QPointF(sx, y_base + 4),
                        QPointF(sx - 4, y_base),
                    ]
                    path = QPainterPath()
                    path.moveTo(pts[0])
                    path.lineTo(pts[1])
                    path.lineTo(pts[2])
                    path.lineTo(pts[3])
                    path.closeSubpath()
                    painter.drawPath(path)

        # unknown 也统一画在同一侧（小三角）
        n_u = len(unknown)
        if n_u:
            start_x = x_pos - (n_u - 1) * h_step / 2
            for i, _k in enumerate(unknown):
                sx = start_x + i * h_step
                pts = [QPointF(sx, y_base - 4), QPointF(sx - 4, y_base + 2.4), QPointF(sx + 4, y_base + 2.4)]
                path = QPainterPath()
                path.moveTo(pts[0])
                path.lineTo(pts[1])
                path.lineTo(pts[2])
                path.closeSubpath()
                painter.drawPath(path)
    def has_connection(self):
        return len(self.connections) > 0

    def get_connection(self):
        return self.connections[0] if self.connections else None

    def get_turn_distance(self):
        if self.manual_turn_distance is not None:
            return self.manual_turn_distance
        base_distance = 50
        increment = 7
        return base_distance + (self.index * increment)

    def get_bypass_offset(self):
        if self.manual_bypass_y is not None:
            if self.parent_node:
                start_node_top = self.parent_node.scenePos().y() - self.parent_node.height / 2
                return start_node_top - self.manual_bypass_y
            else:
                return self.scenePos().y() - 10 - self.manual_bypass_y
        base_offset = 50
        increment = 7
        return base_offset + (self.index * increment)

    def get_reverse_h_extend(self):
        if self.manual_reverse_h_extend is not None:
            return self.manual_reverse_h_extend
        base_extend = 50
        increment = 7
        return base_extend + (self.index * increment)
    
    def get_signals(self):
        return self.signals

    def _format_signal_text(self):
            # 1) 规范化 signals 为列表
            signals = self.signals if isinstance(self.signals, (list, tuple, set)) else [self.signals]
            signals = [str(s).lower() for s in signals if s not in (None, "")]

            if not signals:
                return "信号类型：无"

            # 2) 映射到你想显示的名字
            name_map = {
                "level":        "★ Level（幅度）实线",
                "phase":        "● Phase（相位）虚线",
                "bool":         "■ Bool（布尔）",
                "differential": "◆ Differential（差分）点划线",
            }

            pretty = [name_map.get(s, s) for s in signals]

            # 3) 你想要的格式（示例：多行）
            return "信号类型：\n- " + "\n- ".join(pretty)

    def _build_tooltip(self):
        node_name = self.parent_node.name if self.parent_node else getattr(self, "name", "Port")
        port_label = f"{self.port_type}{self.index + 1}"
        return f"{node_name} {port_label}\n{self._format_signal_text()}"

    def _update_tooltip(self):
        self.setToolTip(self._build_tooltip())

    def hoverEnterEvent(self, event):
        self._update_tooltip()
        QToolTip.showText(event.screenPos(), self.toolTip())
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        QToolTip.hideText()
        super().hoverLeaveEvent(event)
    
class NodeItem(QGraphicsItem):
    def __init__(self, name, component_name, index, position, num_inputs, num_outputs):
        super().__init__()
        self.name = name
        self.width = 140
        self.height = 180
        self.component_name = component_name
        self.display_name = f"{self.component_name}{index + 1}"
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs_signals = []
        self.outputs_signals = []
        self.setPos(position)

        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.in_ports = []
        self.out_ports = []
        self.edges = []
        self._special_method_args = {}
        self._pending_cache_state = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.activate_parameter_editor():
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def activate_parameter_editor(self) -> bool:
        """Open this node's parameter UI through the integrated or modal path."""
        if _dispatch_param_open(self):
            return True
        if not self.param_schema() and not self.special_methods_schema():
            return False
        self.open_param_dialog()
        return True

    def param_schema(self) -> list[dict]:
        return []
    
    def get_params(self) -> dict:
        return {}
    
    def set_params(self, params: dict) -> None:
        pass

    def special_methods_schema(self) -> list[dict]:
        return []

    def _stage_param_cache_update(self, params: dict) -> None:
        if not isinstance(params, dict) or not params:
            self._pending_cache_state = None
            return
        previous = {}
        current = getattr(self, "_params", None)
        if not isinstance(current, dict):
            self._pending_cache_state = None
            return
        for key, value in params.items():
            previous[key] = current.get(key, _CACHE_MISSING)
            current[key] = value
        self._pending_cache_state = ("params", previous)

    def _stage_special_method_cache_update(self, method_name: str, args: dict) -> None:
        if not method_name:
            self._pending_cache_state = None
            return
        previous = self._special_method_args.get(method_name, _CACHE_MISSING)
        self._special_method_args[method_name] = dict(args or {})
        self._pending_cache_state = ("special_method", method_name, previous)

    def _commit_pending_cache_update(self) -> None:
        self._pending_cache_state = None

    def _rollback_pending_cache_update(self) -> None:
        pending = self._pending_cache_state
        self._pending_cache_state = None
        if not pending:
            return
        kind = pending[0]
        if kind == "params":
            previous = pending[1]
            current = getattr(self, "_params", None)
            if not isinstance(current, dict):
                return
            for key, old_value in previous.items():
                if old_value is _CACHE_MISSING:
                    current.pop(key, None)
                else:
                    current[key] = old_value
            return
        if kind == "special_method":
            method_name = pending[1]
            old_value = pending[2]
            if old_value is _CACHE_MISSING:
                self._special_method_args.pop(method_name, None)
            else:
                self._special_method_args[method_name] = old_value

    def apply_special_method(self, method_name: str, args: dict) -> None:
        self._stage_special_method_cache_update(method_name, args)
        self._notify_param_change({"__special_method__": method_name, "args": args})

    def _notify_param_change(self, params: dict) -> None:
        if params:
            _dispatch_param_apply(self, params)

    def open_param_dialog(self):
        schema = self.param_schema()
        special_methods = self.special_methods_schema()

        if not schema and not special_methods:
            return

        parent = QApplication.activeWindow()
        if schema:
            dig = ParamDialog(schema, self.get_params(), parent=parent, apply_callback=self.set_params)
            dig.exec()
        if special_methods:
            special_dig = SpecialMethodDialog(
                special_methods,
                parent=parent,
                apply_callback=self.apply_special_method,
                initial_values=self._special_method_args,
            )
            special_dig.exec()

    def _create_ports(self):
        self._apply_adaptive_size()

        if self.num_inputs > 0:
            port_spacing_in = self.height / (self.num_inputs + 1)
        if self.num_outputs > 0:
            port_spacing_out = self.height / (self.num_outputs + 1)

        for i in range(self.num_inputs):
            port = PortItem(self, 'in', i, self.inputs_signals[i])
            y_offset = -self.height/2 + port_spacing_in * (i + 1)
            port.setPos(-self.width/2, y_offset)
            self.in_ports.append(port)

        for i in range(self.num_outputs):
            port = PortItem(self, 'out', i, self.outputs_signals[i])
            y_offset = -self.height/2 + port_spacing_out * (i + 1)
            port.setPos(self.width/2, y_offset)
            self.out_ports.append(port)

    def boundingRect(self):
        return QRectF(-self.width/2, -self.height/2, self.width, self.height)

    def _apply_adaptive_size(self):
        max_ports = max(int(self.num_inputs), int(self.num_outputs))

        # 按 max(输入, 输出) 分档，整体尺寸较之前更紧凑。
        if max_ports <= 1:
            self.width = 128
            self.height = 84
        elif max_ports == 2:
            self.width = 128
            self.height = 108
        elif max_ports == 3:
            self.width = 128
            self.height = 132
        elif max_ports == 4:
            self.width = 128
            self.height = 156
        else:
            self.width = 128
            self.height = 180

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_path()
        return super().itemChange(change, value)
    
    def get_num_inputs(self):
        return self.num_inputs
    
    def get_num_outputs(self):
        return self.num_outputs

class ModulePID(NodeItem):
    def __init__(self, component_name, index, position, num_inputs = 2, num_outputs = 1):
        if index == 0:
            name = "PIDC"
        else:
            name = f"PID{index + 1}"
        super().__init__(name, component_name, index, position, num_inputs, num_outputs)
        self.name = name
        self.height = 180
        self.width = 140
        self.component_name = component_name
        self.display_name = f"{self.component_name}{index + 1}"
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["RESET", "IN"]
        self.outputs = ["OUT"]
        self.inputs_display_name = ["关闭", "误差信号"]
        self.outputs_display_name = ["反馈信号"]
        self.inputs_signals = [["bool"], ["level", "phase"]]
        self.outputs_signals = [["level", "differential"]]
        self.maxm = 2
        self.setPos(position)
        self.schema = PID_SCHEMA
        self.free_mode = True
        self._params = {}
        self._init_params()

        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self._create_ports()

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        draw_node_chrome(painter, rect, self.isSelected())

        painter.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)

        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)
        painter.drawText(title_rect, Qt.AlignCenter, self.display_name)

        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")
        
        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 65, port_pos.y() - 8, 57, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")

    def getmaxm(self):
        return self.maxm
  
    def param_schema(self):
        if self.free_mode:
            return [f for f in self.schema if f.get("free", True)]
        return self.schema
    
    def _default_for_field(self, field: dict):
        if "default" in field:
            return field["default"]
        ftype = field.get("type", "str")
        if ftype == "int":
            return 0
        if ftype == "float":
            return 0.0
        if ftype == "bool":
            return False
        return ""

    def _init_params(self):
        for field in self.schema:
            key = field.get("key")
            if key not in self._params:
                self._params[key] = self._default_for_field(field)

    def get_params(self):
        params = {}
        for field in self.param_schema():
            key = field.get("key")
            params[key] = self._params.get(key, self._default_for_field(field))
        return params

    def set_params(self, params: dict) -> None:
        if not params:
            return
        self._stage_param_cache_update(params)
        self._notify_param_change(params)

class ModuleAccumulator(NodeItem):
    def __init__(self, component_name, index, position, num_inputs = 5, num_outputs = 2):
        if index == 0:
            name = "ACCM"
        else:
            name = f"ACC{index + 1}"
        super().__init__(name, component_name, index, position, num_inputs, num_outputs)
        self.name = name
        self.height = 180
        self.width = 140
        self.component_name = component_name
        self.display_name = f"{self.component_name}{index + 1}"
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["ERROR_IN", "BIAS_IN", "RESET", "PAUSE", "LF_RESET"]
        self.outputs = ["SLOW_OUT", "FAST_OUT"]
        self.inputs_display_name = ["误差信号", "频率偏置", "关闭", "暂停", "关闭锁相环PID"]
        self.outputs_display_name = ["分频输出", "默认输出"]
        self.inputs_signals = [["level", "phase"], ["differential"], ["bool"], ["bool"], ["bool"]]
        self.outputs_signals = [["level", "phase"], ["level", "phase"]]
        self.maxm = 2
        self.setPos(position)
        self.free_mode = True
        self.schema = ACCM_SCHEMA
        self._params = {}
        self._init_params()

        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self._create_ports()

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        draw_node_chrome(painter, rect, self.isSelected())

        painter.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)

        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)
        painter.drawText(title_rect, Qt.AlignCenter, self.display_name)
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")
        
        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 80, port_pos.y() - 8, 72, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")

    def getmaxm(self):
        return self.maxm
  
    def param_schema(self):
        if self.free_mode:
            return [f for f in self.schema if f.get("free", True)]
        return self.schema
    
    def _default_for_field(self, field: dict):
        if "default" in field:
            return field["default"]
        ftype = field.get("type", "str")
        if ftype == "int":
            return 0
        if ftype == "float":
            return 0.0
        if ftype == "bool":
            return False
        return ""

    def _init_params(self):
        for field in self.schema:
            key = field.get("key")
            if key not in self._params:
                self._params[key] = self._default_for_field(field)

    def get_params(self):
        params = {}
        for field in self.param_schema():
            key = field.get("key")
            params[key] = self._params.get(key, self._default_for_field(field))
        return params

    def set_params(self, params: dict) -> None:
        if not params:
            return
        self._stage_param_cache_update(params)
        self._notify_param_change(params)

class ModuleBase(NodeItem):
    def __init__(self, component_name, index, position, num_inputs = 2, num_outputs = 1):
        if component_name == "三角函数运算器":
            if index == 0:
                name = "TRIG"
            else:
                name = f"TRI{index + 1}"
            super().__init__(name, component_name, index, position, 1, 2)
            self.num_inputs = 1
            self.num_outputs = 2
        elif component_name == "反三角函数运算器":
            if index == 0:
                name = "ATAN"
            else:
                name = f"ATA{index + 1}"
            super().__init__(name, component_name, index, position, 2, 1)
            self.num_inputs = 2
            self.num_outputs = 1
        elif component_name == "混频器":
            if index == 0:
                name = "MIXR"
            else:
                name = f"MIX{index + 1}"
            super().__init__(name, component_name, index, position, 2, 1)
            self.num_inputs = 2
            self.num_outputs = 1
        elif component_name == "解卷绕器":
            name = "UNWR"
            super().__init__(name, component_name, index, position, 1, 1)
            self.num_inputs = 1
            self.num_outputs = 1
        self.name = name
        self.height = 180
        self.width = 140
        self.component_name = component_name
        self.display_name = f"{self.component_name}{index + 1}"
        self.index = index
        if component_name == "三角函数运算器":
            self.inputs = ["IN"]
            self.outputs = ["SIN", "COS"]
            self.inputs_display_name = ["相位输入"]
            self.outputs_display_name = ["正弦输出", "余弦输出"]
            self.inputs_signals = [["phase"]]
            self.outputs_signals = [["level"], ["level"]]
            self.maxm = 2
        elif component_name == "反三角函数运算器":
            self.inputs = ["SIN", "COS"]
            self.outputs = ["OUT"]
            self.inputs_display_name = ["正弦输入", "余弦输入"]
            self.outputs_display_name = ["相位输出"]
            self.inputs_signals = [["level"], ["level"]]
            self.outputs_signals = [["phase"]]
            self.maxm = 2
        elif component_name == "混频器":
            self.inputs = ["IN_A", "IN_B"]
            self.outputs = ["OUT"]
            self.inputs_display_name = ["输入A", "输入B"]
            self.outputs_display_name = ["混频输出"]
            self.inputs_signals = [["level"], ["level"]]
            self.outputs_signals = [["level", "differential"]]
            self.maxm = 4
        elif component_name == "解卷绕器":
            self.inputs = ["IN"]
            self.outputs = ["OUT"]
            self.inputs_display_name = ["相位输入"]
            self.outputs_display_name = ["相位输出"]
            self.inputs_signals = [["phase"]]
            self.outputs_signals = [["phase"]]
            self.maxm = 1
        self.setPos(position)

        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self._create_ports()

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        draw_node_chrome(painter, rect, self.isSelected())
        
        painter.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)

        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)
        painter.drawText(title_rect, Qt.AlignCenter, self.display_name)
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            if self.component_name == "三角函数运算器":
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")
            elif self.component_name == "反三角函数运算器":
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")
            elif self.component_name == "混频器":
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")
            elif self.component_name == "解卷绕器":
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")
        
        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 60, port_pos.y() - 8, 52, 16)
            if self.component_name == "三角函数运算器":
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")
            elif self.component_name == "反三角函数运算器":
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")
            elif self.component_name == "混频器":
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")
            elif self.component_name == "解卷绕器":
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")


    def getmaxm(self):
        return self.maxm

class ModuleScaler(NodeItem):
    def __init__(self, component_name, index, position, num_inputs = 1, num_outputs = 1):
        if index == 0:
            name = "SCLR"
        else:
            name = f"SCL{index + 1}"
        super().__init__(name, component_name, index, position, num_inputs, num_outputs)
        self.name = name
        self.height = 180
        self.width = 140
        self.component_name = component_name
        self.display_name = f"{self.component_name}{index + 1}"
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["IN"]
        self.outputs = ["OUT"]
        self.inputs_display_name = ["信号输入"]
        self.outputs_display_name = ["信号输出"]
        self.inputs_signals = [["level", "phase", "differential"]]
        self.outputs_signals = [["level", "phase", "differential"]]
        self.maxm = 4
        self.setPos(position)
        self.schema = SCLR_SCHEMA
        self.free_mode = True
        self._params = {}
        self._init_params()

        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self._create_ports()

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        draw_node_chrome(painter, rect, self.isSelected())
        
        painter.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        
        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)
        painter.drawText(title_rect, Qt.AlignCenter, self.display_name)
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 60, port_pos.y() - 8, 52, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")

    def getmaxm(self):
        return self.maxm
  
    def param_schema(self):
        if self.free_mode:
            return [f for f in self.schema if f.get("free", True)]
        return self.schema
    
    def _default_for_field(self, field: dict):
        if "default" in field:
            return field["default"]
        ftype = field.get("type", "str")
        if ftype == "int":
            return 0
        if ftype == "float":
            return 0.0
        if ftype == "bool":
            return False
        return ""

    def _init_params(self):
        for field in self.schema:
            key = field.get("key")
            if key not in self._params:
                self._params[key] = self._default_for_field(field)

    def get_params(self):
        params = {}
        for field in self.param_schema():
            key = field.get("key")
            params[key] = self._params.get(key, self._default_for_field(field))
        return params

    def set_params(self, params: dict) -> None:
        if not params:
            return
        self._stage_param_cache_update(params)
        self._notify_param_change(params)

class ModuleFIRFilter(NodeItem):
    def __init__(self, component_name, index, position, num_inputs = 1, num_outputs = 1):
        if index == 0:
            name = "FIRF"
        else:
            name = f"FIR{index + 1}"
        super().__init__(name, component_name, index, position, num_inputs, num_outputs)
        self.name = name
        self.height = 180
        self.width = 140
        self.component_name = component_name
        self.display_name = f"{self.component_name}{index + 1}"
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["IN"]
        self.outputs = ["OUT"]
        self.inputs_display_name = ["信号输入"]
        self.outputs_display_name = ["信号输出"]
        self.inputs_signals = [["level", "differential"]]
        self.outputs_signals = [["level", "differential"]]
        self.maxm = 4
        self.setPos(position)
        self.schema = FIRF_SCHEMA
        self.free_mode = True
        self._params = {}
        self._init_params()

        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self._create_ports()

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        draw_node_chrome(painter, rect, self.isSelected())

        painter.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        
        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)
        painter.drawText(title_rect, Qt.AlignCenter, self.display_name)
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 60, port_pos.y() - 8, 52, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")

    def getmaxm(self):
        return self.maxm
  
    def param_schema(self):
        if self.free_mode:
            return [f for f in self.schema if f.get("free", True)]
        return self.schema
    
    def _default_for_field(self, field: dict):
        if "default" in field:
            return field["default"]
        ftype = field.get("type", "str")
        if ftype == "int":
            return 0
        if ftype == "float":
            return 0.0
        if ftype == "bool":
            return False
        return ""

    def _init_params(self):
        for field in self.schema:
            key = field.get("key")
            if key not in self._params:
                self._params[key] = self._default_for_field(field)

    def get_params(self):
        params = {}
        for field in self.param_schema():
            key = field.get("key")
            params[key] = self._params.get(key, self._default_for_field(field))
        return params

    def set_params(self, params: dict) -> None:
        if not params:
            return
        self._stage_param_cache_update(params)
        self._notify_param_change(params)

    def special_methods_schema(self):
        return [
            {
                "name": "design_lowpass",
                "label": "低通滤波器设计",
                "params": [
                    {"key": "freq_pass", "label": "通带截止频率(Hz)", "type": "float", "min": 0.0, "max": 1e12, "default": 1e6, "decimals": 3, "unit": "Hz"},
                    {"key": "freq_stop", "label": "阻带截止频率(Hz)", "type": "float", "min": 0.0, "max": 1e12, "default": 10e6, "decimals": 3, "unit": "Hz"},
                    {"key": "freq_sample", "label": "采样频率(Hz)", "type": "float", "min": 1.0, "max": 1e12, "default": 250e6, "decimals": 3, "unit": "Hz"},
                    {"key": "weight", "label": "阻带权重", "type": "float", "min": 1e-6, "max": 1e6, "default": 1.0, "decimals": 6},
                    {"key": "taps", "label": "抽头数", "type": "choice", "default": 64, "options": [16, 32, 64]},
                ],
            }
        ]

class ModuleLinerTransformer(NodeItem):
    def __init__(self, component_name, index, position, num_inputs = 2, num_outputs = 2):
        if index == 0:
            name = "LTRN"
        else:
            name = f"LTR{index + 1}"
        super().__init__(name, component_name, index, position, num_inputs, num_outputs)
        self.name = name
        self.height = 180
        self.width = 140
        self.component_name = component_name
        self.display_name = f"{self.component_name}{index + 1}"
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["IN_A", "IN_B"]
        self.outputs = ["OUT_A", "OUT_B"]
        self.inputs_display_name = ["输入A", "输入B"]
        self.outputs_display_name = ["输出A", "输出B"]
        self.inputs_signals = [["level", "differential"], ["level", "differential"]]
        self.outputs_signals = [["level", "differential"], ["level", "differential"]]
        self.maxm = 2
        self.setPos(position)
        self.schema = LTRN_SCHEMA
        self.free_mode = True
        self._params = {}
        self._init_params()
        
        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self._create_ports()

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        draw_node_chrome(painter, rect, self.isSelected())
        painter.setPen(Qt.white)

        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)

        painter.drawText(title_rect, Qt.AlignCenter, self.display_name)
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 80, port_pos.y() - 8, 72, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")

    def getmaxm(self):
        return self.maxm
  
    def param_schema(self):
        if self.free_mode:
            return [f for f in self.schema if f.get("free", True)]
        return self.schema
    
    def _default_for_field(self, field: dict):
        if "default" in field:
            return field["default"]
        ftype = field.get("type", "str")
        if ftype == "int":
            return 0
        if ftype == "float":
            return 0.0
        if ftype == "bool":
            return False
        return ""

    def _init_params(self):
        for field in self.schema:
            key = field.get("key")
            if key not in self._params:
                self._params[key] = self._default_for_field(field)

    def get_params(self):
        params = {}
        for field in self.param_schema():
            key = field.get("key")
            params[key] = self._params.get(key, self._default_for_field(field))
        return params

    def set_params(self, params: dict) -> None:
        if not params:
            return
        self._stage_param_cache_update(params)
        self._notify_param_change(params)

class ModulePDHFSM(NodeItem):
    def __init__(self, component_name, index,position, num_inputs = 2, num_outputs = 3):
        name = "PDHS"
        super().__init__(name, component_name, index, position, num_inputs, num_outputs)
        self.name = name
        self.height = 180
        self.width = 140
        self.component_name = component_name
        self.display_name = f"{self.component_name}{index + 1}"
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["POWER", "SCAN"]
        self.outputs = ["PID_RESET_CTRL", "MIXER_RESET_CTRL", "SCAN_RESET_CTRL"]
        self.inputs_display_name = ["功率输入", "扫描信号"]
        self.outputs_display_name = ["关闭PID", "关闭混频器", "暂停扫描"]
        self.inputs_signals = [["level"], ["level"]]
        self.outputs_signals = [["bool"], ["bool"], ["bool"]]
        self.maxm = 1
        self.setPos(position)
        self.schema = PDH_SCHEMA
        self.free_mode = True
        self._params = {}
        self._init_params()

        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self._create_ports()

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        draw_node_chrome(painter, rect, self.isSelected())
        painter.setPen(Qt.white)

        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)

        painter.drawText(title_rect, Qt.AlignCenter, self.display_name)
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 110, port_pos.y() - 8, 100, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")

    def getmaxm(self):
        return self.maxm
  
    def param_schema(self):
        if self.free_mode:
            return [f for f in self.schema if f.get("free", True)]
        return self.schema
    
    def _default_for_field(self, field: dict):
        if "default" in field:
            return field["default"]
        ftype = field.get("type", "str")
        if ftype == "int":
            return 0
        if ftype == "float":
            return 0.0
        if ftype == "bool":
            return False
        return ""

    def _init_params(self):
        for field in self.schema:
            key = field.get("key")
            if key not in self._params:
                self._params[key] = self._default_for_field(field)

    def get_params(self):
        params = {}
        for field in self.param_schema():
            key = field.get("key")
            params[key] = self._params.get(key, self._default_for_field(field))
        return params

    def set_params(self, params: dict) -> None:
        if not params:
            return
        self._stage_param_cache_update(params)
        self._notify_param_change(params)
# 在 ModuleFIRFilter 类之后添加

class ModuleIIRFilter(NodeItem):
    def __init__(self, component_name, index, position, num_inputs = 1, num_outputs = 1):
        if index == 0:
            name = "IIRF"
        else:
            name = f"IIR{index + 1}"
        super().__init__(name, component_name, index, position, num_inputs, num_outputs)
        self.name = name
        self.height = 180
        self.width = 140
        self.component_name = component_name
        self.display_name = f"{self.component_name}{index + 1}"
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["IN"]
        self.outputs = ["OUT"]
        self.inputs_display_name = ["信号输入"]
        self.outputs_display_name = ["信号输出"]
        self.inputs_signals = [["level", "differential"]]
        self.outputs_signals = [["level", "differential"]]
        self.maxm = 4
        self.setPos(position)
        self.schema = IIR_SCHEMA
        self.free_mode = True
        self._params = {}
        self._init_params()

        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self._create_ports()

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        draw_node_chrome(painter, rect, self.isSelected())

        painter.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        
        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)
        painter.drawText(title_rect, Qt.AlignCenter, self.display_name)
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 60, port_pos.y() - 8, 52, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")

    def getmaxm(self):
        return self.maxm
  
    def param_schema(self):
        if self.free_mode:
            return [f for f in self.schema if f.get("free", True)]
        return self.schema
    
    def _default_for_field(self, field: dict):
        if "default" in field:
            return field["default"]
        ftype = field.get("type", "str")
        if ftype == "int":
            return 0
        if ftype == "float":
            return 0.0
        if ftype == "bool":
            return False
        return ""

    def _init_params(self):
        for field in self.schema:
            key = field.get("key")
            if key not in self._params:
                self._params[key] = self._default_for_field(field)

    def get_params(self):
        params = {}
        for field in self.param_schema():
            key = field.get("key")
            params[key] = self._params.get(key, self._default_for_field(field))
        return params

    def set_params(self, params: dict) -> None:
        if not params:
            return
        self._stage_param_cache_update(params)
        self._notify_param_change(params)

    def special_methods_schema(self):
        return [
            {
                "name": "design_lowpass",
                "label": "低通滤波器设计",
                "params": [
                    {"key": "filter_type", "label": "滤波器类型", "type": "choice", "default": "butter", "options": ["butter", "ellip", "cheby1", "cheby2", "bessel"]},
                    {"key": "freq_pass", "label": "通带截止频率(Hz)", "type": "float", "min": 0.0, "max": 1e12, "default": 1e6, "decimals": 3, "unit": "Hz"},
                    {"key": "freq_sample", "label": "采样频率(Hz)", "type": "float", "min": 1.0, "max": 1e12, "default": 250e6, "decimals": 3, "unit": "Hz"},
                ],
            }
        ]
        
class ModuleSCLOFSM(NodeItem):
    def __init__(self, component_name, index, position, num_inputs = 1, num_outputs = 2):
        if index:
            name = f"SLO{index + 1}"
        else:
            name = "SCLO"
        super().__init__(name, component_name, index, position, num_inputs, num_outputs)
        self.name = name
        self.height = 180
        self.width = 140
        self.component_name = component_name
        self.display_name = f"{self.component_name}{index + 1}"
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["PHASE_IN"]
        self.outputs = ["BIAS_OUT", "PID_RESET_CTRL"]
        self.inputs_display_name = ["相位输入"]
        self.outputs_display_name = ["频率偏置", "关闭PID"]
        self.inputs_signals = [["phase"]]
        self.outputs_signals = [["differential"], ["bool"]]
        self.maxm = 2
        self.setPos(position)
        self.schema = SCLO_SCHEMA
        self.free_mode = True
        self._params = {}
        self._init_params()

        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self._create_ports()

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        draw_node_chrome(painter, rect, self.isSelected())
        painter.setPen(Qt.white)

        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)

        painter.drawText(title_rect, Qt.AlignCenter, self.display_name)
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.inputs_display_name[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 100, port_pos.y() - 8, 90, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.outputs_display_name[i]}")

    def getmaxm(self):
        return self.maxm
  
    def param_schema(self):
        if self.free_mode:
            return [f for f in self.schema if f.get("free", True)]
        return self.schema
    
    def _default_for_field(self, field: dict):
        if "default" in field:
            return field["default"]
        ftype = field.get("type", "str")
        if ftype == "int":
            return 0
        if ftype == "float":
            return 0.0
        if ftype == "bool":
            return False
        return ""

    def _init_params(self):
        for field in self.schema:
            key = field.get("key")
            if key not in self._params:
                self._params[key] = self._default_for_field(field)

    def get_params(self):
        params = {}
        for field in self.param_schema():
            key = field.get("key")
            params[key] = self._params.get(key, self._default_for_field(field))
        return params

    def set_params(self, params: dict) -> None:
        if not params:
            return
        self._stage_param_cache_update(params)
        self._notify_param_change(params)


class ModuleConstantBool(NodeItem):
    def __init__(self, component_name, index, position, num_inputs=0, num_outputs=1):
        base_name = "HIGH" if component_name == "布尔值：是" else "LOW"
        name = base_name
        super().__init__(name, component_name, index, position, 0, 1)
        self.name = name
        self.component_name = component_name
        self.display_name = "布尔值：是" if base_name == "HIGH" else "布尔值：否"
        self.index = index
        self.num_inputs = 0
        self.num_outputs = 1
        self.inputs = []
        self.outputs = [base_name]
        self.inputs_display_name = []
        self.outputs_display_name = [self.display_name]
        self.inputs_signals = []
        self.outputs_signals = [["bool"]]
        self.maxm = -1
        self.free_mode = True
        self.setPos(position)

        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self._create_ports()

    def _apply_adaptive_size(self):
        self.width = 74
        self.height = 52

    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        draw_node_chrome(painter, rect, self.isSelected())

        painter.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.display_name)

    def getmaxm(self):
        return self.maxm

class CompositeModule:

    sub_modules = []
    auto_edges = []

    @classmethod
    def create_sub_modules(cls, scene, position, alloc_index_func, connect_func=None):
        created_nodes = []
        for sub_name, offset in cls.sub_modules:
            module_cls = module_factory.get(sub_name)
            if module_cls:
                idx = alloc_index_func(sub_name)
                if idx is None:
                    print(f"❌ 超出 {sub_name} 模块数量上限")
                    continue
                sub_position = position + offset
                node = module_cls(sub_name, idx, sub_position)
                scene.addItem(node)
                created_nodes.append(node)
                if hasattr(node, "free_mode"):
                    node.free_mode = not getattr(scene, "developer_mode", False)

        if connect_func and created_nodes and cls.auto_edges:
            for edge_spec in cls.auto_edges:
                if not isinstance(edge_spec, (tuple, list)) or len(edge_spec) != 4:
                    print(f"⚠️ 跳过无效自动连线配置: {edge_spec}")
                    continue

                src_node_idx, src_out_idx, dst_node_idx, dst_in_idx = edge_spec

                if not (0 <= src_node_idx < len(created_nodes)) or not (0 <= dst_node_idx < len(created_nodes)):
                    print(f"⚠️ 自动连线节点索引越界: {edge_spec}")
                    continue

                src_node = created_nodes[src_node_idx]
                dst_node = created_nodes[dst_node_idx]

                if not (0 <= src_out_idx < len(src_node.out_ports)):
                    print(f"⚠️ 自动连线输出端口索引越界: {edge_spec}")
                    continue

                if not (0 <= dst_in_idx < len(dst_node.in_ports)):
                    print(f"⚠️ 自动连线输入端口索引越界: {edge_spec}")
                    continue

                src_port = src_node.out_ports[src_out_idx]
                dst_port = dst_node.in_ports[dst_in_idx]
                if not connect_func(src_port, dst_port):
                    print(f"⚠️ 自动连线失败: {src_node.name}.Out{src_out_idx + 1} -> {dst_node.name}.In{dst_in_idx + 1}")

        return created_nodes

class SINGenerator(CompositeModule):

    sub_modules = [
        ("累加器", QPointF(0, 0)),
        ("三角函数运算器", QPointF(200, 0)),
    ]
    auto_edges = [
        # 累加器默认输出 -> 三角函数运算器相位输入
        (0, 1, 1, 0),
    ]

class DigitalControlledOscillator(CompositeModule):

    sub_modules = [
        ("累加器", QPointF(0, 0)),
        ("三角函数运算器", QPointF(200, -150)),
        ("三角函数运算器", QPointF(200, 150)),
    ]

module_factory = {
    "PID控制器": ModulePID,
    "累加器": ModuleAccumulator,
    "布尔值：是": ModuleConstantBool,
    "布尔值：否": ModuleConstantBool,
    "三角函数运算器": ModuleBase,
    "反三角函数运算器": ModuleBase,
    "线性缩放器": ModuleScaler,
    "FIR滤波器": ModuleFIRFilter,
    "IIR滤波器": ModuleIIRFilter,
    "线性变换器": ModuleLinerTransformer,
    "混频器": ModuleBase,
    "解卷绕器": ModuleBase,
    "PDH状态机": ModulePDHFSM,
    "LO自动校准状态机": ModuleSCLOFSM,
}

module_maxm = {
    "PID控制器": 2,
    "累加器": 2,
    "布尔值：是": -1,
    "布尔值：否": -1,
    "三角函数运算器": 4,
    "反三角函数运算器": 2,
    "线性缩放器": 4,
    "FIR滤波器": 4,
    "IIR滤波器": 4,
    "线性变换器": 2,
    "混频器": 4,
    "解卷绕器": 1,
    "PDH状态机": 1,
    "LO自动校准状态机": 2,
}

composite_modules = {
    "正弦波发生器": SINGenerator,
    "数字控制振荡器": DigitalControlledOscillator,
    # 可以添加更多组合模块
}
