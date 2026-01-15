from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QListWidget, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem,
                               QSplitter, QGraphicsEllipseItem, QDialog, QFormLayout,
                               QSpinBox, QDoubleSpinBox, QLineEdit, QDialogButtonBox)
# 导入PySide6的QtCore模块中的相关类
from PySide6.QtCore import Qt, QMimeData, QPointF, QRectF, Signal, QObject, QByteArray, QPoint
# 导入PySide6.QtGui模块中的相关类
from PySide6.QtGui import QDrag, QPainter, QPen, QBrush, QPainterPath, QColor, QFont, QPixmap, QImage, QCursor
#from qt_moudle_schema import PID_SCHEMA


class ParamDialog(QDialog):
    def __init__(self, schema: list[dict], values: dict, parent = None):
        super().__init__(parent)
        self.setWindowTitle("参数修改")
        self._editors = {}

        layout = QFormLayout

        for field in schema:
            key = field["key"]
            label = field.get("label", key)
            ftype = field.get("type", "str")

            if type == "int":
                w = QSpinBox()
                w.setRange(field.get("min", -10**9), field.get("max", 10**9))
                w.setValue(int(values.get(key, field.get("default", 0.0))))
            elif type == "float":
                w = QDoubleSpinBox()
                w.setDecimals(field.get("decimals", 6))
                w.setRange(field.get("min", -1e18), field.get("max", 1e18))
                w.setValue(float(values.get(key, field.get("default", 0.0))))
            else:
                w = QLineEdit()
                w.setText(str(values.get(key, field.get("default", ""))))
            
            self._editors[key] = (ftype, w)
            layout.addRow(label, w)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def values(self) -> dict:
        out = {}
        for key, (ftype, w) in self._editors.items():
            if ftype == "int":
                out[key] = int(w.value())
            elif ftype == "float":
                out[key] = float(w.value())
            else:
                out[key] = w.text()
        return out

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

    def __init__(self, parent, port_type, index, radius=6):
        super().__init__(parent)
        self.parent_node = parent
        self.port_type = port_type
        self.index = index
        self.radius = radius
        self.connections = []
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

    def _assign_unique_color(self):
        if self.parent_node:
            unique_id = id(self.parent_node) + self.index
        else:
            unique_id = id(self) + self.index
        color_index = unique_id % len(self.COLOR_POOL)
        return self.COLOR_POOL[color_index]

    def boundingRect(self):
        return QRectF(-self.radius, -self.radius, 2*self.radius, 2*self.radius)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(QPen(Qt.white, 1))
        painter.drawEllipse(-self.radius, -self.radius, 2*self.radius, 2*self.radius)

    def has_connection(self):
        return len(self.connections) > 0

    def get_connection(self):
        return self.connections[0] if self.connections else None

    def get_turn_distance(self):
        if self.manual_turn_distance is not None:
            return self.manual_turn_distance
        base_distance = 30
        increment = 7
        return base_distance + (self.index * increment)

    def get_bypass_offset(self):
        if self.manual_bypass_y is not None:
            if self.parent_node:
                start_node_top = self.parent_node.scenePos().y() - self.parent_node.height / 2
                return start_node_top - self.manual_bypass_y
            else:
                return self.scenePos().y() - 10 - self.manual_bypass_y
        base_offset = 30
        increment = 7
        return base_offset + (self.index * increment)

    def get_reverse_h_extend(self):
        if self.manual_reverse_h_extend is not None:
            return self.manual_reverse_h_extend
        base_extend = 30
        increment = 7
        return base_extend + (self.index * increment)
    
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
        self.setPos(position)

        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.in_ports = []
        self.out_ports = []
        self.edges = []

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.open_param_dialog()
            event.accept()
            return
        super().mouseDoubleClickEvent

    def param_schema(self) -> list[dict]:
        return []
    
    def get_params(self) -> dict:
        return {}
    
    def set_params(self, params: dict) -> None:
        pass

    def open_param_dialog(self):
        schema = self.param_schema()
        if not schema:
            return
        
        parent = QApplication.activeWindow()
        dig = ParamDialog(schema, self.get_params(), parent = parent)
        if dig.exec() == QDialog.accepted:
            self.set_params(dig.values())

    def _create_ports(self):
        if self.num_inputs > 0:
            port_spacing_in = self.height / (self.num_inputs + 1)
        if self.num_outputs > 0:
            port_spacing_out = self.height / (self.num_outputs + 1)

        for i in range(self.num_inputs):
            port = PortItem(self, 'in', i)
            y_offset = -self.height/2 + port_spacing_in * (i + 1)
            port.setPos(-self.width/2, y_offset)
            self.in_ports.append(port)

        for i in range(self.num_outputs):
            port = PortItem(self, 'out', i)
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

