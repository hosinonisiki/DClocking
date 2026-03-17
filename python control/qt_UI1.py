# 导入系统模块
from platform import node
import sys
import random
from collections import deque
from PySide6.QtCore import QTimer
# 导入PySide6的QtWidgets模块中的相关组件
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QListWidget, QListWidgetItem, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem,
                               QSplitter, QGraphicsEllipseItem, QPushButton, QComboBox)
# 导入PySide6的QtCore模块中的相关类
from PySide6.QtCore import Qt, QMimeData, QPointF, QRectF, Signal, QObject, QByteArray, QPoint
# 导入PySide6.QtGui模块中的相关类
from PySide6.QtGui import QDrag, QPainter, QPen, QBrush, QPainterPath, QColor, QFont, QPixmap, QImage, QCursor
from qt_moudle import (PortItem, NodeItem, MoudlePID, MoudleAccumulator, MoudleBase, 
                         MoudleScaler, ModuleFIRFilter, ModuleIIRFilter, MoudleSCLOFSM, MoudlePDHFSM,
                         MoudleLinerTransformer, CompositeMoudle, SINGenerator, DigitalControlledOscillator,
                         moudle_factory, moudle_maxm, set_param_apply_handler)
from qt_Port import Port
from PySide6.QtSerialPort import QSerialPort
import module_signal_router
import port_numbers as pn


def _ensure_port_methods():
    if hasattr(Port, "write_bus"):
        return

    def is_open(self):
        return self.serial_port.isOpen()

    def write_bus(self, module, address, data, hold=False):
        if not self.serial_port or not self.serial_port.isOpen():
            raise RuntimeError("Serial port is not open")
        module = module.upper()
        if isinstance(address, int):
            address = address.to_bytes(4, "big")
        elif isinstance(address, str):
            address = bytes.fromhex(address).rjust(4, b"\x00")
        if isinstance(data, int):
            data = data.to_bytes(4, "big")
        elif isinstance(data, str):
            data = bytes.fromhex(data).rjust(4, b"\x00")
        message = b":BUS_." + module.encode() + b".WRTE.ADDR." + address + b".DATA." + data
        if hold:
            message += b".HOLD!"
        else:
            message += b"!"
        self.serial_port.write(message)

    Port.is_open = is_open
    Port.write_bus = write_bus


class PortBus:
    def __init__(self, port_ctrl):
        self.port_ctrl = port_ctrl

    def write(self, module, address, data, hold=False):
        self.port_ctrl.write_bus(module, address, data, hold)


def _border_port_index(name, prefix):
    if not name.startswith(prefix):
        return None
    try:
        return int(name[len(prefix):])
    except ValueError:
        return None


def _resolve_port_number(node_name, port_index, role):
    border_out_idx = _border_port_index(node_name, "Border_out_")
    if border_out_idx is not None:
        inputs = [pn.INPUT_A, pn.INPUT_B, pn.INPUT_C, pn.INPUT_D, pn.INPUT_E, pn.INPUT_F, pn.INPUT_G, pn.INPUT_H]
        return inputs[border_out_idx] if 0 <= border_out_idx < len(inputs) and role == "out" else None

    border_in_idx = _border_port_index(node_name, "Border_in_")
    if border_in_idx is not None:
        outputs = [pn.OUTPUT_A, pn.OUTPUT_B, pn.OUTPUT_C, pn.OUTPUT_D, pn.OUTPUT_E, pn.OUTPUT_F, pn.OUTPUT_G, pn.OUTPUT_H]
        return outputs[border_in_idx] if 0 <= border_in_idx < len(outputs) and role == "in" else None

    if node_name in ("PIDC", "PID"):
        inputs = [pn.PID_RESET, pn.PID_IN]
        outputs = [pn.PID_OUT]
    elif node_name.startswith("PID"):
        inputs = [pn.PID2_RESET, pn.PID2_IN]
        outputs = [pn.PID2_OUT]
    elif node_name == "ACCM":
        inputs = {0: pn.ACC_ERROR_IN, 1 : pn.ACC_BIAS_IN, 2: pn.ACC_RESET, 3: pn.ACC_PAUSE, 4 : pn.ACC_LF_RESET}
        outputs = {0: pn.ACC_SLOW_OUT, 1: pn.ACC_FAST_OUT}
    elif node_name.startswith("ACC"):
        inputs = {0: pn.ACC2_ERROR_IN, 1: pn.ACC2_BIAS_IN, 2: pn.ACC2_RESET, 3: pn.ACC2_PAUSE, 4 : pn.ACC2_LF_RESET}
        outputs = {0: pn.ACC2_SLOW_OUT, 1: pn.ACC2_FAST_OUT}
    elif node_name == "SCLR":
        inputs = [pn.SCALER_IN]
        outputs = [pn.SCALER_OUT]
    elif node_name.startswith("SCL"):
        suffix = node_name[3:]
        base = f"SCALER{suffix}"
        inputs = [getattr(pn, f"{base}_IN", None)]
        outputs = [getattr(pn, f"{base}_OUT", None)]
    elif node_name == "FIRF":
        inputs = [pn.FIR_IN]
        outputs = [pn.FIR_OUT]
    elif node_name.startswith("FIR"):
        base = node_name
        inputs = [getattr(pn, f"{base}_IN", None)]
        outputs = [getattr(pn, f"{base}_OUT", None)]
    elif node_name == "IIRF":
        inputs = [pn.IIR_IN]
        outputs = [pn.IIR_OUT]
    elif node_name.startswith("IIR"):
        suffix = node_name[3:]
        base = f"IIR{suffix}"
        inputs = [getattr(pn, f"{base}_IN", None)]
        outputs = [getattr(pn, f"{base}_OUT", None)]
    elif node_name == "MIXR":
        inputs = [pn.MIXER_IN_A, pn.MIXER_IN_B]
        outputs = [pn.MIXER_OUT]
    elif node_name.startswith("MIX"):
        suffix = node_name[3:]
        base = f"MIXER{suffix}"
        inputs = [getattr(pn, f"{base}_IN_A", None), getattr(pn, f"{base}_IN_B", None)]
        outputs = [getattr(pn, f"{base}_OUT", None)]
    elif node_name == "TRIG":
        inputs = [pn.TRI_IN, None]
        outputs = [pn.TRI_COS]
    elif node_name == "TRI2":
        inputs = [pn.TRI2_IN, None]
        outputs = [pn.TRI2_COS]
    elif node_name == "ATAN":
        inputs = [pn.ATAN_IN_SIN, pn.ATAN_IN_COS]
        outputs = [pn.ATAN_OUT]
    elif node_name == "ATA2":
        inputs = [pn.ATAN2_IN_SIN, pn.ATAN2_IN_COS]
        outputs = [pn.ATAN2_OUT]
    elif node_name == "UNWR":
        inputs = [pn.UNWRAPPER_IN]
        outputs = [pn.UNWRAPPER_OUT]
    elif node_name == "LTRN":
        inputs = [pn.LN_TRANSFORMER_IN_A, pn.LN_TRANSFORMER_IN_B]
        outputs = [pn.LN_TRANSFORMER_OUT_A, pn.LN_TRANSFORMER_OUT_B]
    elif node_name == "LTR2":
        inputs = [pn.LN_TRANSFORMER2_IN_A, pn.LN_TRANSFORMER2_IN_B]
        outputs = [pn.LN_TRANSFORMER2_OUT_A, pn.LN_TRANSFORMER2_OUT_B]
    elif node_name == "PDH":
        inputs = [pn.PDHFSM_IN_POWER, pn.PDHFSM_IN_SCAN]
        outputs = [pn.PDHFSM_PID_RESET_CTRL, pn.PDHFSM_MIXER_RESET_CTRL, pn.PDHFSM_SCAN_RESET_CTRL]
    else:
        return None

    if isinstance(inputs, dict):
        return inputs.get(port_index) if role == "in" else outputs.get(port_index)
    if role == "in":
        return inputs[port_index] if 0 <= port_index < len(inputs) else None
    return outputs[port_index] if 0 <= port_index < len(outputs) else None


