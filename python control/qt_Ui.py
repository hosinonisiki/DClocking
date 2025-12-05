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

    Attributes:
        COLOR_POOL: 颜色池，用于为输出端口分配不同颜色
        parent_node: 父节点引用
        port_type: 端口类型 ('in' 或 'out')
        index: 端口索引
        radius: 端口半径
        connections: 连接到此端口的边列表
        line_color: 连接线颜色（仅对输出端口）
        brush: 画刷，用于填充端口颜色
    """
    COLOR_POOL = [
        "#E74C3C",  "#3498DB",  "#2ECC71",  "#F39C12",  "#9B59B6",
        "#1ABC9C",  "#E91E63",  "#FF5722",  "#00BCD4",  "#FFEB3B",
        "#8BC34A",  "#FF9800",  "#673AB7",  "#03A9F4",  "#CDDC39",
        "#FFC107",  "#009688",  "#795548",  "#607D8B",
    ]

    def __init__(self, parent, port_type, index, radius=6):
        """
        初始化端口

        Args:
            parent: 父节点
            port_type: 端口类型 ('in' 或 'out')
            index: 端口索引
            radius: 端口半径，默认为6
        """
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
        """
        为输出端口分配唯一颜色

        Returns:
            str: 分配的颜色值
        """
        unique_id = id(self.parent_node) + self.index
        color_index = unique_id % len(self.COLOR_POOL)
        return self.COLOR_POOL[color_index]

    def boundingRect(self):
        """
        返回端口的边界矩形，用于确定端口的可视区域

        Returns:
            QRectF: 端口的边界矩形
        """
        return QRectF(-self.radius, -self.radius, 2*self.radius, 2*self.radius)

    def paint(self, painter, option, widget):
        """
        绘制端口图形

        Args:
            painter: 画家对象，用于执行绘制操作
            option: 绘制选项
            widget: 目标控件
        """
        painter.setBrush(self.brush)  # 设置填充画刷
        painter.setPen(QPen(Qt.white, 1))  # 设置白色边框，宽度1像素
        painter.drawEllipse(-self.radius, -self.radius, 2*self.radius, 2*self.radius)  # 绘制圆形端口

    def has_connection(self):
        """
        检查端口是否有连接

        Returns:
            bool: 如果端口有连接则返回True，否则返回False
        """
        return len(self.connections) > 0

    def get_connection(self):
        """
        获取端口的第一个连接

        Returns:
            EdgeItem或None: 如果端口有连接则返回第一个连接，否则返回None
        """
        return self.connections[0] if self.connections else None

    def get_turn_distance(self):
        """
        获取正向连接的转弯距离

        Returns:
            int: 转弯距离
        """
        if self.manual_turn_distance is not None:
            return self.manual_turn_distance
        base_distance = 30
        increment = 5
        return base_distance + (self.index * increment)

    def get_bypass_offset(self):
        """
        获取反向连接的绕行偏移量

        Returns:
            int: 绕行偏移量
        """
        if self.manual_bypass_y is not None:
            # 如果是手动设置的绝对Y坐标，需要转换为偏移
            start_node_top = self.parent_node.scenePos().y() - self.parent_node.height / 2
            return start_node_top - self.manual_bypass_y
        base_offset = 30
        increment = 5
        return base_offset + (self.index * increment)

    def get_reverse_h_extend(self):
        """
        获取反向连接的水平扩展距离

        Returns:
            int: 水平扩展距离
        """
        if self.manual_reverse_h_extend is not None:
            return self.manual_reverse_h_extend
        base_extend = 30
        increment = 5
        return base_extend + (self.index * increment)

# --- 4. 节点类 (Node) ---
class NodeItem(QGraphicsItem):
    """
    表示节点的图形项类，具有指定数量的输入和输出端口

    Attributes:
        name: 节点名称
        width: 节点宽度
        height: 节点高度
        num_inputs: 输入端口数量
        num_outputs: 输出端口数量
        in_ports: 输入端口列表
        out_ports: 输出端口列表
        edges: 连接到此节点的边列表
    """
    def __init__(self, name, position, num_inputs=2, num_outputs=2):
        """
        初始化节点

        Args:
            name: 节点名称
            position: 节点位置
            num_inputs: 输入端口数量，默认为2
            num_outputs: 输出端口数量，默认为2
        """
        super().__init__()
        self.name = name
        self.width = 140
        self.height = 180
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.setPos(position)  # 设置节点的位置

        self.setFlag(QGraphicsItem.ItemIsMovable)  # 允许图形项被鼠标拖拽移动
        self.setFlag(QGraphicsItem.ItemIsSelectable)  # 允许图形项被鼠标选中
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)  # 允许图形项在位置变化时发送通知

        self.in_ports = []
        self.out_ports = []
        self.edges = []

        self._create_ports()

    def _create_ports(self):
        """
        创建节点的输入和输出端口，并按均匀分布排列在节点两侧
        """
        if self.num_inputs > 0:  # 节点的输入端口数量
            port_spacing_in = self.height / (self.num_inputs + 1)
        if self.num_outputs > 0:  # 节点的输出端口数量
            port_spacing_out = self.height / (self.num_outputs + 1)

        for i in range(self.num_inputs):
            port = PortItem(self, 'in', i)  # 创建输入端口实例（关联当前节点、类型、索引）
            y_offset = -self.height/2 + port_spacing_in * (i + 1)  # 计算Y轴偏移
            port.setPos(-self.width/2, y_offset)  # 定位到节点左侧
            self.in_ports.append(port)  # 加入输入端口列表

        for i in range(self.num_outputs):
            port = PortItem(self, 'out', i)  # 创建输出端口实例
            y_offset = -self.height/2 + port_spacing_out * (i + 1)  # 计算Y轴偏移
            port.setPos(self.width/2, y_offset)  # 定位到节点右侧
            self.out_ports.append(port)  # 加入输出端口列表

    def boundingRect(self):
        """
        返回节点的边界矩形，用于确定节点的可视区域

        Returns:
            QRectF: 节点的边界矩形
        """
        return QRectF(-self.width/2, -self.height/2, self.width, self.height)

    def paint(self, painter, option, widget):
        """
        绘制节点外观

        Args:
            painter: 画家对象，用于执行绘制操作
            option: 绘制选项
            widget: 目标控件
        """
        rect = self.boundingRect()  # 获取图形项（节点 / 端口）的边界矩形

        painter.setBrush(QBrush(QColor("#2C3E50")))  # 设置填充画笔（深蓝色背景）
        painter.setPen(QPen(Qt.white, 2))  # 设置轮廓画笔（白色、2px宽边框）
        painter.drawRoundedRect(rect, 8, 8)  # 绘制圆角矩形（圆角半径8px）

        # 设置标题文字样式：白色、加粗、10号字体
        painter.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)

        # 定义标题区域：节点顶部25px高度的矩形
        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)
        # 在标题区域居中绘制节点名称（self.name）
        painter.drawText(title_rect, Qt.AlignCenter, self.name)

        font.setBold(False)  # 取消加粗
        font.setPointSize(8)  # 字号改为8号
        painter.setFont(font)

        # 为节点的输入 / 输出端口绘制编号文本（如 In1/Out1）
        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()  # 端口在节点局部坐标中的位置（X/Y），决定文本的垂直对齐基准
            text_rect = QRectF(-self.width/2 + 10, port_pos.y() - 8, 40, 16)  # Y轴方向向下
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"In{i+1}")

        for i, port in enumerate(self.out_ports):
            port_pos = port.pos()
            text_rect = QRectF(self.width/2 - 50, port_pos.y() - 8, 40, 16)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"Out{i+1}")

    def itemChange(self, change, value):
        """
        处理节点变化事件，当节点位置改变时更新连接到该节点的边的路径

        Args:
            change: 变化类型
            value: 变化值

        Returns:
            QVariant: 处理结果
        """
        # 是 itemChange() 方法的触发类型，表示「图形项（端口 / 节点）的位置即将发生变化」（还未完成移动）。
        if change == QGraphicsItem.ItemPositionChange:
            # 遍历当前端口/节点关联的所有连线
            for edge in self.edges:
                # 调用连线的更新路径方法，重新计算并绘制连线
                edge.update_path()
        # 调用父类方法，完成位置变更的默认逻辑（必须保留，否则位置无法更新）
        return super().itemChange(change, value)

# --- 5. 连线类 (Edge) - 支持拖动横线和竖线 ---
class EdgeItem(QGraphicsPathItem):
    """
    表示两个端口之间的连接线

    Attributes:
        start_port: 起始端口
        end_port: 结束端口
        color: 连接线颜色
        control_points: 控制点列表
        horizontal_offset: 正向连接水平段的Y偏移
        reverse_horizontal_offset: 反向连接水平段的X偏移
    """
    def __init__(self, start_port, end_port):
        """
        初始化连接线

        Args:
            start_port: 起始端口
            end_port: 结束端口
        """
        super().__init__()
        self.start_port = start_port
        self.end_port = end_port
        self.setZValue(-1)  # 用于设置图形项在 Z 轴（垂直于绘图平面的方向）的显示层级，数值越小，图形项越靠下

        self.color = start_port.line_color

        pen = QPen(QColor(self.color))
        pen.setWidth(3)
        self.setPen(pen)

        self.control_points = []
        self.horizontal_offset = 0  # 正向连接水平段的Y偏移
        self.reverse_horizontal_offset = 0  # 反向连接水平段的X偏移

        start_port.connections.append(self)  # 将当前对象（self）添加到两个端口对象（start_port/end_port）的连接列表中
        end_port.connections.append(self)

        self.setFlag(QGraphicsItem.ItemIsSelectable)  # 为当前图形项开启「可选中」特性。
        self.setAcceptHoverEvents(True)  # 允许当前图形项接收鼠标悬停事件

        self.update_path()

    def _is_reverse_connection(self):
        """
        判断是否为反向连接（目标节点在起始节点左侧）

        Returns:
            bool: 如果是反向连接返回True，否则返回False
        """
        p1 = self.start_port.scenePos()  # 返回图形项在场景坐标系中的绝对位置
        p2 = self.end_port.scenePos()
        return p2.x() < p1.x()

    def _calculate_reverse_route(self, p1, p2):
        """
        计算反向连接的绕行路径

        Args:
            p1: 起始点坐标
            p2: 结束点坐标

        Returns:
            list: 路径点坐标列表
        """
        # 计算起始/目标节点的上下边界（场景坐标）
        start_node_top = self.start_port.parent_node.scenePos().y() - self.start_port.parent_node.height / 2
        start_node_bottom = self.start_port.parent_node.scenePos().y() + self.start_port.parent_node.height / 2
        end_node_top = self.end_port.parent_node.scenePos().y() - self.end_port.parent_node.height / 2
        end_node_bottom = self.end_port.parent_node.scenePos().y() + self.end_port.parent_node.height / 2

        bypass_offset = self.start_port.get_bypass_offset()
        # 决定绕行是在上方还是下方：根据被连接的输入端口在节点本地坐标中的Y值判断
        # 如果输入端口本地坐标为正（位于节点下方），则绕下方；否则绕上方
        if self.end_port.pos().y() > 0:
            # 绕下方：选择两个节点底部中较大的作为基准，然后向下偏移
            bypass_y = max(start_node_bottom, end_node_bottom) + bypass_offset
        else:
            # 绕上方：选择两个节点顶部中较小的作为基准，然后向上偏移
            bypass_y = min(start_node_top, end_node_top) - bypass_offset

        h_extend = self.start_port.get_reverse_h_extend()
        target_h_extend = h_extend

        route = [
            p1,
            QPointF(p1.x() + h_extend, p1.y()),
            QPointF(p1.x() + h_extend, bypass_y),
            QPointF(p2.x() - target_h_extend + self.reverse_horizontal_offset, bypass_y),
            QPointF(p2.x() - target_h_extend, p2.y()),
            p2
        ]
        return route

    def update_path(self):
        """
        更新连接线的路径，根据连接方向（正向或反向）计算不同的路径形状
        """
        if not self.start_port or not self.end_port:
            return

        p1 = self.start_port.scenePos()
        p2 = self.end_port.scenePos()

        path = QPainterPath()
        path.moveTo(p1)

        if self._is_reverse_connection():
            route = self._calculate_reverse_route(p1, p2)
            for point in route[1:]:
                path.lineTo(point)
        else:
            # 正向连接：支持水平段偏移
            turn_distance = self.start_port.get_turn_distance()
            turn_x = p1.x() + turn_distance

            # 计算水平段的Y坐标（可能有偏移）
            y1_with_offset = p1.y() + self.horizontal_offset
            y2_with_offset = p2.y() + self.horizontal_offset

            path.lineTo(turn_x, p1.y())
            path.lineTo(turn_x, y1_with_offset)
            path.lineTo(turn_x, y2_with_offset)
            path.lineTo(turn_x, p2.y())
            path.lineTo(p2.x(), p2.y())

        self.setPath(path)

        # 更新控制点位置
        if self.control_points:
            p1 = self.start_port.scenePos()
            p2 = self.end_port.scenePos()

            if self._is_reverse_connection():
                h_extend = self.start_port.get_reverse_h_extend()
                bypass_offset = self.start_port.get_bypass_offset()

                start_node_top = self.start_port.parent_node.scenePos().y() - self.start_port.parent_node.height / 2
                start_node_bottom = self.start_port.parent_node.scenePos().y() + self.start_port.parent_node.height / 2
                end_node_top = self.end_port.parent_node.scenePos().y() - self.end_port.parent_node.height / 2
                end_node_bottom = self.end_port.parent_node.scenePos().y() + self.end_port.parent_node.height / 2

                # 同样根据目标输入端口的位置决定绕行方向（上/下）
                if self.end_port.pos().y() > 0:
                    bypass_y = max(start_node_bottom, end_node_bottom) + bypass_offset
                else:
                    bypass_y = min(start_node_top, end_node_top) - bypass_offset

                if len(self.control_points) >= 3:
                    # 控制点分别位于起始水平段中点、转折处以及目标水平段中点
                    self.control_points[0].setPos(QPointF(p1.x() + h_extend/2, p1.y()))
                    self.control_points[1].setPos(QPointF(p1.x() + h_extend, (p1.y() + bypass_y) / 2))
                    self.control_points[2].setPos(QPointF((p1.x() + h_extend + p2.x() - h_extend) / 2 + self.reverse_horizontal_offset, bypass_y))
            else:
                turn_distance = self.start_port.get_turn_distance()
                turn_x = p1.x() + turn_distance

                y1_with_offset = p1.y() + self.horizontal_offset
                y2_with_offset = p2.y() + self.horizontal_offset
                mid_v_y = (y1_with_offset + y2_with_offset) / 2

                if len(self.control_points) >= 3:
                    self.control_points[0].setPos(QPointF((p1.x() + turn_x) / 2, p1.y()))
                    self.control_points[1].setPos(QPointF(turn_x, mid_v_y))
                    self.control_points[2].setPos(QPointF((turn_x + p2.x()) / 2, p2.y()))

    def hoverEnterEvent(self, event):
        """
        处理鼠标悬停进入事件，高亮显示连线并显示控制点

        Args:
            event: 鼠标事件
        """
        for edge in self.start_port.connections:
            for cp in edge.control_points:
                cp.setVisible(True)

        pen = self.pen()
        pen.setWidth(4)
        self.setPen(pen)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        处理鼠标悬停离开事件，恢复连线正常显示并隐藏未选中的控制点

        Args:
            event: 鼠标事件
        """
        for edge in self.start_port.connections:
            for cp in edge.control_points:
                if not cp.isSelected():
                    cp.setVisible(False)

        pen = self.pen()
        pen.setWidth(3)
        self.setPen(pen)
        super().hoverLeaveEvent(event)

    def remove(self):
        """
        删除连线及其相关的控制点，并更新相关数据结构
        """
        was_first = self.start_port.connections.index(self) == 0 if self in self.start_port.connections else False

        for cp in self.control_points:
            if cp.scene():
                cp.scene().removeItem(cp)
        self.control_points.clear()

        if self in self.start_port.connections:
            self.start_port.connections.remove(self)
        if self in self.end_port.connections:
            self.end_port.connections.remove(self)

        if self in self.start_port.parent_node.edges:
            self.start_port.parent_node.edges.remove(self)
        if self in self.end_port.parent_node.edges:
            self.end_port.parent_node.edges.remove(self)

        if was_first and self.start_port.connections:
            first_edge = self.start_port.connections[0]
            first_edge._create_control_points()

        if self.scene():
            self.scene().removeItem(self)

