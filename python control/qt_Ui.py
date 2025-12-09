# 导入系统模块
import sys
import random
# 导入PySide6的QtWidgets模块中的相关组件
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QListWidget, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem,
                               QSplitter, QGraphicsEllipseItem)
# 导入PySide6的QtCore模块中的相关类
from PySide6.QtCore import Qt, QMimeData, QPointF, QRectF, Signal, QObject
# 导入PySide6.QtGui模块中的相关类
from PySide6.QtGui import QDrag, QPainter, QPen, QBrush, QPainterPath, QColor, QFont

# --- 1. 信号通信类 ---
class NodeSignals(QObject):
    """
    自定义信号类，用于在节点之间传递连接创建和删除的信号

    Signals:
        connection_created: 当创建新连接时发出，参数为(源节点名, 源端口索引, 目标节点名, 目标端口索引)
        connection_removed: 当删除连接时发出，参数为(源节点名, 源端口索引, 目标节点名, 目标端口索引)
    """
    connection_created = Signal(str, int, str, int)
    connection_removed = Signal(str, int, str, int)

# --- 3. 端口类 (Port) ---
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
        unique_id = id(self.parent_node) + self.index
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
            start_node_top = self.parent_node.scenePos().y() - self.parent_node.height / 2
            return start_node_top - self.manual_bypass_y
        base_offset = 30
        increment = 7
        return base_offset + (self.index * increment)

    def get_reverse_h_extend(self):
        if self.manual_reverse_h_extend is not None:
            return self.manual_reverse_h_extend
        base_extend = 30
        increment = 7
        return base_extend + (self.index * increment)

# --- 4. 节点类 (Node) ---
class NodeItem(QGraphicsItem):
    def __init__(self, name, position, num_inputs=2, num_outputs=2):
        super().__init__()
        self.name = name
        self.width = 140
        self.height = 180
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.setPos(position)

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.in_ports = []
        self.out_ports = []
        self.edges = []

        self._create_ports()

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
            text_rect = QRectF(-self.width/2 + 10, port_pos.y() - 8, 40, 16)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"In{i+1}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width/2 - 50, port_pos.y() - 8, 40, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"Out{i+1}")

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for edge in self.edges:
                edge.update_path()
        return super().itemChange(change, value)

# --- 5. 连线类 (Edge) ---
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
        s_node = self.start_port.parent_node
        e_node = self.end_port. parent_node
        s_top = s_node.scenePos().y() - s_node.height / 2
        s_bottom = s_node.scenePos().y() + s_node.height / 2
        e_top = e_node. scenePos().y() - e_node.height / 2
        e_bottom = e_node.scenePos().y() + e_node.height / 2
        return (s_top, s_bottom, e_top, e_bottom, s_node.width, s_node.height)

    def _calculate_bypass_y(self, bypass_offset):
        """
        根据规则计算绕行的 y 坐标，返回一个 y 值。
        新规则：当垂直距离超过节点高度时，横线位于目标节点顶部上方，
        并且根据起始端口的索引添加递增的偏移量，避免线条重叠。
        """
        p1_node = self.start_port. parent_node
        p2_node = self.end_port. parent_node
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
        port_spacing = 10
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
        s_node = self.start_port.parent_node
        e_node = self.end_port.parent_node
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
                    self.control_points[0].setPos(QPointF(vertical_x, p1.y()))
                    self.control_points[1].setPos(QPointF(vertical_x, p2.y()))
            elif dy > node_h: 
                h_extend = self.start_port.get_reverse_h_extend()
                bypass_offset = self.start_port.get_bypass_offset()
                bypass_y = self._calculate_bypass_y(bypass_offset)

                if len(self.control_points) >= 3:
                    self.control_points[0].setPos(QPointF(p1.x() + h_extend/2, p1.y()))
                    self.control_points[1].setPos(QPointF(p1.x() + h_extend, (p1.y() + bypass_y) / 2))
                    self.control_points[2].setPos(QPointF((p1.x() + h_extend + p2.x() - h_extend) / 2 + self.reverse_horizontal_offset, bypass_y))
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
                        self. control_points[0].setPos(QPointF(p1.x() + h_extend/2, p1.y()))
                        self.control_points[1].setPos(QPointF(p1.x() + h_extend, (p1.y() + bypass_y) / 2))
                        self.control_points[2].setPos(QPointF((p1.x() + h_extend + p2.x() - h_extend) / 2 + self.reverse_horizontal_offset, bypass_y))
                else:
                    turn_distance = self.start_port.get_turn_distance()
                    turn_x = p1.x() + turn_distance

                    y1_with_offset = p1.y() + self.horizontal_offset
                    y2_with_offset = p2.y() + self.horizontal_offset
                    mid_v_y = (y1_with_offset + y2_with_offset) / 2

                    if len(self.control_points) >= 3:
                        self.control_points[0]. setPos(QPointF((p1.x() + turn_x) / 2, p1.y()))
                        self.control_points[1].setPos(QPointF(turn_x, mid_v_y))
                        self.control_points[2].setPos(QPointF((turn_x + p2.x()) / 2, p2.y()))

    def hoverEnterEvent(self, event):
        for edge in self.start_port.connections:
            for cp in edge.control_points:
                cp.setVisible(True)

        pen = self.pen()
        pen.setWidth(4)
        self.setPen(pen)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        for edge in self.start_port.connections:
            for cp in edge.control_points:
                if not cp.isSelected():
                    cp.setVisible(False)

        pen = self.pen()
        pen.setWidth(3)
        self.setPen(pen)
        super().hoverLeaveEvent(event)

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

        if self in self.start_port.parent_node.edges:
            self.start_port.parent_node.edges.remove(self)
        if self in self.end_port.parent_node.edges:
            self. end_port.parent_node. edges.remove(self)

        if was_first and self.start_port.connections:
            first_edge = self.start_port.connections[0]
            first_edge._create_control_points()

        if self.scene():
            self.scene().removeItem(self)