class MoudlePID(NodeItem):
    def __init__(self, component_name, index, position, num_inputs = 2, num_outputs = 1):
        if index == 0:
            name = "PIDC"
        else:
            name = f"PID{index + 1}"
        super().__init__(name, component_name, index, position, num_inputs, num_outputs)
        self.name = name
        self.height = 180
        self.width = 240
        self.component_name = component_name
        self.index = index
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.inputs = ["RESET", "IN"]
        self.outputs = ["OUT"]
        self.maxm = 2
        self.setPos(position)
   #     self.schema = PID_SCHEMA
        self.free_mode = True

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
        font.setPointSize(8)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            if self.index:
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"PID{self.index + 1}_{self.inputs[i]}")
            else:
                str = "PIDC_" + self.inputs[i]
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
"""  
    def param_schema(self):
        if self.free_mode:
            return [f for f in PID_SCHEMA if f.get("free", True)]
        return PID_SCHEMA
    
    def get_params(self):
        keys = [f["key"] for f in self.param_schema() if f.get("mode") in ("direct", "indirect")]
        return {}
"""
class MoudleAccumulator(NodeItem):
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
        self.maxm = 2
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
        font.setPointSize(8)
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

class MoudleBase(NodeItem):
    def __init__(self, component_name, index, position, num_inputs = 2, num_outputs = 1):
        if component_name == "三角函数运算器":
            if index == 0:
                name = "TRIG"
            else:
                name = f"TRI{index + 1}"
            super().__init__(name, component_name, index, position, 2, 1)
            self.num_inputs = 2
            self.num_outputs = 1
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
            self.inputs = ["IN", "SIN"]
            self.outputs = ["COS"]
            self.maxm = 2
        elif component_name == "反三角函数运算器":
            self.inputs = ["SIN", "COS"]
            self.outputs = ["OUT"]
            self.maxm = 2
        elif component_name == "混频器":
            self.inputs = ["IN_A", "IN_B"]
            self.outputs = ["OUT"]
            self.maxm = 4
        elif component_name == "解卷绕器":
            self.inputs = ["IN"]
            self.outputs = ["OUT"]
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
        font.setPointSize(8)
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

class MoudleScaler(NodeItem):
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
        self.maxm = 4
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
        font.setPointSize(8)
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
        self.maxm = 4
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
        font.setPointSize(8)
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

class MoudleLinerTransformer(NodeItem):
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
        self.maxm = 2
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
        font.setPointSize(8)
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

class MoudlePDHFSM(NodeItem):
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
        font.setPointSize(8)
        painter.setFont(font)

        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width / 2 + 10, port_pos.y() - 8, 80, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"PDHFSM_IN_{self.inputs[i]}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width / 2 - 100, port_pos.y() - 8, 90, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"PDHFSM_{self.outputs[i]}")

    def getmaxm(self):
        return self.maxm

class MoudleSCLOFSM(NodeItem):
    def __init__(self, component_name, index, position, num_inputs = 1, num_outputs = 2):
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
        font.setPointSize(8)
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

class CompositeMoudle:

    sub_moudles = []

    @classmethod
    def create_sub_modules(cls, scene, position, alloc_index_func):
        for sub_name, offset in cls.sub_moudles:
            moudle_cls = moudle_factory.get(sub_name)
            if moudle_cls:
                idx = alloc_index_func(sub_name)
                if idx is None:
                    print(f"❌ 超出 {sub_name} 模块数量上限")
                    continue
                sub_position = position + offset
                node = moudle_cls(sub_name, idx, sub_position)
                scene.addItem(node)

class SINGenerator(CompositeMoudle):

    sub_moudles = [
        ("累加器", QPointF(0, 0)),
        ("三角函数运算器", QPointF(200, 0)),
    ]

class DigitalControlledOscillator(CompositeMoudle):

    sub_moudles = [
        ("累加器", QPointF(0, 0)),
        ("三角函数运算器", QPointF(200, -150)),
        ("三角函数运算器", QPointF(200, 150)),
    ]

moudle_factory = {
    "PID控制器": MoudlePID,
    "累加器": MoudleAccumulator,
    "三角函数运算器": MoudleBase,
    "反三角函数运算器": MoudleBase,
    "线性缩放器": MoudleScaler,
    "FIR滤波器": ModuleFIRFilter,
    "线性变换器": MoudleLinerTransformer,
    "混频器": MoudleBase,
    "解卷绕器": MoudleBase,
    "PDH状态机": MoudlePDHFSM,
    "LO自动校准状态机": MoudleSCLOFSM,
}

moudle_maxm = {
    "PID控制器": 2,
    "累加器": 2,
    "三角函数运算器": 2,
    "反三角函数运算器": 2,
    "线性缩放器": 4,
    "FIR滤波器": 4,
    "线性变换器": 2,
    "混频器": 4,
    "解卷绕器": 1,
    "PDH状态机": 1,
    "LO自动校准状态机": 1,
}
composite_modules = {
    "正弦波发生器": SINGenerator,
    "数字控制振荡器": DigitalControlledOscillator,
    # 可以添加更多组合模块
}