class NodeSignals(QObject):
    """
    自定义信号类，用于在节点之间传递连接创建和删除的信号

    Signals:
        connection_created: 当创建新连接时发出，参数为(源节点名, 源端口索引, 目标节点名, 目标端口索引)
        connection_removed: 当删除连接时发出，参数为(源节点名, 源端口索引, 目标节点名, 目标端口索引)
    """
    connection_created = Signal(str, int, str, int)
    connection_removed = Signal(str, int, str, int)

class BorderPort(PortItem):
    """
    表示边框上的输入/输出端口的图形项类
    """
    def __init__(self, port_type, index, position):
        super().__init__(None, port_type, index, ["bool", "level", "phase", "differential"])
        self.name = f"Border_{port_type}_{index}"
        self.port_type = port_type
        self.index = index
        self.radius = 6
        self.width = 20  # virtual width
        self.height = 20  # virtual height
        self.connections = []
        self.setPos(position)

        self.setAcceptHoverEvents(True)
        self.setZValue(10)

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
        base_distance = 30
        increment = 7
        return base_distance + (self.index * increment)

    def get_bypass_offset(self):
        base_offset = 30
        increment = 7
        return base_offset + (self.index * increment)

    def get_reverse_h_extend(self):
        base_extend = 30
        increment = 7
        return base_extend + (self.index * increment)


