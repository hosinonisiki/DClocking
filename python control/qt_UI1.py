# 导入系统模块
from platform import node
import sys
import random
# 导入PySide6的QtWidgets模块中的相关组件
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QListWidget, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem,
                               QSplitter, QGraphicsEllipseItem, QPushButton, QComboBox)
# 导入PySide6的QtCore模块中的相关类
from PySide6.QtCore import Qt, QMimeData, QPointF, QRectF, Signal, QObject, QByteArray, QPoint
# 导入PySide6.QtGui模块中的相关类
from PySide6.QtGui import QDrag, QPainter, QPen, QBrush, QPainterPath, QColor, QFont, QPixmap, QImage, QCursor
from qt_moudle import (PortItem, NodeItem, MoudlePID, MoudleAccumulator, MoudleBase, 
                         MoudleScaler, ModuleFIRFilter, MoudleSCLOFSM, MoudlePDHFSM,
                         MoudleLinerTransformer, CompositeMoudle, SINGenerator, DigitalControlledOscillator,
                         moudle_factory, moudle_maxm)
from qt_Port import Port

from PySide6.QtSerialPort import QSerialPort

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
        super().__init__(None, port_type, index)
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

        pen = QPen(QColor(self.color))
        pen.setWidth(3)
        self.setPen(pen)

        self.control_points = []
        self. horizontal_offset = 0
        self.reverse_horizontal_offset = 0

        start_port.connections.append(self)
        end_port.connections.append(self)

        self. setFlag(QGraphicsItem. ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        self.update_path()

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
        pen.setWidth(4)
        self.setPen(pen)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        pen = self.pen()
        pen.setWidth(3)
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

class DiagramScene(QGraphicsScene):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.temp_line = None
        self.start_port = None

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
                pen.setStyle(Qt.DashLine)
                pen.setWidth(2)
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
            else:
                p2_ref = p2

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

    def _is_valid_connection(self, start_port, end_port):
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
        self._used_indices = {k : set() for k in moudle_factory}
        self._maxnum = {k : moudle_maxm.get(k) for k in moudle_maxm}
        self._drag_candidate_node = None
        self._drag_start_pos = None
        self._is_dragging_view = False
        self._view_drag_start_pos = None
        self.scale_factor = 1.0
        self.setRenderHint(QPainter.Antialiasing)
        self.setAcceptDrops(True)
        self.sync_scene_to_viewport()
        self.update_border_ports()

    def sync_scene_to_viewport(self):
        scene = self.scene()
        if not scene:
            return
        
        top_left = self.mapToScene(self.viewport().rect().topLeft())
        bottom_right = self.mapToScene(self.viewport().rect().bottomRight())

        rect = QRectF(top_left, bottom_right)
        scene.setSceneRect(rect)

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
        #删除组件
        for edge in list(node.edges):
            edge.remove()

        if node.scene():
            self._free_index(node.component_name, int(node.index))
            node.scene().removeItem(node)

        node.edges.clear()
        
        self.scene().update()
        self.viewport().update()

        print(f"🗑️ 已移除组件: {node.name}")
    
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

        items = ["PID控制器", "累加器", "三角函数运算器", "反三角函数运算器", "线性缩放器", "FIR滤波器",  "线性变换器", "混频器", "解卷绕器", "PDH状态机",
                 "LO自动校准状态机", "正弦波发生器", "数字控制振荡器"]
        for i in items:
            self.addItem(i)

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

        self.comboBox = QComboBox()
        self.comboBox.setFixedWidth(180)

        self.connect_btn = QPushButton("连接")
        self.connect_btn.setFixedWidth(80)

        serial_bar = QWidget()
        serial_bar.setFixedHeight(40)
        serial_layout = QHBoxLayout(serial_bar)
        serial_layout.setContentsMargins(8, 4, 8, 4)
        serial_layout.addStretch()
        serial_layout.addWidget(self.comboBox)
        serial_layout.addWidget(self.connect_btn)
        serial_layout.addStretch()
        self.serial_port = QSerialPort(self)
        self.port_ctrl = Port(self, self.serial_port)
        self.port_ctrl.scan_ports(force_update=True)

        self.signals = NodeSignals()
        self.signals.connection_created.connect(self.run_business_logic)
        self.signals.connection_removed.connect(self.handle_connection_removed)

        self.scene = DiagramScene(self.signals)
        self.view = DiagramView(self.scene)
        self.palette = ComponentPalette()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.view)
        splitter.addWidget(self.palette)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(serial_bar)
        main_layout.addWidget(splitter)

        self.setCentralWidget(main_widget)

    def run_business_logic(self, src, src_port, dst, dst_port):
        print(f"🔄 >> 执行业务逻辑: 数据从 {src}:Out{src_port+1} 传输到 {dst}:In{dst_port+1}...")

    def handle_connection_removed(self, src, src_port, dst, dst_port):
        print(f"🧹 >> 清理业务逻辑: 断开 {src}:Out{src_port+1} 到 {dst}:In{dst_port+1} 的数据流...")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