# --- 6. 场景类 (Scene) ---
class DiagramScene(QGraphicsScene):
    """
    场景类负责管理所有的图形项和交互逻辑

    Attributes:
        signals: 信号对象用于发射连接事件
        temp_line: 临时连线
        start_port: 起始端口
    """
    def __init__(self, signals):
        """
        初始化场景

        Args:
            signals: 信号对象
        """
        super().__init__()
        self.signals = signals
        self.temp_line = None
        self.start_port = None

        self.setBackgroundBrush(QBrush(QColor("#1E1E1E")))
        self.setSceneRect(0, 0, 5000, 5000)

    def mousePressEvent(self, event):
        """
        处理鼠标按下事件

        Args:
            event: 鼠标事件
        """
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
        """
        处理鼠标移动事件，在创建连接过程中实时更新临时连线的路径

        Args:
            event: 鼠标事件
        """
        if self.temp_line and self.start_port:
            p1 = self.start_port.scenePos()
            p2 = event.scenePos()

            path = QPainterPath()
            path.moveTo(p1)

            if p2.x() < p1.x():
                h_extend = self.start_port.get_reverse_h_extend()
                bypass_offset = self.start_port.get_bypass_offset()
                # 根据当前鼠标位置相对于起始端口决定预览绕行在上方还是下方
                start_node_top = self.start_port.parent_node.scenePos().y() - self.start_port.parent_node.height / 2
                start_node_bottom = self.start_port.parent_node.scenePos().y() + self.start_port.parent_node.height / 2
                if p2.y() > p1.y():
                    # 预览绕下方
                    bypass_y = max(start_node_bottom, p2.y()) + bypass_offset
                else:
                    # 预览绕上方
                    bypass_y = min(start_node_top, p2.y()) - bypass_offset

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
        """
        处理鼠标释放事件，确定最终连接目标或取消连接操作

        Args:
            event: 鼠标事件
        """
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
        """
        验证连接是否有效

        Args:
            start_port: 起始端口
            end_port: 结束端口

        Returns:
            bool: 如果连接有效返回True，否则返回False
        """
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
        """
        取消连接操作，清理临时元素
        """
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None

        if self.start_port:
            print(f"⚠️ 连接已取消: 未找到有效的目标端口")
            self.start_port = None

    def finalize_connection(self, end_port):
        """
        完成连接操作，创建新的连接线并发射连接创建信号

        Args:
            end_port: 结束端口
        """
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
        """
        删除现有连接并发射连接移除信号

        Args:
            input_port: 输入端口
        """
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
    """
    视图类显示场景内容并处理拖放事件，启用抗锯齿渲染

    Attributes:
        None
    """
    def __init__(self, scene):
        """
        初始化视图

        Args:
            scene: 关联的场景对象
        """
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """
        处理拖拽进入事件

        Args:
            event: 拖拽事件
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """
        处理拖拽移动事件

        Args:
            event: 拖拽事件
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """
        处理拖拽放置事件，允许从组件面板拖拽组件到场景中创建节点

        Args:
            event: 拖拽事件
        """
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
    """
    组件面板类，列出可用的节点类型，启用拖拽功能

    Attributes:
        None
    """
    def __init__(self):
        """
        初始化组件面板
        """
        super().__init__()
        self.setDragEnabled(True)
        self.setStyleSheet("font-size: 14px; padding: 5px;")

        items = ["数据源 A", "处理器 B", "过滤器 C", "AI模型 D", "终端显示 E"]
        for i in items:
            self.addItem(i)

    def startDrag(self, supportedActions):
        """
        实现拖拽操作，将选中项目的文本数据传递给拖拽操作

        Args:
            supportedActions: 支持的拖拽操作
        """
        item = self.currentItem()
        mimeData = QMimeData()
        mimeData.setText(item.text())

        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec(Qt.CopyAction)

# --- 9. 主窗口 ---
class MainWindow(QMainWindow):
    """
    主窗口类，整合所有组件

    Attributes:
        signals: 信号对象
        scene: 场景对象
        view: 视图对象
        palette: 组件面板对象
    """
    def __init__(self):
        """
        初始化主窗口
        """
        super().__init__()
        self.setWindowTitle("PySide6 节点流编辑器 - 支持拖动横竖线")
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
        """
        处理连接创建事件的业务逻辑函数

        Args:
            src: 源节点名
            src_port: 源端口索引
            dst: 目标节点名
            dst_port: 目标端口索引
        """
        print(f"🔄 >> 执行业务逻辑: 数据从 {src}:Out{src_port+1} 传输到 {dst}:In{dst_port+1}...")

    def handle_connection_removed(self, src, src_port, dst, dst_port):
        """
        处理连接删除事件的业务逻辑函数

        Args:
            src: 源节点名
            src_port: 源端口索引
            dst: 目标节点名
            dst_port: 目标端口索引
        """
        print(f"🧹 >> 清理业务逻辑: 断开 {src}:Out{src_port+1} 到 {dst}:In{dst_port+1} 的数据流...")

# 程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())