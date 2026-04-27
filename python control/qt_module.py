from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QListWidget, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem,
                               QSplitter, QGraphicsEllipseItem, QDialog, QFormLayout,
                               QSpinBox, QDoubleSpinBox, QLineEdit,
                               QCheckBox, QPushButton, QToolTip, QComboBox, QMessageBox, QLabel)
# 导入PySide6的QtCore模块中的相关类
from PySide6.QtCore import Qt, QMimeData, QPointF, QRectF, Signal, QObject, QByteArray, QPoint
# 导入PySide6.QtGui模块中的相关类
from PySide6.QtGui import QDrag, QPainter, QPen, QBrush, QPainterPath, QColor, QFont, QPixmap, QImage, QCursor
import math
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from qt_module_schema import PID_SCHEMA, ACCM_SCHEMA, SCLR_SCHEMA, FIRF_SCHEMA, LTRN_SCHEMA, PDH_SCHEMA, SCLO_SCHEMA, IIR_SCHEMA
from quantity_entry_core import QuantityEntryCore, QuantityFormat

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 110)
        self.setFixedHeight(125)

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
        painter.drawText(QRectF(rect.left() + 10, rect.top() + 6, rect.width() - 20, 18), Qt.AlignLeft | Qt.AlignVCenter, "PID Schematic")

        body_font = QFont()
        body_font.setPointSize(6)
        painter.setFont(body_font)
        painter.setPen(QColor("#8A94A6"))

        plot_rect = QRectF(rect.left() + 18, rect.top() + 26, rect.width() - 36, rect.height() - 40)
        painter.setPen(QPen(QColor("#D7DCE4"), 1))
        painter.drawRoundedRect(plot_rect, 6, 6)

        x0 = plot_rect.left() + 14
        x1 = plot_rect.left() + plot_rect.width() * 0.26
        x2 = plot_rect.left() + plot_rect.width() * 0.48
        x3 = plot_rect.left() + plot_rect.width() * 0.72
        x4 = plot_rect.right() - 14

        y_high = plot_rect.top() + 14
        y_mid = plot_rect.center().y() + 2

        painter.setPen(QPen(QColor("#2F6BFF"), 3))
        painter.drawLine(QPointF(x0, y_high), QPointF(x1, y_high))
        painter.drawLine(QPointF(x1, y_high), QPointF(x2, y_mid))
        painter.drawLine(QPointF(x2, y_mid), QPointF(x3, y_mid))
        painter.drawLine(QPointF(x3, y_mid), QPointF(x4, y_high))

        painter.setPen(QPen(QColor("#AAB4C2"), 1, Qt.DashLine))
        painter.drawLine(QPointF(plot_rect.left() + 6, y_high), QPointF(x1, y_high))
        painter.drawLine(QPointF(plot_rect.left() + 6, y_mid), QPointF(x3, y_mid))
        painter.drawLine(QPointF(x1, y_high), QPointF(x1, plot_rect.bottom() - 6))
        painter.drawLine(QPointF(x2, y_mid), QPointF(x2, plot_rect.bottom() - 6))
        painter.drawLine(QPointF(x3, y_mid), QPointF(x3, plot_rect.bottom() - 6))

        painter.setPen(QColor("#5C6678"))
        painter.drawText(QRectF(x0 - 4, y_high - 16, 54, 12), Qt.AlignLeft | Qt.AlignVCenter, "饱和增益")
        painter.drawText(QRectF((x2 + x3) / 2 - 14, y_mid - 16, 28, 12), Qt.AlignCenter | Qt.AlignVCenter, "增益")

        painter.drawText(QRectF(x1 - 32, plot_rect.bottom() - 4, 64, 12), Qt.AlignCenter | Qt.AlignVCenter, "饱和拐点频率")
        painter.drawText(QRectF(x2 - 16, plot_rect.bottom() - 16, 32, 12), Qt.AlignCenter | Qt.AlignVCenter, "PI拐点")
        painter.drawText(QRectF(x3 - 16, plot_rect.bottom() - 16, 32, 12), Qt.AlignCenter | Qt.AlignVCenter, "PD拐点")

        painter.setPen(QColor("#8A94A6"))
        painter.drawText(QRectF(plot_rect.left(), plot_rect.bottom() + 2, plot_rect.width(), 10), Qt.AlignCenter | Qt.AlignVCenter, "Frequency")
        painter.save()
        painter.translate(plot_rect.left() - 7, plot_rect.center().y())
        painter.rotate(-90)
        painter.drawText(QRectF(-plot_rect.height() / 2, -16, plot_rect.height(), 10), Qt.AlignCenter | Qt.AlignVCenter, "Gain")
        painter.restore()
        painter.end()

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

        for key in self._editors.keys():
            try:
                self._committed_values[key] = self._value_from_editor(key)
            except Exception:
                continue

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

        self._enter_committed_keys.clear()

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
        painter.setPen(QPen(Qt.white, 1))
        painter.drawEllipse(-self.radius, -self.radius, 2*self.radius, 2*self.radius)

        # draw the outward short wire from the port center
        painter.save()
        line_pen = QPen(QColor(self.line_color) if self.line_color else Qt.gray, 2)
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
            if _dispatch_param_open(self):
                event.accept()
                return
            self.open_param_dialog()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

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
        painter.setBrush(QBrush(QColor("#2C3E50")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRoundedRect(rect, 8, 8)

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
        painter.setBrush(QBrush(QColor("#2C3E50")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRoundedRect(rect, 8, 8)

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
        painter.setBrush(QBrush(QColor("#2C3E50")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRoundedRect(rect, 8, 8)
        
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
        painter.setBrush(QBrush(QColor("#2C3E50")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRoundedRect(rect, 8, 8)
        
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
        painter.setBrush(QBrush(QColor("#2C3E50")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRoundedRect(rect, 8, 8)

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
        painter.setBrush(QBrush(QColor("#2C3E50")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRoundedRect(rect, 8, 8)
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
        painter.setBrush(QBrush(QColor("#2C3E50")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRoundedRect(rect, 8, 8)
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
        painter.setBrush(QBrush(QColor("#2C3E50")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRoundedRect(rect, 8, 8)

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
        painter.setBrush(QBrush(QColor("#2C3E50")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRoundedRect(rect, 8, 8)
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
        painter.setBrush(QBrush(QColor("#2C3E50")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRoundedRect(rect, 8, 8)

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
