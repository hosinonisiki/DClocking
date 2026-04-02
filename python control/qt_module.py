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
from decimal import Decimal, InvalidOperation
from qt_module_schema import PID_SCHEMA, ACCM_SCHEMA, SCLR_SCHEMA, FIRF_SCHEMA, LTRN_SCHEMA, PDH_SCHEMA, SCLO_SCHEMA, IIR_SCHEMA

_PARAM_APPLY_HANDLER = None
_PARAM_OPEN_HANDLER = None

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
    PREFIX_MAP = {
        "": Decimal("1"),
        "m": Decimal("1e-3"),
        "u": Decimal("1e-6"),
        "n": Decimal("1e-9"),
        "p": Decimal("1e-12"),
        "f": Decimal("1e-15"),
        "a": Decimal("1e-18"),
        "k": Decimal("1e3"),
        "M": Decimal("1e6"),
        "G": Decimal("1e9"),
        "T": Decimal("1e12"),
    }

    def __init__(self, value=0, unit="", decimals=6, parent=None):
        super().__init__(parent)
        self.unit = unit or ""
        self.decimals = int(max(0, decimals))
        self._re = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*$")
        self.setText(self._format_display(Decimal(str(value))))

    def _format_display(self, value: Decimal):
        s = f"{value:.{self.decimals}f}".rstrip("0").rstrip(".")
        if s in ("", "-", "+"):
            s = "0"
        return s

    def _parse_text(self):
        text = self.text().strip()
        m = self._re.match(text)
        if not m:
            return None
        num_str = m.group(1)
        try:
            base = Decimal(num_str)
        except InvalidOperation:
            return None
        return {
            "num": base,
            "num_str": num_str,
            "value": base,
        }

    def value_si(self):
        parsed = self._parse_text()
        return parsed["value"] if parsed else None

    def keyPressEvent(self, event):
        if event.key() not in (Qt.Key_Up, Qt.Key_Down):
            super().keyPressEvent(event)
            return

        parsed = self._parse_text()
        if not parsed:
            super().keyPressEvent(event)
            return

        full_text = self.text()
        num_str = parsed["num_str"]
        sign_offset = 1 if num_str.startswith(("-", "+")) else 0
        digits = num_str[sign_offset:]
        dot_idx = digits.find(".")

        start_idx = full_text.find(num_str)
        if start_idx < 0:
            super().keyPressEvent(event)
            return
        cursor = self.cursorPosition()
        rel = max(0, min(len(num_str) - 1, cursor - start_idx))

        if num_str[rel] in "+-":
            rel = min(len(num_str) - 1, rel + 1)
        if num_str[rel] == ".":
            rel = min(len(num_str) - 1, rel + 1)

        rel_no_sign = max(0, rel - sign_offset)
        if dot_idx >= 0:
            if rel_no_sign < dot_idx:
                power = dot_idx - rel_no_sign - 1
            elif rel_no_sign > dot_idx:
                power = -(rel_no_sign - dot_idx)
            else:
                power = 0
        else:
            power = len(digits) - rel_no_sign - 1

        step = Decimal(10) ** Decimal(power)
        if event.key() == Qt.Key_Down:
            step = -step

        new_num = parsed["num"] + step
        display = self._format_display(new_num)
        self.setText(display)
        self.setCursorPosition(max(0, min(len(display), cursor)))

        event.accept()

