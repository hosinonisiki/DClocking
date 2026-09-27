"""PDH observation and draft editor; never reads or writes hardware.

The supplied trace is the only curve drawn. Values are internal signed signal
codes, not an assumed ADC voltage. Programmatic setters never emit edits.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


ENTER = "threshold_signal_scan"
LOSS = "threshold_signal_lock"
TIMES = ("time_scan", "time_lock")
COLORS = {ENTER: QColor("#a40032"), LOSS: QColor("#087f83"),
          TIMES[0]: QColor("#a40032"), TIMES[1]: QColor("#087f83")}
LABELS = {ENTER: "入锁线", LOSS: "失锁线", TIMES[0]: "入锁确认", TIMES[1]: "失锁确认"}


class PDHWaveformCanvas(QWidget):
    parameter_changed = Signal(str, object)
    selection_changed = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(520, 310)
        self.setMouseTracking(True)
        self.setAccessibleName("PDH 判锁波形与判据草稿")
        self._times = ()
        self._values = ()
        self._parameters = {ENTER: 0, LOSS: 0, TIMES[0]: 0, TIMES[1]: 0}
        self._clock_hz = None
        self._source_label = "尚无数据"
        self._selection = None
        self._drag = None
        self._selection_anchor = None
        self._frozen_range = None
        self._display_range = (-50.0, 50.0)
        self._update_accessibility()

    @property
    def selection(self):
        return self._selection

    def set_trace(self, times, values, source_label="来源未标注"):
        times, values = tuple(times), tuple(values)
        if not times and not values:
            self._times, self._values = (), ()
        else:
            if len(times) != len(values) or len(times) < 2:
                raise ValueError("波形需要等长的时间与信号数组，且至少有两个采样点")
            if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
                   for x in (*times, *values)):
                raise ValueError("波形仅接受有限的数值")
            if any(b <= a for a, b in zip(times, times[1:])):
                raise ValueError("波形时间必须严格递增，单位为秒")
            if not math.isfinite(times[-1] - times[0]):
                raise ValueError("波形时间跨度超出有限范围")
            if any(x < -32768 or x > 32767 for x in values):
                raise ValueError("波形须使用有符号 16 位范围内的内部信号码")
            self._times, self._values = times, values
        self._source_label = str(source_label) or "来源未标注"
        self._selection = None
        self._drag = self._frozen_range = None
        self._refresh_range()
        self._update_accessibility()
        self.update()

    def set_parameters(self, mapping, clock_hz=None):
        candidate = dict(self._parameters)
        for key in candidate:
            if key not in mapping:
                continue
            value = mapping[key]
            low, high = (-32768, 32767) if key in (ENTER, LOSS) else (0, 2**32 - 1)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{key} 超出兼容的寄存器值范围")
            candidate[key] = value
        self._parameters = candidate
        self._clock_hz = (float(clock_hz) if type(clock_hz) in (int, float)
                          and math.isfinite(clock_hz) and clock_hz > 0 else None)
        # A synchronous parent echo must not move the scale below the cursor.
        # _frozen_range is held until mouseReleaseEvent, not reset here.
        if self._frozen_range is None:
            self._refresh_range()
        self.update()

    def set_selection(self, start, end):
        if not self._times:
            self._selection = None
        else:
            if any(type(x) not in (int, float) or not math.isfinite(x) for x in (start, end)):
                raise ValueError("选区端点必须是有限秒数")
            start, end = sorted((float(start), float(end)))
            start = max(self._times[0], min(self._times[-1], start))
            end = max(self._times[0], min(self._times[-1], end))
            self._selection = (start, end) if end > start else None
        self.update()

    def _update_accessibility(self):
        self.setAccessibleDescription(self._source_label + "；纵轴为内部信号码；修改只产生参数草稿")

    def _plot_rect(self):
        return QRectF(70, 61, max(1, self.width() - 94), max(1, self.height() - 170))

    def _y_range(self):
        return self._frozen_range or self._display_range

    def _refresh_range(self):
        data = (*self._values, self._parameters[ENTER], self._parameters[LOSS])
        low, high = min(data), max(data)
        padding = max(50.0, (high - low) * 0.12)
        self._display_range = max(-32768.0, low - padding), min(32767.0, high + padding)

    def _x(self, seconds):
        rect = self._plot_rect()
        return rect.left() + (seconds - self._times[0]) / (self._times[-1] - self._times[0]) * rect.width()

    def _time_at(self, x):
        rect = self._plot_rect()
        fraction = max(0.0, min(1.0, (x - rect.left()) / rect.width()))
        return self._times[0] + fraction * (self._times[-1] - self._times[0])

    def _y(self, value):
        low, high = self._y_range()
        rect = self._plot_rect()
        return rect.bottom() - (value - low) / (high - low) * rect.height()

    def marker_position(self, key):
        """Return the drag handle's widget coordinates, or None if unavailable."""
        if not self._times:
            return None
        rect = self._plot_rect()
        if key in (ENTER, LOSS):
            return QPointF(rect.left() + rect.width() * (0.72 if key == ENTER else 0.94),
                           self._y(self._parameters[key]))
        if key in TIMES and self._clock_hz is not None:
            span = self._times[-1] - self._times[0]
            duration = self._parameters[key] / self._clock_hz
            return QPointF(rect.left() + min(1.0, duration / span) * rect.width(),
                           rect.bottom() + 47 + TIMES.index(key) * 28)
        return None

    def _hit_marker(self, point):
        # Explicit handles take precedence when thresholds overlap.
        for key in (ENTER, LOSS, *TIMES):
            marker = self.marker_position(key)
            if marker is not None and (marker - point).manhattanLength() <= 14:
                return key
        rect = self._plot_rect()
        if rect.contains(point):
            for key in (ENTER, LOSS):
                marker = self.marker_position(key)
                if marker is not None and abs(marker.y() - point.y()) <= 5:
                    return key
        return None

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or not self._times:
            return super().mousePressEvent(event)
        key = self._hit_marker(event.position())
        if key:
            self._frozen_range = self._y_range()
            self._drag = key
        elif self._plot_rect().contains(event.position()):
            self._drag = "selection"
            self._selection_anchor = self._time_at(event.position().x())
        else:
            return super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(self, event):
        if self._drag is None:
            key = self._hit_marker(event.position())
            self.setCursor(Qt.SizeHorCursor if key in TIMES else Qt.SizeVerCursor if key
                           else Qt.CrossCursor if self._times and self._plot_rect().contains(event.position())
                           else Qt.ArrowCursor)
            return super().mouseMoveEvent(event)
        self._move_drag(event.position())
        event.accept()

    def _move_drag(self, point):
        if self._drag == "selection":
            previous = self._selection
            self.set_selection(self._selection_anchor, self._time_at(point.x()))
            if self._selection is not None and previous != self._selection:
                self.selection_changed.emit(*self._selection)
            return
        rect = self._plot_rect()
        key = self._drag
        if key in (ENTER, LOSS):
            low, high = self._y_range()
            value = round(low + (rect.bottom() - point.y()) / rect.height() * (high - low))
            value = max(-32768, min(32767, value))
        elif key in TIMES and self._clock_hz is not None:
            fraction = max(0.0, min(1.0, (point.x() - rect.left()) / rect.width()))
            duration = fraction * (self._times[-1] - self._times[0])
            value = (2**31 - 1 if duration >= (2**31 - 1) / self._clock_hz
                     else round(duration * self._clock_hz))
        else:
            return
        if value != self._parameters[key]:
            self._parameters[key] = value
            self.parameter_changed.emit(key, value)
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drag is not None:
            self._move_drag(event.position())
            self._drag = self._frozen_range = None
            self._refresh_range()
            self.update()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    @staticmethod
    def _duration_label(seconds):
        if seconds < 0.001:
            return f"{seconds * 1e6:.3g} μs"
        if seconds < 1:
            return f"{seconds * 1e3:.3g} ms"
        return f"{seconds:.3g} s"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#faf9f6"))
        painter.setPen(QColor("#344149"))
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        title = "判锁波形 · " + self._source_label
        painter.drawText(QRectF(16, 9, self.width() - 32, 25), Qt.AlignVCenter,
                         painter.fontMetrics().elidedText(title, Qt.ElideRight, self.width() - 32))
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(QColor("#64747d"))
        painter.drawText(QRectF(16, 35, 200, 20), "内部信号码")
        rect = self._plot_rect()
        painter.fillRect(rect, QColor("#ffffff"))
        painter.setPen(QPen(QColor("#d8dddf"), 1))
        painter.drawRect(rect)
        if not self._times:
            painter.setPen(QColor("#73828a"))
            painter.drawText(rect.adjusted(20, 0, -20, 0), Qt.AlignCenter | Qt.TextWordWrap,
                             "尚无波形\n导入记录、使用明确标注的演示，或接收实测快照")
            return
        low, high = self._y_range()
        span = self._times[-1] - self._times[0]
        unit, scale = ("μs", 1e6) if span < 0.001 else ("ms", 1e3) if span < 1 else ("s", 1)
        for index in range(5):
            fraction = index / 4
            x, y = rect.left() + rect.width() * fraction, rect.bottom() - rect.height() * fraction
            painter.setPen(QPen(QColor("#e4e7e8"), 1, Qt.DashLine))
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            painter.setPen(QColor("#64747d"))
            painter.drawText(QRectF(0, y - 9, 62, 18), Qt.AlignRight | Qt.AlignVCenter,
                             f"{low + (high - low) * fraction:.0f}")
            painter.drawText(QRectF(x - 38, rect.bottom() + 3, 76, 18), Qt.AlignCenter,
                             f"{(self._times[0] + span * fraction) * scale:.3g}")
        painter.drawText(QRectF(rect.right() - 75, rect.bottom() + 20, 75, 18),
                         Qt.AlignRight, "时间 / " + unit)
        painter.save()
        painter.setClipRect(rect)
        if self._selection:
            x0, x1 = map(self._x, self._selection)
            painter.fillRect(QRectF(x0, rect.top(), x1 - x0, rect.height()), QColor(164, 0, 50, 25))
        path = QPainterPath()
        path.moveTo(self._x(self._times[0]), self._y(self._values[0]))
        for time, value in zip(self._times[1:], self._values[1:]):
            path.lineTo(self._x(time), self._y(value))
        painter.setPen(QPen(QColor("#303d43"), 1.7))
        painter.drawPath(path)
        for key in (ENTER, LOSS):
            marker = self.marker_position(key)
            painter.setPen(QPen(COLORS[key], 1.4, Qt.DashLine))
            painter.drawLine(QPointF(rect.left(), marker.y()), QPointF(rect.right(), marker.y()))
            painter.setBrush(COLORS[key])
            painter.drawEllipse(marker, 5, 5)
            label = f"{LABELS[key]} {self._parameters[key]}"
            painter.drawText(QRectF(rect.left() + 8, marker.y() - 23 if key == ENTER else marker.y() + 3,
                                   rect.width() - 16, 20), Qt.AlignLeft, label)
        painter.restore()
        for index, key in enumerate(TIMES):
            y = rect.bottom() + 47 + index * 28
            painter.setPen(QPen(QColor("#e1e3e3"), 3))
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            marker = self.marker_position(key)
            painter.setPen(COLORS[key])
            if marker is not None:
                painter.setPen(QPen(COLORS[key], 3))
                painter.drawLine(QPointF(rect.left(), y), marker)
                painter.setBrush(COLORS[key])
                painter.drawEllipse(marker, 5, 5)
                duration = self._parameters[key] / self._clock_hz
                text = LABELS[key] + " " + self._duration_label(duration)
                if duration > span:
                    text += "（超出显示跨度）"
            else:
                text = LABELS[key] + "：确认核心时钟后可拖动"
            painter.drawText(QRectF(rect.left() + 5, y - 22, rect.width() - 10, 20), text)
        painter.setPen(QColor("#64747d"))
        painter.drawText(QRectF(16, self.height() - 22, self.width() - 32, 18),
                         "拖动判据只修改草稿；空白处横向拖动选择共振区段")
