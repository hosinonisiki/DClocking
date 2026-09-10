"""Reusable quantity-aware Qt line editor."""

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit

from quantity_entry_core import QuantityEntryCore, QuantityFormat

__all__ = ["QuantityLineEdit"]


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
                special_values=tuple(field.get("special_values", ())),
            )
        digits_limit = field.get("digits_limit")
        if digits_limit is not None:
            int_limit, frac_limit, min_frac = digits_limit
            return QuantityFormat(
                digits_limit=(int(int_limit), int(frac_limit), int(min_frac)),
                prefix=cls._prefix_map_for_field(field),
                unit=unit,
                special_values=tuple(field.get("special_values", ())),
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
            special_values=tuple(field.get("special_values", ())),
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