class ParamDialog(QDialog):
    def __init__(self, schema: list[dict], values: dict, parent = None, apply_callback = None):
        super().__init__(parent)
        self.setWindowTitle("参数修改")
        self._editors = {}
        self._fields = {}
        self._apply_callback = apply_callback

        layout = QFormLayout(self)

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
                value = int(values.get(key, field.get("default", 0)))
                edit = QuantityLineEdit(value=value, unit=field.get("unit", ""), decimals=0)
                prefix_box = QComboBox()
                for p in ["", "m", "u", "n", "p", "f", "a", "k", "M", "G", "T"]:
                    prefix_box.addItem(p if p else "(base)", p)
                prefix_box.setCurrentIndex(0)
                unit_text = field.get("unit", "")
                unit_label = QLabel(unit_text)
                unit_label.setMinimumWidth(36)
                w = QWidget()
                w_layout = QHBoxLayout(w)
                w_layout.setContentsMargins(0, 0, 0, 0)
                w_layout.addWidget(edit)
                w_layout.addWidget(prefix_box)
                w_layout.addWidget(unit_label)
            elif ftype == "float":
                value = float(values.get(key, field.get("default", 0.0)))
                edit = QuantityLineEdit(value=value, unit=field.get("unit", ""), decimals=field.get("decimals", 6))
                prefix_box = QComboBox()
                for p in ["", "m", "u", "n", "p", "f", "a", "k", "M", "G", "T"]:
                    prefix_box.addItem(p if p else "(base)", p)
                prefix_box.setCurrentIndex(0)
                unit_text = field.get("unit", "")
                unit_label = QLabel(unit_text)
                unit_label.setMinimumWidth(36)
                w = QWidget()
                w_layout = QHBoxLayout(w)
                w_layout.setContentsMargins(0, 0, 0, 0)
                w_layout.addWidget(edit)
                w_layout.addWidget(prefix_box)
                w_layout.addWidget(unit_label)
            elif ftype == "bool":
                w = QCheckBox()
                w.setChecked(bool(values.get(key, field.get("default", False))))
            else:
                w = QLineEdit()
                w.setText(str(values.get(key, field.get("default", ""))))
            
            if ftype == "int":
                self._editors[key] = ("int_qty", (edit, prefix_box))
            elif ftype == "float":
                self._editors[key] = ("float_qty", (edit, prefix_box))
            else:
                self._editors[key] = (ftype, w)
            row = QHBoxLayout()
            row.addWidget(w)
            confirm_btn = QPushButton("确认")
            confirm_btn.clicked.connect(lambda checked=False, k=key: self._apply_field(k))
            row.addWidget(confirm_btn)
            layout.addRow(label, row)

    def _value_from_editor(self, key: str):
        ftype, w = self._editors[key]
        field = self._fields.get(key, {})
        min_v = field.get("min", None)
        max_v = field.get("max", None)

        if ftype == "int_qty":
            edit, prefix_box = w
            si = edit.value_si()
            if si is None:
                raise ValueError("输入格式无效，请使用数字+可选前缀（m/u/n/p/f/a/k/M/G/T）")
            prefix = prefix_box.currentData() if isinstance(prefix_box.currentData(), str) else ""
            si = si * QuantityLineEdit.PREFIX_MAP.get(prefix, Decimal("1"))
            if si != si.to_integral_value():
                raise ValueError("整型参数经单位换算后必须是整数，请调整数值或前缀")
            value = int(si)
            if min_v is not None and value < min_v:
                raise ValueError(f"参数值小于最小值 {min_v}")
            if max_v is not None and value > max_v:
                raise ValueError(f"参数值大于最大值 {max_v}")
            return value

        if ftype == "float_qty":
            edit, prefix_box = w
            si = edit.value_si()
            if si is None:
                raise ValueError("输入格式无效，请使用数字+可选前缀（m/u/n/p/f/a/k/M/G/T）")
            prefix = prefix_box.currentData() if isinstance(prefix_box.currentData(), str) else ""
            si = si * QuantityLineEdit.PREFIX_MAP.get(prefix, Decimal("1"))
            value = float(si)
            if min_v is not None and value < min_v:
                raise ValueError(f"参数值小于最小值 {min_v}")
            if max_v is not None and value > max_v:
                raise ValueError(f"参数值大于最大值 {max_v}")
            return value

        if ftype == "bool":
            return bool(w.isChecked())
        if ftype == "flip_toggle":
            return bool(w.isChecked())
        if ftype == "flip_pulse":
            return None
        if ftype == "int":
            return int(w.value())
        if ftype == "float":
            return float(w.value())
        return w.text()

    def _set_toggle_button_text(self, button: QPushButton, label: str, checked: bool):
        state_text = "按下" if checked else "弹起"
        button.setText(f"{label}: {state_text}")

    def _apply_toggle_field(self, key: str, label: str, button: QPushButton, checked: bool):
        self._set_toggle_button_text(button, label, checked)
        if not self._apply_callback:
            return
        self._apply_callback({key: bool(checked)})

    def _apply_pulse_field(self, key: str):
        if not self._apply_callback:
            return
        # Pulse style: click triggers a one-shot action.
        self._apply_callback({key: None})

    def _apply_field(self, key: str) -> None:
        if not self._apply_callback:
            return
        try:
            value = self._value_from_editor(key)
            self._apply_callback({key: value})
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
                w = QSpinBox()
                w.setRange(field.get("min", -10**9), field.get("max", 10**9))
                w.setValue(int(init_value if init_value is not None else 0))
            elif ftype == "float":
                w = QDoubleSpinBox()
                w.setDecimals(field.get("decimals", 6))
                w.setRange(field.get("min", -1e18), field.get("max", 1e18))
                w.setValue(float(init_value if init_value is not None else 0.0))
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
                args[key] = int(w.value())
            elif ftype == "float":
                args[key] = float(w.value())
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
        h_step = 13
        n = len(items)
        if n:
            start_x = x_pos - (n - 1) * h_step / 2
            for i, (k, kind) in enumerate(items):
                sx = start_x + i * h_step

                if kind == "tick":
                    outer_r = 6
                    inner_r = 2.5
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
                    painter.drawEllipse(sx - 4, y_base - 4, 8, 8)

                elif kind == "square":
                    painter.drawRect(sx - 4, y_base - 4, 8, 8)

                elif kind == "diamond":
                    pts = [
                        QPointF(sx, y_base - 6),
                        QPointF(sx + 6, y_base),
                        QPointF(sx, y_base + 6),
                        QPointF(sx - 6, y_base),
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
                pts = [QPointF(sx, y_base - 5), QPointF(sx - 5, y_base + 3), QPointF(sx + 5, y_base + 3)]
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

    def apply_special_method(self, method_name: str, args: dict) -> None:
        if method_name:
            self._special_method_args[method_name] = dict(args or {})
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
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["RESET", "IN"]
        self.outputs = ["OUT"]
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
        painter.drawText(title_rect, Qt.AlignCenter, self.name)

        font.setBold(False)
        font.setPointSize(5)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"PID{self.index + 1}_{self.inputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"PID_{self.inputs[i]}")
        
        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 65, port_pos.y() - 8, 57, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"PID{self.index + 1}_{self.outputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"PID_{self.outputs[i]}")

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
        for key, value in params.items():
            self._params[key] = value
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
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["ERROR_IN", "BIAS_IN", "RESET", "PAUSE", "LF_RESET"]
        self.outputs = ["SLOW_OUT", "FAST_OUT"]
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
        painter.drawText(title_rect, Qt.AlignCenter, self.name)
        font.setBold(False)
        font.setPointSize(5)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"ACC{self.index + 1}_{self.inputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"ACC_{self.inputs[i]}")
        
        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 80, port_pos.y() - 8, 72, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"ACC{self.index + 1}_{self.outputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"ACC_{self.outputs[i]}")

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
        for key, value in params.items():
            self._params[key] = value
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
        self.index = index
        if component_name == "三角函数运算器":
            self.inputs = ["IN"]
            self.outputs = ["SIN", "COS"]
            self.inputs_signals = [["phase"]]
            self.outputs_signals = [["level"], ["level"]]
            self.maxm = 2
        elif component_name == "反三角函数运算器":
            self.inputs = ["SIN", "COS"]
            self.outputs = ["OUT"]
            self.inputs_signals = [["level"], ["level"]]
            self.outputs_signals = [["phase"]]
            self.maxm = 2
        elif component_name == "混频器":
            self.inputs = ["IN_A", "IN_B"]
            self.outputs = ["OUT"]
            self.inputs_signals = [["level"], ["level"]]
            self.outputs_signals = [["level", "differential"]]
            self.maxm = 4
        elif component_name == "解卷绕器":
            self.inputs = ["IN"]
            self.outputs = ["OUT"]
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
        painter.drawText(title_rect, Qt.AlignCenter, self.name)
        font.setBold(False)
        font.setPointSize(5)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            if self.component_name == "三角函数运算器":
                if self.index:
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"TRI{self.index + 1}_{self.inputs[i]}")
                else:
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"TRI_{self.inputs[i]}")
            elif self.component_name == "反三角函数运算器":
                if self.index:
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"ATAN{self.index + 1}_{self.inputs[i]}")
                else:
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"ATAN_{self.inputs[i]}")
            elif self.component_name == "混频器":
                if self.index:
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"MIXER{self.index + 1}_{self.inputs[i]}")
                else:
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"MIXER_{self.inputs[i]}")
            elif self.component_name == "解卷绕器":
                if self.index:
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"UNWRAPPER{self.index + 1}_{self.inputs[i]}")
                else:
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"UNWRAPPER_{self.inputs[i]}")
        
        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 60, port_pos.y() - 8, 52, 16)
            if self.component_name == "三角函数运算器":
                if self.index:
                    painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"TRI{self.index + 1}_{self.outputs[i]}")
                else:
                    painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"TRI_{self.outputs[i]}")
            elif self.component_name == "反三角函数运算器":
                if self.index:
                    painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"ATAN{self.index + 1}_{self.outputs[i]}")
                else:
                    painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"ATAN_{self.outputs[i]}")
            elif self.component_name == "混频器":
                if self.index:
                    painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"MIXER{self.index + 1}_{self.outputs[i]}")
                else:
                    painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"MIXER_{self.outputs[i]}")

            elif self.component_name == "解卷绕器":
                if self.index:
                    painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"UNWRAPPER{self.index + 1}_{self.outputs[i]}")
                else:
                    painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"UNWRAPPER_{self.outputs[i]}")


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
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["IN"]
        self.outputs = ["OUT"]
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
        painter.drawText(title_rect, Qt.AlignCenter, self.name)
        font.setBold(False)
        font.setPointSize(5)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"SCALER{self.index + 1}_{self.inputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"SCALER_{self.inputs[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 60, port_pos.y() - 8, 52, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"SCALER{self.index + 1}_{self.outputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"SCALER_{self.outputs[i]}")

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
        for key, value in params.items():
            self._params[key] = value
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
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["IN"]
        self.outputs = ["OUT"]
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
        painter.drawText(title_rect, Qt.AlignCenter, self.name)
        font.setBold(False)
        font.setPointSize(5)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"FIR{self.index + 1}_{self.inputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"FIR_{self.inputs[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 60, port_pos.y() - 8, 52, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"FIR{self.index + 1}_{self.outputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"FIR_{self.outputs[i]}")

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
        for key, value in params.items():
            self._params[key] = value
        self._notify_param_change(params)

    def special_methods_schema(self):
        return [
            {
                "name": "design_lowpass",
                "label": "低通滤波器设计",
                "params": [
                    {"key": "freq_pass", "label": "通带截止频率(Hz)", "type": "float", "min": 0.0, "max": 1e12, "default": 1e6, "decimals": 3},
                    {"key": "freq_stop", "label": "阻带截止频率(Hz)", "type": "float", "min": 0.0, "max": 1e12, "default": 10e6, "decimals": 3},
                    {"key": "freq_sample", "label": "采样频率(Hz)", "type": "float", "min": 1.0, "max": 1e12, "default": 250e6, "decimals": 3},
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
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["IN_A", "IN_B"]
        self.outputs = ["OUT_A", "OUT_B"]
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

        painter.drawText(title_rect, Qt.AlignCenter, self.name)
        font.setBold(False)
        font.setPointSize(5)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"LN_TRANSFORMER_{self.index + 1}_{self.inputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"LN_TRANSFORMER_{self.inputs[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 80, port_pos.y() - 8, 72, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"LN_TRANSFORMER_{self.index + 1}_{self.outputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"LN_TRANSFORMER_{self.outputs[i]}")

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
        for key, value in params.items():
            self._params[key] = value
        self._notify_param_change(params)

class ModulePDHFSM(NodeItem):
    def __init__(self, component_name, index,position, num_inputs = 2, num_outputs = 3):
        name = "PDH"
        super().__init__(name, component_name, index, position, num_inputs, num_outputs)
        self.name = name
        self.height = 180
        self.width = 140
        self.component_name = component_name
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["POWER", "SCAN"]
        self.outputs = ["PIN_RESET_CTRL", "MIXER_RESET_CTRL", "SCAN_RESET_CTRL"]
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

        painter.drawText(title_rect, Qt.AlignCenter, self.name)
        font.setBold(False)
        font.setPointSize(5)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"PDHFSM_IN_{self.inputs[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 110, port_pos.y() - 8, 100, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"PDHFSM_{self.outputs[i]}")

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
        for key, value in params.items():
            self._params[key] = value
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
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["IN"]
        self.outputs = ["OUT"]
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
        painter.drawText(title_rect, Qt.AlignCenter, self.name)
        font.setBold(False)
        font.setPointSize(5)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"IIR{self.index + 1}_{self.inputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"IIR_{self.inputs[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 60, port_pos.y() - 8, 52, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"IIR{self.index + 1}_{self.outputs[i]}")
            else:
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"IIR_{self.outputs[i]}")

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
        for key, value in params.items():
            self._params[key] = value
        self._notify_param_change(params)

    def special_methods_schema(self):
        return [
            {
                "name": "design_lowpass",
                "label": "低通滤波器设计",
                "params": [
                    {"key": "filter_type", "label": "滤波器类型", "type": "choice", "default": "butter", "options": ["butter", "ellip", "cheby1", "cheby2", "bessel"]},
                    {"key": "freq_pass", "label": "通带截止频率(Hz)", "type": "float", "min": 0.0, "max": 1e12, "default": 1e6, "decimals": 3},
                    {"key": "freq_sample", "label": "采样频率(Hz)", "type": "float", "min": 1.0, "max": 1e12, "default": 250e6, "decimals": 3},
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
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["PHASE_IN"]
        self.outputs = ["BIAS_OUT", "PID_RESET_CTRL"]
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

        painter.drawText(title_rect, Qt.AlignCenter, self.name)
        font.setBold(False)
        font.setPointSize(5)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"SCLOFSM_{self.inputs[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 100, port_pos.y() - 8, 90, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"SCLOFSM_{self.outputs[i]}")

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
        for key, value in params.items():
            self._params[key] = value
        self._notify_param_change(params)

class CompositeModule:

    sub_modules = []

    @classmethod
    def create_sub_modules(cls, scene, position, alloc_index_func):
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
                if hasattr(node, "free_mode"):
                    node.free_mode = not getattr(scene, "developer_mode", False)

class SINGenerator(CompositeModule):

    sub_modules = [
        ("累加器", QPointF(0, 0)),
        ("三角函数运算器", QPointF(200, 0)),
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
    "三角函数运算器": 2,
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