class EdgeItem(QGraphicsPathItem):
    def __init__(self, start_port, end_port):
        super().__init__()
        self.start_port = start_port
        self.end_port = end_port
        self.setZValue(-1)

        self.color = start_port.line_color
        self.base_pen_width = self._base_pen_width()
        self.hover_pen_width = self.base_pen_width + 1

        pen = QPen(QColor(self.color))
        pen.setWidth(self.base_pen_width)
        self._apply_pen_style(pen)
        self.setPen(pen)

        self.control_points = []
        self. horizontal_offset = 0
        self.reverse_horizontal_offset = 0

        start_port.connections.append(self)
        end_port.connections.append(self)

        self. setFlag(QGraphicsItem. ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        self.update_path()

    def _signal_set(self, port):
        signals = port.get_signals()
        if isinstance(signals, (list, tuple, set)):
            return {str(s) for s in signals}
        return {str(signals)}

    def _physical_signal_type(self):
        matched = self._matched_signals()
        for sig in ("level", "phase", "differential"):
            if sig in matched:
                return sig
        return None

    def _apply_pen_style(self, pen):
        sig = self._physical_signal_type()
        if sig == "phase":
            pen.setStyle(Qt.CustomDashLine)
            pen.setDashPattern([10, 4])
        elif sig == "differential":
            pen.setStyle(Qt.DashDotLine)
        else:
            pen.setStyle(Qt.SolidLine)

    def _matched_signals(self):
        start_set = self._signal_set(self.start_port)
        end_set = self._signal_set(self.end_port)
        matched = start_set & end_set
        if matched:
            return matched
        scene = self.scene()
        if scene and getattr(scene, "developer_mode", False):
            physical = {"level", "phase", "differential"}
            if (start_set & physical) and (end_set & physical):
                return (start_set & physical) or (end_set & physical)
        return matched

    def _has_physical_signal(self):
        matched = self._matched_signals()
        physical = {"level", "phase", "differential"}
        return any(sig in physical for sig in matched)

    def _base_pen_width(self):
        return 4 if self._has_physical_signal() else 2

    def _is_reverse_connection(self):
        p1 = self.start_port.scenePos()
        p2 = self.end_port.scenePos()
        return p2.x() < p1.x()

    def _compute_node_extents(self):
        s_node = self.start_port.parent_node if hasattr(self.start_port, 'parent_node') and self.start_port.parent_node else self.start_port
        e_node = self.end_port.parent_node if hasattr(self.end_port, 'parent_node') and self.end_port.parent_node else self.end_port
        s_top = s_node.scenePos().y() - s_node.height / 2
        s_bottom = s_node.scenePos().y() + s_node.height / 2
        e_top = e_node.scenePos().y() - e_node.height / 2
        e_bottom = e_node.scenePos().y() + e_node.height / 2
        return (s_top, s_bottom, e_top, e_bottom, s_node.width, s_node.height)

    def _calculate_bypass_y(self, bypass_offset):
        """
        根据规则计算绕行的 y 坐标，返回一个 y 值。
        新规则：当垂直距离超过节点高度时，横线位于目标节点顶部上方，
        并且根据起始端口的索引添加递增的偏移量，避免线条重叠。
        """
        p1_node = self.start_port.parent_node if hasattr(self.start_port, 'parent_node') and self.start_port.parent_node else self.start_port
        p2_node = self.end_port.parent_node if hasattr(self.end_port, 'parent_node') and self.end_port.parent_node else self.end_port
        s_pos = p1_node.scenePos()
        e_pos = p2_node.scenePos()

        dx = abs(e_pos.x() - s_pos.x())
        dy = abs(e_pos. y() - s_pos.y())
        node_w = max(p1_node.width, p2_node.width)
        node_h = max(p1_node.height, p2_node.height)

        s_top, s_bottom, e_top, e_bottom, _, _ = self._compute_node_extents()

        # 核心改动：当垂直距离超过节点高度时，横线位于目标节点顶部上方
        # 并根据输出端口索引添加递增偏移
        if dy > node_h: 
            # 基础间距
            base_clearance = 15
            # 每个端口的额外间距（根据索引递增）
            port_spacing = 10
            port_offset = self.start_port.index * port_spacing
            
            # 判断目标节点在起点节点的上方还是下方
            if e_pos.y() > s_pos.y():
                # 目标在下方，横线在目标节点顶部上方
                return e_top - base_clearance - port_offset
            else:
                # 目标在上方，横线在目标节点底部下方
                return e_bottom + base_clearance + port_offset
        
        # 原有逻辑：水平接近且垂直差大的情况
        if dx <= node_w: 
            # 情形 A:   起点端口在下方，目标端口在上方 -> 起点走上方，目标走下方
            if self. start_port.pos().y() > 0 and self.end_port.pos().y() < 0:
                up_point = s_top - bypass_offset
                down_point = e_bottom + bypass_offset
                return (up_point + down_point) / 2.0
            # 情形 B:  起点端口在上方，目标端口在下方 -> 起点走下方，目标走上方
            if self.start_port.pos().y() < 0 and self.end_port.pos().y() > 0:
                down_point = s_bottom + bypass_offset
                up_point = e_top - bypass_offset
                return (down_point + up_point) / 2.0
            # 其余情况回落到按目标端口决定上下
            if self.end_port.pos().y() > 0:
                return max(s_bottom, e_bottom) + bypass_offset
            else:
                return min(s_top, e_top) - bypass_offset
        else:
            # 按之前逻辑：目标端口在下方 -> 绕下，否则绕上
            if self.end_port.pos().y() > 0:
                return max(s_bottom, e_bottom) + bypass_offset
            else:
                return min(s_top, e_top) - bypass_offset

    def _calculate_route_using_bypass(self, p1, p2, bypass_y, h_extend):
        """
        使用给定 bypass_y 和水平延伸 h_extend 构建路由点（多段折线）。
        适用于既可左向也可右向的情形（在 dx 小且 dy 大时也使用）。
        """
        route = [
            p1,
            QPointF(p1.x() + h_extend, p1.y()),
            QPointF(p1.x() + h_extend, bypass_y),
            QPointF(p2.x() - h_extend + self.reverse_horizontal_offset, bypass_y),
            QPointF(p2.x() - h_extend, p2.y()),
            p2
        ]
        return route

    def _calculate_reverse_route(self, p1, p2):
        """
        旧的反向绕行计算（保留兼容性），但现在我们会在更高层决定绕行 y，并调用统一构建函数。
        """
        h_extend = self.start_port.get_reverse_h_extend()
        bypass_offset = self.start_port.get_bypass_offset()
        bypass_y = self._calculate_bypass_y(bypass_offset)
        return self._calculate_route_using_bypass(p1, p2, bypass_y, h_extend)

    def _calculate_simple_z_route(self, p1, p2):
        """
        计算简单的Z字形路径（直来直去），根据端口索引添加水平偏移避免竖线重叠。
        适用于正向连接且水平、垂直距离都较大的情况。
        """
        # 基础水平偏移
        base_offset = 30
        # 每个端口的额外偏移（根据索引递增）
        port_spacing = 7
        port_offset = self.start_port.index * port_spacing
        
        # 在起点右侧一定距离处转折（根据端口索引不同）
        vertical_x = p1.x() + base_offset + port_offset
        
        route = [
            p1,
            QPointF(vertical_x, p1.y()),
            QPointF(vertical_x, p2.y()),
            p2
        ]
        return route

    def update_path(self):
        if not self.start_port or not self.end_port:
            return

        p1 = self.start_port.scenePos()
        p2 = self.end_port.scenePos()

        path = QPainterPath()
        path.moveTo(p1)

        # 先判断是否采用"多段折线+bypass_y"的统一策略：
        s_node = self.start_port.parent_node if hasattr(self.start_port, 'parent_node') and self.start_port.parent_node else self.start_port
        e_node = self.end_port.parent_node if hasattr(self.end_port, 'parent_node') and self.end_port.parent_node else self.end_port
        dx = abs(e_node.scenePos().x() - s_node.scenePos().x())
        dy = abs(e_node.scenePos().y() - s_node.scenePos().y())
        node_w = max(s_node.width, e_node.width)
        node_h = max(s_node.height, e_node.height)

        # 判断是否为反向连接
        is_reverse = self._is_reverse_connection()

        # 新增逻辑：正向连接且水平、垂直距离都较大时，使用简单Z字形路径
        if not is_reverse and dx > node_w * 1.5 and dy > node_h:
            route = self._calculate_simple_z_route(p1, p2)
            for point in route[1: ]:
                path.lineTo(point)
        # 当垂直距离超过节点高度时，使用多段绕行路径
        elif dy > node_h:
            h_extend = self.start_port.get_reverse_h_extend()
            bypass_offset = self.start_port.get_bypass_offset()
            bypass_y = self._calculate_bypass_y(bypass_offset)
            route = self._calculate_route_using_bypass(p1, p2, bypass_y, h_extend)
            for point in route[1:]:
                path.lineTo(point)
        else:
            # 原有逻辑：根据左右决定是否为反向
            if is_reverse:
                route = self._calculate_reverse_route(p1, p2)
                for point in route[1:]: 
                    path.lineTo(point)
            else:
                # 正向连接：水平折线 + 可选垂直偏移
                turn_distance = self.start_port.get_turn_distance()
                turn_x = p1.x() + turn_distance

                y1_with_offset = p1.y() + self.horizontal_offset
                y2_with_offset = p2.y() + self.horizontal_offset

                path.lineTo(turn_x, p1.y())
                path. lineTo(turn_x, y1_with_offset)
                path.lineTo(turn_x, y2_with_offset)
                path.lineTo(turn_x, p2.y())
                path.lineTo(p2.x(), p2.y())

        self.setPath(path)

        # 更新控制点（若存在）
        if self.control_points:
            p1 = self.start_port.scenePos()
            p2 = self.end_port.scenePos()

            # 简单Z字形路径的控制点更新
            if not is_reverse and dx > node_w * 1.5 and dy > node_h:
                base_offset = 30
                port_spacing = 10
                port_offset = self.start_port.index * port_spacing
                vertical_x = p1.x() + base_offset + port_offset
                
                if len(self.control_points) >= 2:
                    calculated_center0 = QPointF(vertical_x, p1.y())
                    self.control_points[0].base_pos = calculated_center0
                    new_pos0 = calculated_center0 + self.control_points[0].manual_offset - self.control_points[0].rect().center()
                    self.control_points[0].setPos(new_pos0)
                    calculated_center1 = QPointF(vertical_x, p2.y())
                    self.control_points[1].base_pos = calculated_center1
                    new_pos1 = calculated_center1 + self.control_points[1].manual_offset - self.control_points[1].rect().center()
                    self.control_points[1].setPos(new_pos1)
            elif dy > node_h: 
                h_extend = self.start_port.get_reverse_h_extend()
                bypass_offset = self.start_port.get_bypass_offset()
                bypass_y = self._calculate_bypass_y(bypass_offset)

                if len(self.control_points) >= 3:
                    calculated_center0 = QPointF(p1.x() + h_extend, p1.y())
                    self.control_points[0].base_pos = calculated_center0
                    new_pos0 = calculated_center0 + self.control_points[0].manual_offset - self.control_points[0].rect().center()
                    self.control_points[0].setPos(new_pos0)
                    calculated_center1 = QPointF(p1.x() + h_extend, bypass_y)
                    self.control_points[1].base_pos = calculated_center1
                    new_pos1 = calculated_center1 + self.control_points[1].manual_offset - self.control_points[1].rect().center()
                    self.control_points[1].setPos(new_pos1)
                    calculated_center2 = QPointF(p2.x() - h_extend + self.reverse_horizontal_offset, bypass_y)
                    self.control_points[2].base_pos = calculated_center2
                    new_pos2 = calculated_center2 + self.control_points[2].manual_offset - self.control_points[2].rect().center()
                    self.control_points[2].setPos(new_pos2)
            else:
                if is_reverse:
                    h_extend = self.start_port.get_reverse_h_extend()
                    bypass_offset = self.start_port.get_bypass_offset()
                    start_node_top = self.start_port.parent_node.scenePos().y() - self.start_port.parent_node.height / 2
                    end_node_top = self.end_port.parent_node.scenePos().y() - self.end_port.parent_node.height / 2
                    start_node_bottom = self.start_port.parent_node.scenePos().y() + self.start_port.parent_node. height / 2
                    end_node_bottom = self.end_port.parent_node.scenePos().y() + self.end_port.parent_node. height / 2

                    if self.end_port.pos().y() > 0:
                        bypass_y = max(start_node_bottom, end_node_bottom) + bypass_offset
                    else: 
                        bypass_y = min(start_node_top, end_node_top) - bypass_offset

                    if len(self.control_points) >= 3:
                        calculated_center0 = QPointF(p1.x() + h_extend, p1.y())
                        self.control_points[0].base_pos = calculated_center0
                        new_pos0 = calculated_center0 + self.control_points[0].manual_offset - self.control_points[0].rect().center()
                        self.control_points[0].setPos(new_pos0)
                        calculated_center1 = QPointF(p1.x() + h_extend, bypass_y)
                        self.control_points[1].base_pos = calculated_center1
                        new_pos1 = calculated_center1 + self.control_points[1].manual_offset - self.control_points[1].rect().center()
                        self.control_points[1].setPos(new_pos1)
                        calculated_center2 = QPointF(p2.x() - h_extend + self.reverse_horizontal_offset, bypass_y)
                        self.control_points[2].base_pos = calculated_center2
                        new_pos2 = calculated_center2 + self.control_points[2].manual_offset - self.control_points[2].rect().center()
                        self.control_points[2].setPos(new_pos2)
                else:
                    turn_distance = self.start_port.get_turn_distance()
                    turn_x = p1.x() + turn_distance

                    y1_with_offset = p1.y() + self.horizontal_offset
                    y2_with_offset = p2.y() + self.horizontal_offset
                    mid_v_y = (y1_with_offset + y2_with_offset) / 2

                    if len(self.control_points) >= 2:
                        calculated_center0 = QPointF(turn_x, p1.y())
                        self.control_points[0].base_pos = calculated_center0
                        new_pos0 = calculated_center0 + self.control_points[0].manual_offset - self.control_points[0].rect().center()
                        self.control_points[0].setPos(new_pos0)
                        calculated_center1 = QPointF(turn_x, p2.y())
                        self.control_points[1].base_pos = calculated_center1
                        new_pos1 = calculated_center1 + self.control_points[1].manual_offset - self.control_points[1].rect().center()
                        self.control_points[1].setPos(new_pos1)
                        if len(self.control_points) >= 3:
                            calculated_center2 = QPointF(turn_x, p2.y())
                            self.control_points[2].base_pos = calculated_center2
                            new_pos2 = calculated_center2 + self.control_points[2].manual_offset - self.control_points[2].rect().center()
                            self.control_points[2].setPos(new_pos2)

    def hoverEnterEvent(self, event):
        for edge in self.start_port.connections:
            for cp in edge.control_points:
                cp.setVisible(True)

        pen = self.pen()
        pen.setWidth(self.hover_pen_width)
        self.setPen(pen)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        pen = self.pen()
        pen.setWidth(self.base_pen_width)
        self.setPen(pen)
        super().hoverLeaveEvent(event)

    def _create_control_points(self):
        return
    
    def remove(self):
        was_first = self.start_port.connections. index(self) == 0 if self in self.start_port.connections else False

        for cp in self.control_points:
            if cp.scene():
                cp.scene().removeItem(cp)
        self.control_points.clear()

        if self in self.start_port.connections:
            self.start_port. connections.remove(self)
        if self in self.end_port.connections:
            self. end_port.connections.remove(self)

        start_node = self.start_port.parent_node if hasattr(self.start_port, 'parent_node') and self.start_port.parent_node else None
        end_node = self.end_port.parent_node if hasattr(self.end_port, 'parent_node') and self.end_port.parent_node else None

        if start_node and self in start_node.edges:
            start_node.edges.remove(self)
        if end_node and self in end_node.edges:
            end_node.edges.remove(self)

        if was_first and self.start_port.connections:
            for edge in self.start_port.connections:
                edge._create_control_points()
                break

        if self.scene():
            self.scene().removeItem(self)

    def refresh_style(self):
        self.color = self.start_port.line_color
        self.base_pen_width = self._base_pen_width()
        self.hover_pen_width = self.base_pen_width + 1
        pen = self.pen()
        pen.setColor(QColor(self.color))
        pen.setWidth(self.base_pen_width)
        self._apply_pen_style(pen)
        self.setPen(pen)

class DiagramScene(QGraphicsScene):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.temp_line = None
        self.start_port = None
        self.developer_mode = False

        self.setBackgroundBrush(QBrush(QColor("#1E1E1E")))
        self.setSceneRect(0, 0, 4800, 2700)

        # Add border ports
        self.left_ports = []
        self.right_ports = []
        for i in range(8):
            left_port = BorderPort('out', i, QPointF(0, 0))
            self.addItem(left_port)
            self.left_ports.append(left_port)
            right_port = BorderPort('in', i, QPointF(0, 0))
            self.addItem(right_port)
            self.right_ports.append(right_port)

    def set_developer_mode(self, enabled: bool):
        self.developer_mode = bool(enabled)
        for item in self.items():
            if isinstance(item, EdgeItem):
                item.refresh_style()

    def _signal_set(self, port):
        signals = port.get_signals()
        if isinstance(signals, (list, tuple, set)):
            return {str(s) for s in signals}
        return {str(signals)}

    def _signal_set_from_signals(self, signals):
        if isinstance(signals, (list, tuple, set)):
            return {str(s) for s in signals}
        return {str(signals)}

    def _preview_style(self, start_port, end_port=None):
        physical = {"level", "phase", "differential"}
        start_set = self._signal_set(start_port)
        if end_port is not None:
            end_set = self._signal_set(end_port)
            matched = start_set & end_set
            if not matched and self.developer_mode:
                if (start_set & physical) and (end_set & physical):
                    matched = (start_set & physical) or (end_set & physical)
        else:
            matched = start_set

        for sig in ("level", "phase", "differential"):
            if sig in matched:
                return sig
        return None

    def _apply_preview_style(self, pen, start_port, end_port=None):
        sig = self._preview_style(start_port, end_port)
        if sig == "phase":
            pen.setStyle(Qt.CustomDashLine)
            pen.setDashPattern([10, 4])
        elif sig == "differential":
            pen.setStyle(Qt.DashDotLine)
        else:
            pen.setStyle(Qt.SolidLine)

    def _preview_width(self, start_port, end_port=None):
        physical = {"level", "phase", "differential"}
        start_set = self._signal_set(start_port)
        if end_port is not None:
            end_set = self._signal_set(end_port)
            matched = start_set & end_set
            if not matched and self.developer_mode:
                if (start_set & physical) and (end_set & physical):
                    matched = (start_set & physical) or (end_set & physical)
            return 3 if any(sig in physical for sig in matched) else 2
        return 3 if any(sig in physical for sig in start_set) else 2

    def mousePressEvent(self, event):
        items = self.items(event.scenePos())
        port = None
        for item in items:
            if isinstance(item, (PortItem, BorderPort)):
                port = item
                break

        if port:
            if port.port_type == 'out':
                self.start_port = port
                self.temp_line = QGraphicsPathItem()
                pen = QPen(QColor(port.line_color))
                self._apply_preview_style(pen, port)
                pen.setWidth(self._preview_width(port))
                self.temp_line.setPen(pen)
                self.addItem(self.temp_line)
                return

            elif port.port_type == 'in':
                if port.has_connection():
                    self.remove_connection(port)
                    return
                elif self.start_port:
                    self.finalize_connection(port)
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.temp_line and self.start_port:
            p1 = self.start_port.scenePos()
            p2 = event.scenePos()

            path = QPainterPath()
            path.moveTo(p1)

            s_node = self.start_port.parent_node if hasattr(self.start_port, 'parent_node') and self.start_port.parent_node else self.start_port
            # 如果鼠标悬停在某端口上则优先以该端口决定预览（否则以鼠标位置估算）
            hovered_items = self.items(event.scenePos())
            hovered_port = None
            for it in hovered_items:
                if isinstance(it, (PortItem, BorderPort)) and it is not self.start_port:
                    hovered_port = it
                    break

            if hovered_port:
                # 使用端口位置决定预览
                end_port_pos = hovered_port.scenePos()
                p2_ref = end_port_pos
                pen = self.temp_line.pen()
                pen.setColor(QColor(self.start_port.line_color))
                self._apply_preview_style(pen, self.start_port, hovered_port)
                pen.setWidth(self._preview_width(self.start_port, hovered_port))
                self.temp_line.setPen(pen)
            else:
                p2_ref = p2
                pen = self.temp_line.pen()
                pen.setColor(QColor(self.start_port.line_color))
                self._apply_preview_style(pen, self.start_port)
                pen.setWidth(self._preview_width(self.start_port))
                self.temp_line.setPen(pen)

            # 根据两节点位置决定是否采用跨式绕行策略（当 x 接近且 y 差大时）
            # 若没有真正的 end port，则以鼠标点估算 dx/dy
            dx = abs(p2_ref.x() - s_node.scenePos().x())
            dy = abs(p2_ref.y() - s_node.scenePos().y())
            node_w = s_node.width
            node_h = s_node.height

            if dx <= node_w and dy > node_h:
                # 采用多段绕行预览
                h_extend = self.start_port.get_reverse_h_extend()
                bypass_offset = self.start_port.get_bypass_offset()
                # 这里若有 hovered_port 则使用它的本地 pos 判断方向，否则用鼠标相对位置估算
                if hovered_port:
                    # 计算 bypass_y 同 update_path 的规则
                    tmp_edge = EdgeItem(self.start_port, hovered_port)
                    # 不将其添加到场景，只利用其计算函数
                    bypass_y = tmp_edge._calculate_bypass_y(bypass_offset)
                    # 立即清理临时创建的连接对象（仅用于计算）
                    tmp_edge.remove()
                else:
                    # 估算：鼠标在 start 上方/下方决定
                    if p2.y() > p1.y():
                        bypass_y = max(s_node.scenePos().y() + node_h/2, p2.y()) + bypass_offset
                    else:
                        bypass_y = min(s_node.scenePos().y() - node_h/2, p2.y()) - bypass_offset

                route = [
                    p1,
                    QPointF(p1.x() + h_extend, p1.y()),
                    QPointF(p1.x() + h_extend, bypass_y),
                    QPointF(p2_ref.x() - h_extend, bypass_y),
                    QPointF(p2_ref.x() - h_extend, p2_ref.y()),
                    p2_ref
                ]
                for pt in route[1:]:
                    path.lineTo(pt)
            else:
                # 原先的正向/反向预览逻辑
                if p2.x() < p1.x():
                    h_extend = self.start_port.get_reverse_h_extend()
                    bypass_offset = self.start_port.get_bypass_offset()
                    bypass_y = p1.y() - bypass_offset
                    path.lineTo(p1.x() + h_extend, p1.y())
                    path.lineTo(p1.x() + h_extend, bypass_y)
                    path.lineTo(p2.x() - h_extend, bypass_y)
                    path.lineTo(p2.x() - h_extend, p2.y())
                    path.lineTo(p2.x(), p2.y())
                else:
                    turn_distance = self.start_port.get_turn_distance()
                    turn_x = p1.x() + turn_distance

                    path.lineTo(turn_x, p1.y())
                    path.lineTo(turn_x, p2.y())
                    path.lineTo(p2.x(), p2.y())

            self.temp_line.setPath(path)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.temp_line and self.start_port:
            items = self.items(event.scenePos())
            end_port = None
            for item in items:
                if isinstance(item, (PortItem, BorderPort)):
                    end_port = item
                    break

            if end_port and self._is_valid_connection(self.start_port, end_port):
                self.finalize_connection(end_port)
            else:
                self._cancel_connection()

        super().mouseReleaseEvent(event)

    def _is_signal_type_matched(self, output_signals, input_signals):
        output_set = self._signal_set_from_signals(output_signals)
        input_set = self._signal_set_from_signals(input_signals)
        if output_set & input_set:
            return True
        physical = {"level", "phase", "differential"}
        if self.developer_mode and (output_set & physical) and (input_set & physical):
            return True
        return False

    def _is_valid_connection(self, start_port, end_port):
        output_signals = start_port.get_signals()
        input_signals = end_port.get_signals()
        if end_port.port_type != 'in':
            print("❌ 连接失败: 只能连接到输入端口")
            return False

        start_node = start_port.parent_node if hasattr(start_port, 'parent_node') and start_port.parent_node else None
        end_node = end_port.parent_node if hasattr(end_port, 'parent_node') and end_port.parent_node else None


        if start_node and end_node and end_node == start_node:
            print("❌ 连接失败: 不能连接到自己节点的端口")
            return False

        if end_port.has_connection():
            print("❌ 连接失败: 输入端口已被占用")
            return False

        if not self._is_signal_type_matched(output_signals, input_signals):
            print("❌ 连接失败: 输出端口、输入端口信号类型不匹配")
            return False

        return True

    def _cancel_connection(self):
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None

        if self.start_port:
            print(f"⚠️ 连接已取消: 未找到有效的目标端口")
            self.start_port = None

    def finalize_connection(self, end_port):
        edge = EdgeItem(self.start_port, end_port)
        self.addItem(edge)
        edge.refresh_style()

        start_node = self.start_port.parent_node if hasattr(self.start_port, 'parent_node') and self.start_port.parent_node else None
        end_node = end_port.parent_node if hasattr(end_port, 'parent_node') and end_port.parent_node else None

        if start_node:
            start_node.edges.append(edge)
        if end_node:
            end_node.edges.append(edge)

        if self.temp_line:
            self.removeItem(self.temp_line)
        self.temp_line = None

        src_name = self.start_port.parent_node.name if hasattr(self.start_port, 'parent_node') and self.start_port.parent_node else self.start_port.name
        src_port_idx = self.start_port.index
        dst_name = end_port.parent_node.name if hasattr(end_port, 'parent_node') and end_port.parent_node else end_port.name
        dst_port_idx = end_port.index

        self.start_port = None

        direction = "反向(绕行)" if edge._is_reverse_connection() else "正向"
        print(f"✅ 连线建立: [{src_name}:Out{src_port_idx+1}] --> [{dst_name}:In{dst_port_idx+1}] ({direction}, 颜色: {edge.color})")
        self.signals.connection_created.emit(src_name, src_port_idx, dst_name, dst_port_idx)

    def remove_connection(self, input_port):
        if not input_port.has_connection():
            return

        edge = input_port.get_connection()

        src_name = edge.start_port.parent_node.name if hasattr(edge.start_port, 'parent_node') and edge.start_port.parent_node else edge.start_port.name
        src_port_idx = edge.start_port.index
        dst_name = edge.end_port.parent_node.name if hasattr(edge.end_port, 'parent_node') and edge.end_port.parent_node else edge.end_port.name
        dst_port_idx = edge.end_port.index
        edge_color = edge.color

        edge.remove()

        print(f"🗑️ 连线已断开: [{src_name}:Out{src_port_idx+1}] -X-> [{dst_name}:In{dst_port_idx+1}] (颜色: {edge_color})")
        self.signals.connection_removed.emit(src_name, src_port_idx, dst_name, dst_port_idx)

class DiagramView(QGraphicsView):

    moudle_factory = {
    "PID控制器": MoudlePID,
    "累加器": MoudleAccumulator,
    "三角函数运算器": MoudleBase,
    "反三角函数运算器": MoudleBase,
    "线性缩放器": MoudleScaler,
    "FIR滤波器": ModuleFIRFilter,
    "IIR滤波器": ModuleIIRFilter,  # 新增
    "线性变换器": MoudleLinerTransformer,
    "混频器": MoudleBase,
    "解卷绕器": MoudleBase,
    "PDH状态机": MoudlePDHFSM,
    "LO自动校准状态机": MoudleSCLOFSM,
    }

    composite_modules = {
        "正弦波发生器": SINGenerator,
        "数字控制振荡器": DigitalControlledOscillator,
        # 可以添加更多组合模块
    }

    def __init__(self, scene):
        super().__init__(scene)
        
        # ====== 视口更新和渲染设置 ======
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        
        # ====== 渲染质量设置 ======
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # ====== 性能优化 ======
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, False)
        
        # ====== 初始化属性 ======
        self._used_indices = {k: set() for k in self.moudle_factory}
        self._maxnum = {k: moudle_maxm.get(k, 1) for k in self.moudle_factory}
        self._drag_candidate_node = None
        self._drag_start_pos = None
        self._is_dragging_view = False
        self._view_drag_start_pos = None
        self.scale_factor = 1.0
        
        self.setAcceptDrops(True)
        self.sync_scene_to_viewport()
        self.update_border_ports()
        self.horizontalScrollBar().valueChanged.connect(self._on_view_scrolled)
        self.verticalScrollBar().valueChanged.connect(self._on_view_scrolled)

    def sync_scene_to_viewport(self):
        scene = self.scene()
        if not scene:
            return
        
        top_left = self.mapToScene(self.viewport().rect().topLeft())
        bottom_right = self.mapToScene(self.viewport().rect().bottomRight())
        view_rect = QRectF(top_left, bottom_right)
        scene_rect = scene.sceneRect()
        if not scene_rect.contains(view_rect):
            scene.setSceneRect(scene_rect.united(view_rect))

    def _on_view_scrolled(self, _value):
        self.sync_scene_to_viewport()
        self.update_border_ports()

    def update_border_ports(self):
        scene = self.scene()
        if not scene:
            return
        
        viewport_rect = self.viewport().rect()
        height = viewport_rect.height()
        spacing = height / 9

        for i in range(8):
            y_pos = spacing * (i + 1)

            left_scene_pos = self.mapToScene(QPoint(5 * self.scale_factor, int(y_pos)))
            scene.left_ports[i].setPos(left_scene_pos)

            right_scene_pos = self.mapToScene(QPoint(viewport_rect.width() - 5 * self.scale_factor, int(y_pos)))
            scene.right_ports[i].setPos(right_scene_pos)

        # Update all connections after moving border ports
        for item in scene.items():
            if isinstance(item, EdgeItem):
                item.update_path()

    def _alloc_index(self, component_name: str):
        #给新创建的组件分配下标
        used = self._used_indices[component_name]
        for i in range(self._maxnum[component_name]):
            if i not in used:
                used.add(i)
                return i
        return None
    
    def _free_index(self, component_name: str, idx: int):
        #释放被删除的组件占用的下标
        self._used_indices.get(component_name, set()).discard(idx)

    def _apply_mode_to_node(self, node):
        scene = self.scene()
        if not scene or not node:
            return
        developer_mode = getattr(scene, "developer_mode", False)
        if hasattr(node, "free_mode"):
            node.free_mode = not developer_mode


    def _is_near_node(self, scene_pos, margin=10):
        #判断拖拽位置是否在组件附近
        for item in self.scene().items():
            if isinstance(item, NodeItem):
                node_rect = item.boundingRect()
                node_scene_rect = item.mapRectToScene(node_rect)
                expanded_rect = node_scene_rect.adjusted(-margin, -margin, margin, margin)
                if expanded_rect.contains(scene_pos):
                    return True
        return False
    
    def _is_near_port(self, scene_pos, margin=10):
        #判断拖拽位置是否在端口附近
        for item in self.scene().items():
            if isinstance(item, PortItem):
                port_rect = item.boundingRect()
                port_scene_rect = item.mapRectToScene(port_rect)
                expanded_rect = port_scene_rect.adjusted(-margin, -margin, margin, margin)
                if expanded_rect.contains(scene_pos):
                    return True
        return False
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        #处理将组件拖入画布时组件的创建
        component_name = event.mimeData().text()
        position = self.mapToScene(event.position().toPoint())

        # 检查是否是组合模块
        if component_name in self.composite_modules:
            composite_cls = self.composite_modules[component_name]
            composite_cls.create_sub_modules(self.scene(), position, self._alloc_index)
            event.acceptProposedAction()
        else:
            moudle_cls = self.moudle_factory.get(component_name)
            if moudle_cls:
                idx = self._alloc_index(component_name)
                if idx is None:
                    print(f"❌ 超出 {component_name} 模块数量上限")
                    return
                if component_name == "解卷绕机":
                    node = moudle_cls(component_name, idx, position, 1, 1)
                else:
                    node = moudle_cls(component_name, idx, position)
                self._apply_mode_to_node(node)
                self.scene().addItem(node)
                event.acceptProposedAction()

    def mousePressEvent(self, event):
        #处理拖拽行为，在组件及组件周围时拖动组件/开始连线，其余情况拖动画布
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            items = self.scene().items(scene_pos)

            self._drag_candidate_node = None
            self._drag_start_pos = None
            self._is_dragging_view = False
            self._view_drag_start_pos = None

            # 检查是否在控制点上，如果是则不处理拖拽
            has_control_point = any(isinstance(it, QGraphicsEllipseItem) for it in items)
            if has_control_point:
                return

            for it in items:
                if isinstance(it, NodeItem):
                    self._drag_candidate_node = it
                    self._drag_start_pos = event.position().toPoint()
                    event.accept()
                    return
            
            if not self._is_near_node(scene_pos, margin=10) and not self._is_near_port(scene_pos, margin=10):
                self._is_dragging_view = True
                self._view_drag_start_pos = event.position().toPoint()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return
                
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        #处理画布拖动
        if (event.buttons() & Qt.LeftButton) and self._is_dragging_view and self._view_drag_start_pos:
            delta = event.position().toPoint() - self._view_drag_start_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.update_border_ports()
            self._view_drag_start_pos = event.position().toPoint()
            event.accept()
            return
        #处理组件拖动
        if (event.buttons() & Qt.LeftButton) and self._drag_candidate_node and self._drag_start_pos:
            dist = (event.position().toPoint() - self._drag_start_pos).manhattanLength()
            if dist >= QApplication.startDragDistance():

                gp = event.globalPosition().toPoint()
                top_left = self.viewport().mapToGlobal(self.viewport().rect().topLeft())
                bottom_right = self.viewport().mapToGlobal(self.viewport().rect().bottomRight())

                #判断组件是否被拖入右侧组件栏
                outside_view = (
                    gp.x() > bottom_right.x() and
                    gp.y() >= top_left.y() and gp.y() <= bottom_right.y()
                )

                node = self._drag_candidate_node

                #未拖入组件栏，正常处理
                if not outside_view:
                    scene_pos = self.mapToScene(event.position().toPoint())
                    node.setPos(scene_pos)
                    event.accept()
                    return
                #拖入组件栏，处理删除
                else:
                    node = self._drag_candidate_node
                    orig_visible = node.isVisible()

                    #设置连线、组件状态为不可见
                    node.setVisible(False)
                    for edge in node.edges:
                        edge.setVisible(False)
                    self.scene().clearSelection()
                    mime = QMimeData()
                    mime.setData("application/x-node-instance", QByteArray(str(id(node)).encode("utf-8")))
                    mime.setText(getattr(node, "name", ""))

                    drag = QDrag(self)
                    drag.setMimeData(mime)

                    #生成删除的组件的缩略信息
                    try:
                        pix = self._node_pixmap(node)
                        drag.setPixmap(pix)
                        drag.setHotSpot(pix.rect().center())
                    except Exception:
                        pass

                    result = drag.exec(Qt.MoveAction)

                    #删除组件
                    if result == Qt.MoveAction:
                        self.remove_node(node)
                    #如果重新拖入画布，恢复组件及连线
                    else:
                        global_pos = QCursor.pos() 
                        view_pos = self.viewport().mapFromGlobal(global_pos)
                        scene_pos = self.mapToScene(view_pos)
                        node.setPos(scene_pos)
                        node.setVisible(orig_visible)
                        for edge in node.edges:
                            edge.setVisible(True)

                    self._drag_candidate_node = None
                    self._drag_start_pos = None
                    return


        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self._drag_candidate_node = None
        self._drag_start_pos = None
        if self._is_dragging_view:
            self._is_dragging_view = False
            self._view_drag_start_pos = None
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        #通过ctrl键及鼠标滚轮进行缩放
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                delta_scale_factor = 1.1
            else:
                delta_scale_factor = 0.9
            self.scale_factor *= delta_scale_factor
            self.scale(delta_scale_factor, delta_scale_factor)
            event.accept()
            self.sync_scene_to_viewport()
            self.update_border_ports()
        else:
            super().wheelEvent(event)
            self.sync_scene_to_viewport()
            self.update_border_ports()

    def _node_pixmap(self, node, thumbnail_size=(100, 100)):
        #生成组件的缩略信息
        img = QImage(thumbnail_size[0], thumbnail_size[1], QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)

        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(5, 5, thumbnail_size[0] - 10, thumbnail_size[1] - 10)
        p.setBrush(QBrush(QColor("#2C3E50")))
        p.setPen(QPen(Qt.white, 2))
        p.drawRoundedRect(rect, 8, 8)

        p.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        p.setFont(font)
        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)
        p.drawText(title_rect, Qt.AlignCenter, getattr(node, 'name', 'Node'))

        font.setBold(False)
        font.setPointSize(8)
        p.setFont(font)
        type_rect = QRectF(rect.left(), rect.top() + 25, rect.width(), 20)
        component_name = getattr(node, 'component_name', 'Unknown')
        p.drawText(type_rect, Qt.AlignCenter, component_name)

        p.end()
        return QPixmap.fromImage(img)



    def remove_node(self, node: NodeItem):
            # 延时参数（毫秒）
            delay_ms = 200  # 你可以改成 50/100/200

            edges = list(node.edges)  # 先复制出来，避免边被 remove() 后列表变化

            def remove_next_edge(i=0):
                if i >= len(edges):
                    # 所有边都断完了，再删节点本体
                    if node.scene():
                        self._free_index(node.component_name, int(node.index))
                        node.scene().removeItem(node)

                    node.edges.clear()
                    self.scene().update()
                    self.viewport().update()
                    print(f"🗑️ 已移除组件: {node.name}")
                    return

                edge = edges[i]
                # edge 可能已经被别处删掉了，做个健壮性判断
                if edge and edge.start_port and edge.end_port:
                    src_name = edge.start_port.parent_node.name if getattr(edge.start_port, "parent_node", None) else edge.start_port.name
                    src_port_idx = edge.start_port.index
                    dst_name = edge.end_port.parent_node.name if getattr(edge.end_port, "parent_node", None) else edge.end_port.name
                    dst_port_idx = edge.end_port.index

                    # 先发断开信号（触发硬件清空路由）
                    self.scene().signals.connection_removed.emit(src_name, src_port_idx, dst_name, dst_port_idx)

                    # 再删图形连线
                    edge.remove()

                # 下一条边延时处理
                QTimer.singleShot(delay_ms, lambda: remove_next_edge(i + 1))

            # 开始异步断开第一条
            remove_next_edge(0)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_scene_to_viewport()
        self.update_border_ports()

