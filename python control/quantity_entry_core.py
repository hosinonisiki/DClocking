from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import inspect
import re
from typing import Any, Callable


class QuantityFormat:
    """Parse and normalize quantity strings such as ``10MHz`` or ``0.250V``."""

    default_prefix = {
        "m": 1e-3,
        "u": 1e-6,
        "n": 1e-9,
        "p": 1e-12,
        "f": 1e-15,
        "a": 1e-18,
        "k": 1e3,
        "M": 1e6,
        "G": 1e9,
        "T": 1e12,
    }

    def __init__(
        self,
        digits_limit: tuple[int, int, int] = (9, 9, 3),
        prefix: dict[str, float] | None = None,
        unit: str = "",
    ) -> None:
        self.digits_limit = digits_limit
        self.prefix = self.default_prefix if prefix is None else dict(prefix)
        self.unit = unit
        self.re = self._compile_pattern()

    def _compile_pattern(self) -> re.Pattern[str]:
        int_limit, frac_limit, _ = self.digits_limit
        parts = [rf"(?P<sign>-)?(?P<int>[0-9]{{1,{int_limit}}})"]

        if frac_limit > 0:
            parts.append(rf"(?P<frac>\.[0-9]{{1,{frac_limit}}})?")
        else:
            parts.append(r"(?P<frac>)")

        if self.prefix:
            prefix_chars = "".join(re.escape(key) for key in self.prefix)
            parts.append(rf"(?P<prefix>[{prefix_chars}])?")
        else:
            parts.append(r"(?P<prefix>)")

        if self.unit:
            parts.append(rf"(?P<unit>{re.escape(self.unit)})?")
        else:
            parts.append(r"(?P<unit>)")

        return re.compile("^" + "".join(parts) + "$")

    def match(self, text: str) -> tuple[re.Match[str] | None, float | None, str | None]:
        result = self.re.fullmatch(text)
        if result is None:
            return None, None, None

        sign = "-" if result.group("sign") else ""
        integer = result.group("int")
        fraction = result.group("frac") or ""
        prefix = result.group("prefix") or ""

        numeric_text = sign + integer + fraction
        numeric_value = float(numeric_text)
        if prefix:
            numeric_value *= self.prefix[prefix]

        formalized = sign + integer + self._formalize_fraction(fraction) + prefix + self.unit
        return result, numeric_value, formalized

    def _formalize_fraction(self, fraction: str) -> str:
        minimum_fraction_digits = self.digits_limit[2]
        if not fraction:
            return "" if minimum_fraction_digits == 0 else "." + ("0" * minimum_fraction_digits)

        digits = fraction[1:]
        if len(digits) >= minimum_fraction_digits:
            return "." + digits
        return "." + digits + ("0" * (minimum_fraction_digits - len(digits)))

    def break_up(self, formalized: str) -> tuple[bool, str, str]:
        match = re.match(r"(?P<sign>-)?(?P<number>[0-9]+(?:\.[0-9]+)?)", formalized)
        if match is None:
            raise ValueError(f"Unable to split formatted quantity: {formalized!r}")

        integer, dot, fraction = match.group("number").partition(".")
        return match.group("sign") == "-", integer, fraction if dot else ""


@dataclass(frozen=True)
class QuantityEntrySnapshot:
    """Immutable view of the current core state for adapters and debugging."""

    text: str
    stored: str
    state: str
    value: float | None
    formalized: str | None
    selected_index: int | None
    selected_range: tuple[int, int] | None
    enabled: bool