# --- 6. 场景类 (Scene) ---
class DiagramScene(QGraphicsScene):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.temp_line = None
        self.start_port = None

        self.setBackgroundBrush(QBrush(QColor("#1E1E1E")))
        self.setSceneRect(0, 0, 5000, 5000)

    def mousePressEvent(self, event):
        items = self.items(event.scenePos())
        port = None
        for item in items:
            if isinstance(item, PortItem):
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

            s_node = self.start_port.parent_node
            # 如果鼠标悬停在某端口上则优先以该端口决定预览（否则以鼠标位置估算）
            hovered_items = self.items(event.scenePos())
            hovered_port = None
            for it in hovered_items:
                if isinstance(it, PortItem) and it is not self.start_port:
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
                if isinstance(item, PortItem):
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

        if end_port.parent_node == start_port.parent_node:
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

        self.start_port.parent_node.edges.append(edge)
        end_port.parent_node.edges.append(edge)

        if self.temp_line:
            self.removeItem(self.temp_line)
        self.temp_line = None

        src_name = self.start_port.parent_node.name
        src_port_idx = self.start_port.index
        dst_name = end_port.parent_node.name
        dst_port_idx = end_port.index

        self.start_port = None

        direction = "反向(绕行)" if edge._is_reverse_connection() else "正向"
        print(f"✅ 连线建立: [{src_name}:Out{src_port_idx+1}] --> [{dst_name}:In{dst_port_idx+1}] ({direction}, 颜色: {edge.color})")
        self.signals.connection_created.emit(src_name, src_port_idx, dst_name, dst_port_idx)

    def remove_connection(self, input_port):
        if not input_port.has_connection():
            return

        edge = input_port.get_connection()

        src_name = edge.start_port.parent_node.name
        src_port_idx = edge.start_port.index
        dst_name = edge.end_port.parent_node.name
        dst_port_idx = edge.end_port.index
        edge_color = edge.color

        edge.remove()

        print(f"🗑️ 连线已断开: [{src_name}:Out{src_port_idx+1}] -X-> [{dst_name}:In{dst_port_idx+1}] (颜色: {edge_color})")
        self.signals.connection_removed.emit(src_name, src_port_idx, dst_name, dst_port_idx)

# --- 7. 画布视图 (View) ---
class DiagramView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        component_name = event.mimeData().text()
        position = self.mapToScene(event.position().toPoint())

        port_config = {
            "数据源 A": (8, 8),
            "处理器 B": (8, 8),
            "过滤器 C": (8, 8),
            "AI模型 D": (8, 8),
            "终端显示 E": (8, 8),
        }

        num_in, num_out = port_config.get(component_name, (2, 2))
        node = NodeItem(component_name, position, num_in, num_out)
        self.scene().addItem(node)

        event.acceptProposedAction()

# --- 8. 右侧组件列表 (Palette) ---
class ComponentPalette(QListWidget):
    def __init__(self):
        super().__init__()
        self.setDragEnabled(True)
        self.setStyleSheet("font-size: 14px; padding: 5px;")

        items = ["数据源 A", "处理器 B", "过滤器 C", "AI模型 D", "终端显示 E"]
        for i in items:
            self.addItem(i)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        mimeData = QMimeData()
        mimeData.setText(item.text())

        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec(Qt.CopyAction)

# --- 9. 主窗口 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 节点流编辑器 - 支持复杂绕行规则")
        self.resize(1200, 800)

        self.signals = NodeSignals()
        self.signals.connection_created.connect(self.run_business_logic)
        self.signals.connection_removed.connect(self.handle_connection_removed)

        self.scene = DiagramScene(self.signals)
        self.view = DiagramView(self.scene)
        self.palette = ComponentPalette()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.view)
        splitter.addWidget(self.palette)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def run_business_logic(self, src, src_port, dst, dst_port):
        print(f"🔄 >> 执行业务逻辑: 数据从 {src}:Out{src_port+1} 传输到 {dst}:In{dst_port+1}...")

    def handle_connection_removed(self, src, src_port, dst, dst_port):
        print(f"🧹 >> 清理业务逻辑: 断开 {src}:Out{src_port+1} 到 {dst}:In{dst_port+1} 的数据流...")

# 程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())