class ComponentPalette(QListWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(150)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setStyleSheet("font-size: 14px; padding: 5px;")

        normal_items = [
            "PID控制器",
            "累加器",
            "三角函数运算器",
            "反三角函数运算器",
            "线性缩放器",
            "FIR滤波器",
            "IIR滤波器",  # 新增
            "线性变换器",
            "混频器",
            "解卷绕器",
            "PDH状态机",
            "LO自动校准状态机",
        ]
        composite_items = [
            "正弦波发生器",
            "数字控制振荡器",
        ]

        self._add_section("非组合模块", normal_items)
        self._add_section("组合模块", composite_items)
 
    def _add_section(self, title, items):
        header = QListWidgetItem(title)
        header.setFlags(Qt.ItemIsEnabled)
        header.setTextAlignment(Qt.AlignCenter)
        header.setForeground(QColor("#888888"))
        self.addItem(header)

        for name in items:
            item = QListWidgetItem(name)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
            self.addItem(item)

    def _create_component_thumbnail(self, component_name, size=(120, 100)):
        #创建组件的缩略信息
        img = QImage(size[0], size[1], QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)

        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(5, 5, size[0] - 10, size[1] - 10)
        p.setBrush(QBrush(QColor("#2C3E50")))
        p.setPen(QPen(Qt.white, 2))
        p.drawRoundedRect(rect, 8, 8)

        p.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        p.setFont(font)
        p.drawText(rect, Qt.AlignCenter, component_name)

        p.end()
        return QPixmap.fromImage(img)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item or not (item.flags() & Qt.ItemIsDragEnabled):
            return
        mimeData = QMimeData()
        mimeData.setText(item.text())

        pixmap = self._create_component_thumbnail(item.text())

        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        drag.exec(Qt.CopyAction)

    def dragEnterEvent(self, event):
        md = event.mimeData()
        if md.hasFormat("application/x-node-instance"):
            event.setDropAction(Qt.MoveAction)
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)
    
    def dragMoveEvent(self, e):
        md = e.mimeData()
        if md.hasFormat("application/x-node-instance"):
            e.setDropAction(Qt.MoveAction)
            e.acceptProposedAction()
            return
        super().dragMoveEvent(e)
    
    def dropEvent(self, event):
        md = event.mimeData()
        if md.hasFormat("application/x-node-instance"):
            event.setDropAction(Qt.MoveAction)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 节点流编辑器 - 支持复杂绕行规则")
        self.resize(1600, 900)

        self._route_queue = deque()
        self._route_sending = False
        self.route_send_delay_ms = 80  # 你要的延时：可调 50/80/100/200

        self.comboBox = QComboBox()
        self.mode_combo = QComboBox()
        self.mode_combo.setFixedWidth(120)
        self.mode_combo.addItems(["Free Mode", "Developer Mode"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self.comboBox.setFixedWidth(180)

        self.connect_btn = QPushButton("连接")
        self.connect_btn.setFixedWidth(80)

        serial_bar = QWidget()
        serial_bar.setFixedHeight(40)
        serial_layout = QHBoxLayout(serial_bar)
        serial_layout.setContentsMargins(8, 4, 8, 4)
        serial_layout.addStretch()
        serial_layout.addWidget(self.comboBox)
        serial_layout.addWidget(self.mode_combo)
        serial_layout.addWidget(self.connect_btn)
        serial_layout.addStretch()
        self.serial_port = QSerialPort(self)
        self.port_ctrl = Port(self, self.serial_port)
        self.port_ctrl.scan_ports(force_update=True)
        _ensure_port_methods()
        self.router_bus = None
        self.router = None

        self.signals = NodeSignals()
        self.signals.connection_created.connect(self.run_business_logic)
        self.signals.connection_removed.connect(self.handle_connection_removed)

        self.scene = DiagramScene(self.signals)
        self.view = DiagramView(self.scene)
        self.palette = ComponentPalette()
        self._on_mode_changed(self.mode_combo.currentText())

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.view)
        splitter.addWidget(self.palette)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(serial_bar)
        main_layout.addWidget(splitter)

        self.setCentralWidget(main_widget)
        set_param_apply_handler(self._apply_param_to_hardware)

    def _on_mode_changed(self, text):
        developer_mode = (text == "Developer Mode")
        self.scene.set_developer_mode(developer_mode)
        for item in self.scene.items():
            if isinstance(item, NodeItem) and hasattr(item, "free_mode"):
                item.free_mode = not developer_mode


    def run_business_logic(self, src, src_port, dst, dst_port):
        print(f"🔄 >> 执行业务逻辑: 数据从 {src}:Out{src_port+1} 传输到 {dst}:In{dst_port+1}...")
        src_port_num = _resolve_port_number(src, src_port, "out")
        dst_port_num = _resolve_port_number(dst, dst_port, "in")
        if src_port_num is None or dst_port_num is None:
            print(f"[route] skip: unresolved port mapping src={src}:{src_port} dst={dst}:{dst_port}")
            return
        self._apply_routing(dst_port_num, src_port_num, f"{src}:Out{src_port+1} -> {dst}:In{dst_port+1}")

    def handle_connection_removed(self, src, src_port, dst, dst_port):
        print(f"🧹 >> 清理业务逻辑: 断开 {src}:Out{src_port+1} 到 {dst}:In{dst_port+1} 的数据流...")
        dst_port_num = _resolve_port_number(dst, dst_port, "in")
        if dst_port_num is None:
            print(f"[route] skip: unresolved port mapping dst={dst}:{dst_port}")
            return
        src_port_num = pn.VOID_BOOL if dst_port_num >= 64 else pn.VOID
        self._apply_routing(dst_port_num, src_port_num, f"{dst}:In{dst_port+1} cleared")



    def _ensure_router(self):
        if not self.port_ctrl.is_open():
            print("[route] serial port not open, routing not sent")
            return None
        if self.router is None:
            self.router=self.port_ctrl.hw_controller.router
            # self.router_bus = PortBus(self.port_ctrl)
            # self.router = module_signal_router.ModuleSignalRouter(self.router_bus)
        return self.router

    def _apply_routing(self, dst_port_num, src_port_num, label):
        router = self._ensure_router()
        if router is None:
            return
        try:
            router.set_routing(dst_port_num, src_port_num)
            router.upload()
            print(f"[route] sent: {label} ({src_port_num} -> {dst_port_num})")
        except Exception as exc:
            print(f"[route] failed: {label}: {exc}")

    def _resolve_module_identity(self, node):
        if isinstance(node, MoudlePID):
            return "PID", node.index
        if isinstance(node, MoudleAccumulator):
            return "ACC", node.index
        if isinstance(node, MoudleScaler):
            return "SCLR", node.index
        if isinstance(node, ModuleFIRFilter):
            return "FIR", node.index
        if isinstance(node, ModuleIIRFilter):  # 新增
            return "IIR", node.index
        if isinstance(node, MoudleLinerTransformer):
            return "LTRN", node.index
        if isinstance(node, MoudlePDHFSM):
            return "PDH", node.index
        if isinstance(node, MoudleSCLOFSM):
            return "SCLO", node.index
        return None, None

    def _apply_param_to_hardware(self, node, params):
        module_type, module_index = self._resolve_module_identity(node)
        if module_type is None:
            return
        try:
            self.port_ctrl.send_param(module_type, module_index, params)
            for key, value in params.items():
                print(f"[param] sent {node.name}.{key} = {value}")
        except Exception as exc:
            print(f"[param] failed {node.name}: {exc}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