class QuantityEntryCore:
    """GUI-agnostic state machine for quantity entry and digit rolling."""

    UNCHANGED = "unchanged"
    CHANGED = "changed"
    ROLLING = "rolling"

    def __init__(
        self,
        formater: QuantityFormat | None = None,
        report: Callable[..., Any] | None = None,
    ) -> None:
        self.format = QuantityFormat() if formater is None else formater
        self.report = report
        self._report_accepts_core = self._callback_accepts_core(report)

        self.text = ""
        self.stored = ""
        self.state = self.CHANGED
        self.result: re.Match[str] | None = None
        self.value: float | None = None
        self.formalized: str | None = None
        self.enabled = True

        self.selected: int | None = None
        self.minus = False
        self.integer = ""
        self.fraction = ""
        self.quantity = ""
        self.suffix = ""

    @staticmethod
    def _callback_accepts_core(callback: Callable[..., Any] | None) -> bool:
        if callback is None:
            return False
        try:
            signature = inspect.signature(callback)
        except (TypeError, ValueError):
            return True

        for parameter in signature.parameters.values():
            if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
                return True
            if parameter.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                return True
        return False

    def _emit_report(self) -> Any:
        if self.report is None:
            return None
        if self._report_accepts_core:
            return self.report(self)
        return self.report()

    @property
    def selected_range(self) -> tuple[int, int] | None:
        if self.state != self.ROLLING or self.selected is None:
            return None
        offset = 1 if self.minus else 0
        return self.selected + offset, self.selected + offset + 1

    @property
    def visual_state(self) -> str:
        return "disabled" if not self.enabled else self.state

    def snapshot(self) -> QuantityEntrySnapshot:
        return QuantityEntrySnapshot(
            text=self.text,
            stored=self.stored,
            state=self.state,
            value=self.value,
            formalized=self.formalized,
            selected_index=self.selected,
            selected_range=self.selected_range,
            enabled=self.enabled,
        )

    def call(self) -> Any:
        return self._emit_report()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def set_text(self, text: str, *, mark_changed: bool = True) -> None:
        self.text = text
        if self.state == self.ROLLING:
            self._clear_roll_state()
        if mark_changed:
            self.refresh_state()

    def set(self, text: str, *, mark_changed: bool = True) -> None:
        self.set_text(text, mark_changed=mark_changed)

    def get_text(self) -> str:
        return self.text

    def get_value(self) -> float | None:
        return self.value

    def refresh_state(self) -> str:
        if self.state != self.ROLLING:
            self.state = self.UNCHANGED if self.text == self.stored else self.CHANGED
        return self.state

    def store(self) -> bool:
        result, value, formalized = self.format.match(self.text)
        self.result = result
        self.value = value
        self.formalized = formalized
        if result is None:
            self.state = self.CHANGED
            return False

        self.text = formalized
        self.stored = formalized
        self.state = self.UNCHANGED
        self.selected = None
        return True

    def handle_key(self, key: str) -> bool:
        if not self.enabled:
            return True
        if self.state == self.UNCHANGED:
            return self._unchanged_handle_key(key)
        if self.state == self.CHANGED:
            return self._changed_handle_key(key)
        if self.state == self.ROLLING:
            return self._rolling_handle_key(key)
        return False

    def handle_click(self) -> bool:
        if not self.enabled:
            return True
        if self.state == self.ROLLING:
            self.exit_roll()
            return True
        return False

    def enter_roll(self, direction: str) -> bool:
        if not self.enabled or self.formalized is None:
            return False

        self._load_roll_from_formalized()
        if not self.quantity:
            return False

        self.state = self.ROLLING
        self.selected = 0 if direction == "Left" else self._last_digit_index()
        return True

    def exit_roll(self, *, report: bool = True) -> bool:
        self.selected = None
        stored = self.store()
        if report and stored:
            self._emit_report()
        return stored

    def roll(self, key: str) -> bool:
        if self.state != self.ROLLING or self.selected is None:
            return False

        if key == "Left":
            return self._move_left()
        if key == "Right":
            return self._move_right()
        if key == "Up":
            return self._apply_numeric_delta(1)
        if key == "Down":
            return self._apply_numeric_delta(-1)
        return False

    def _unchanged_handle_key(self, key: str) -> bool:
        if key == "Return":
            return True
        if key in {"Left", "Right"}:
            return self.enter_roll(key)
        return False

    def _changed_handle_key(self, key: str) -> bool:
        if key == "Return":
            if self.store():
                self._emit_report()
            return True
        if key in {"Left", "Right"}:
            return True
        return False

    def _rolling_handle_key(self, key: str) -> bool:
        if key == "Return":
            self.exit_roll()
            return True
        if key in {"Up", "Down", "Left", "Right"}:
            return self.roll(key)
        if key in {str(i) for i in range(10)}:
            return True
        return True

    def _clear_roll_state(self) -> None:
        self.selected = None
        self.minus = False
        self.integer = ""
        self.fraction = ""
        self.quantity = ""
        self.suffix = ""

    def _load_roll_from_formalized(self) -> None:
        minus, integer, fraction = self.format.break_up(self.formalized)
        self.minus = minus
        self.integer = integer
        self.fraction = fraction
        self.quantity = integer if not fraction else f"{integer}.{fraction}"
        self.suffix = self._extract_suffix(self.formalized)

    def _extract_suffix(self, formalized: str) -> str:
        match = re.match(r"-?[0-9]+(?:\.[0-9]+)?(?P<suffix>.*)$", formalized)
        return "" if match is None else match.group("suffix")

    def _rebuild_quantity(self) -> None:
        self.quantity = self.integer if not self.fraction else f"{self.integer}.{self.fraction}"
        self.text = ("-" if self.minus else "") + self.quantity + self.suffix

    def _last_digit_index(self) -> int:
        return len(self.quantity) - 1

    def _move_left(self) -> bool:
        target_place = self._selected_place_exponent() + 1
        if target_place >= self.format.digits_limit[0]:
            return True
        self._normalize_width_for_place(target_place)
        self._set_selection_by_place(target_place)
        return True

    def _move_right(self) -> bool:
        target_place = self._selected_place_exponent() - 1
        if -target_place > self.format.digits_limit[1]:
            return True
        self._normalize_width_for_place(target_place)
        self._set_selection_by_place(target_place)
        return True

    def _apply_numeric_delta(self, direction: int) -> bool:
        selected_place = self._selected_place_exponent()
        current_value = self._current_decimal_value()
        step = self._selected_place_step()
        new_value = current_value + (step * direction)

        if not self._set_from_decimal_value(new_value, selected_place):
            return True

        self.result, self.value, self.formalized = self.format.match(self.text)
        if self.result is not None:
            self._emit_report()
        return True

    def _current_decimal_value(self) -> Decimal:
        quantity = Decimal(self.quantity)
        return -quantity if self.minus else quantity

    def _selected_place_step(self) -> Decimal:
        return Decimal(1).scaleb(self._selected_place_exponent())

    def _selected_place_exponent(self) -> int:
        if self.selected is None:
            raise ValueError("No selected digit in rolling mode.")

        dot_index = self.quantity.find(".")
        if dot_index == -1 or self.selected < dot_index:
            return len(self.integer) - self.selected - 1
        return -(self.selected - dot_index)

    def _set_selection_by_place(self, place: int) -> None:
        if place >= 0:
            self.selected = len(self.integer) - place - 1
        else:
            self.selected = len(self.integer) + (-place)

    def _minimum_fraction_len_for_place(self, place: int) -> int:
        return max(self.format.digits_limit[2], -place if place < 0 else 0)

    def _normalize_width_for_place(self, place: int) -> None:
        minimum_fraction_len = self._minimum_fraction_len_for_place(place)
        if len(self.fraction) < minimum_fraction_len:
            self.fraction = self.fraction + ("0" * (minimum_fraction_len - len(self.fraction)))
        elif len(self.fraction) > minimum_fraction_len:
            removable = len(self.fraction) - minimum_fraction_len
            trailing = len(self.fraction) - len(self.fraction.rstrip("0"))
            trim_count = min(removable, trailing)
            if trim_count:
                self.fraction = self.fraction[:-trim_count]

        minimum_integer_len = max(1, place + 1 if place >= 0 else 1)
        natural_integer = self.integer.lstrip("0") or "0"
        self.integer = natural_integer.zfill(minimum_integer_len)
        self._rebuild_quantity()

    def _set_from_decimal_value(self, value: Decimal, selected_place: int) -> bool:
        old_fraction_len = len(self.fraction)

        quantizer = Decimal(1).scaleb(-old_fraction_len)
        magnitude = abs(value).quantize(quantizer)
        natural_integer, new_fraction = self._split_decimal(magnitude, old_fraction_len)

        integer_capacity = self.format.digits_limit[0]
        if len(natural_integer) > integer_capacity:
            return False

        target_integer_len = max(1, len(natural_integer), selected_place + 1 if selected_place >= 0 else 1)
        self.minus = value < 0
        self.integer = natural_integer.zfill(target_integer_len)
        self.fraction = new_fraction
        self._normalize_width_for_place(selected_place)
        self._rebuild_quantity()
        self._set_selection_by_place(selected_place)
        return True

    def _split_decimal(self, value: Decimal, fraction_digits: int) -> tuple[str, str]:
        text = f"{value:.{fraction_digits}f}"
        integer, dot, fraction = text.partition(".")
        return integer, fraction if dot else ""
