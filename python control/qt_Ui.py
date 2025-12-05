# 导入系统模块
import sys
import random
# 导入PySide6的QtWidgets模块中的相关组件
from PySide6. QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QListWidget, QGraphicsView, QGraphicsScene, 
                               QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem,
                               QSplitter, QGraphicsEllipseItem)
# 导入PySide6的QtCore模块中的相关类
from PySide6.QtCore import Qt, QMimeData, QPointF, QRectF, Signal, QObject
# 导入PySide6. QtGui模块中的相关类
from PySide6. QtGui import QDrag, QPainter, QPen, QBrush, QPainterPath, QColor, QFont

# --- 1. 信号通信类 ---
class NodeSignals(QObject):
    connection_created = Signal(str, int, str, int)
    connection_removed = Signal(str, int, str, int)

# --- 2. 控制点类 (用于拖动连线) ---
class ControlPoint(QGraphicsEllipseItem):
    def __init__(self, parent_edge, point_index, position):
        radius = 6
        super().__init__(-radius, -radius, 2*radius, 2*radius)
        self.parent_edge = parent_edge
        self.point_index = point_index
        self.setPos(position)
        
        self.setBrush(QBrush(QColor("#FFFFFF")))
        self.setPen(QPen(QColor(parent_edge.color), 2))
        self.setZValue(100)
        
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setVisible(False)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value
            if self.point_index == 1:
                new_pos. setY(self.parent_edge.start_port.scenePos().y())
            
            self.parent_edge.manual_offset_x = new_pos.x() - self.parent_edge.start_port.scenePos().x()
            self.parent_edge.update_path()
            return new_pos
        return super().itemChange(change, value)
    
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("#FFD700")))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor("#FFFFFF")))
        super(). hoverLeaveEvent(event)

# --- 3. 端口类 (Port) ---
class PortItem(QGraphicsItem):
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
        self. connections = []
        
        if self.port_type == 'out':
            self.line_color = self._assign_unique_color()
        else:
            self. line_color = None
        
        if self.port_type == 'in':
            self.brush = QBrush(QColor("#3CE75B"))
        else:
            self.brush = QBrush(QColor("#E74C3C"))
            
        self.setAcceptHoverEvents(True)
        self.setZValue(10)
    
    def _assign_unique_color(self):
        unique_id = id(self. parent_node) + self.index
        color_index = unique_id % len(self.COLOR_POOL)
        return self.COLOR_POOL[color_index]

    def boundingRect(self):
        return QRectF(-self.radius, -self.radius, 2*self.radius, 2*self.radius)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(QPen(Qt.white, 1))
        painter.drawEllipse(-self. radius, -self.radius, 2*self.radius, 2*self.radius)
    
    def has_connection(self):
        return len(self.connections) > 0
    
    def get_connection(self):
        return self.connections[0] if self.connections else None
    
    def get_shared_split_point(self):
        """获取该输出端口所有连线的共享分叉点X坐标"""
        if self.port_type != 'out' or not self.connections:
            return None
        
        # 检查是否有手动调整
        manual_offsets = [edge.manual_offset_x for edge in self.connections if edge.manual_offset_x is not None]
        if manual_offsets:
            return self.scenePos().x() + manual_offsets[0]
        
        # 自动计算：找到最远的目标节点
        max_distance = 0
        for edge in self.connections:
            if not edge._is_reverse_connection():
                target_x = edge.end_port.parent_node.scenePos().x()
                distance = target_x - self.scenePos().x()
                max_distance = max(max_distance, distance)
        
        # 在中点位置分叉（但至少60像素）
        if max_distance > 120:
            return self.scenePos().x() + max_distance * 0.5
        else:
            return self.scenePos().x() + 60

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
        self. setFlag(QGraphicsItem. ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self.in_ports = []
        self.out_ports = []
        self.edges = []
        
        self._create_ports()

    def _create_ports(self):
        if self.num_inputs > 0:
            port_spacing_in = self.height / (self.num_inputs + 1)
        if self.num_outputs > 0:
            port_spacing_out = self.height / (self. num_outputs + 1)
        
        for i in range(self. num_inputs):
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
        font. setBold(True)
        font. setPointSize(10)
        painter.setFont(font)
        
        title_rect = QRectF(rect.left(), rect.top(), rect.width(), 25)
        painter.drawText(title_rect, Qt.AlignCenter, self.name)
        
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)
        
        for i, port in enumerate(self.in_ports):
            port_pos = port.pos()
            text_rect = QRectF(-self.width/2 + 10, port_pos. y() - 8, 40, 16)
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

# --- 5. 连线类 (Edge) - 最终优化版 ---
class EdgeItem(QGraphicsPathItem):
    def __init__(self, start_port, end_port):
        super().__init__()
        self.start_port = start_port
        self.end_port = end_port
        self.setZValue(-1)
        
        self. color = start_port.line_color
        
        pen = QPen(QColor(self.color))
        pen.setWidth(3)
        self.setPen(pen)
        
        self. control_points = []
        self.manual_offset_x = None
        self.manual_offset_y = None
        
        start_port.connections.append(self)
        end_port.connections.append(self)
        
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        self.update_path()
        self._create_control_points()
    
    def _create_control_points(self):
        for cp in self.control_points:
            if cp.scene():
                cp.scene().removeItem(cp)
        self.control_points. clear()
        
        if not self._is_reverse_connection():
            p1 = self.start_port.scenePos()
            split_x = self.start_port.get_shared_split_point()
            
            cp1 = ControlPoint(self, 1, QPointF(split_x, p1.y()))
            self. control_points.append(cp1)
            if self.scene():
                self.scene().addItem(cp1)
    
    def _is_reverse_connection(self):
        p1 = self.start_port.scenePos()
        p2 = self.end_port.scenePos()
        return p2. x() < p1.x()
    
    def _calculate_reverse_route(self, p1, p2):
        start_node_top = self.start_port.parent_node.scenePos(). y() - self.start_port.parent_node.height / 2
        end_node_top = self.end_port. parent_node.scenePos(). y() - self.end_port.parent_node.height / 2
        
        bypass_y = min(start_node_top, end_node_top) - 60
        if self. manual_offset_y is not None:
            bypass_y = self.manual_offset_y
        
        h_extend = 40
        
        route = [
            p1,
            QPointF(p1.x() + h_extend, p1.y()),
            QPointF(p1.x() + h_extend, bypass_y),
            QPointF(p2.x() - h_extend, bypass_y),
            QPointF(p2. x() - h_extend, p2.y()),
            p2
        ]
        return route

    def update_path(self):
        """优化的路由算法：尽量重叠，最后才分开"""
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
            # 新策略：三段式路由，尽量重叠
            # 1. 从输出端口水平到共享分叉点
            split_x = self.start_port.get_shared_split_point()
            path.lineTo(split_x, p1.y())
            
            # 2.  从共享点垂直到目标端口的Y坐标（尽量直线）
            path.lineTo(split_x, p2.y())
            
            # 3.  水平连接到目标端口
            path.lineTo(p2. x(), p2.y())
        
        self.setPath(path)
    
    def hoverEnterEvent(self, event):
        for cp in self.control_points:
            cp.setVisible(True)
        pen = self.pen()
        pen.setWidth(4)
        self.setPen(pen)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        for cp in self.control_points:
            if not cp.isSelected():
                cp.setVisible(False)
        pen = self. pen()
        pen.setWidth(3)
        self.setPen(pen)
        super(). hoverLeaveEvent(event)
    
    def remove(self):
        for cp in self.control_points:
            if cp.scene():
                cp. scene().removeItem(cp)
        self.control_points.clear()
        
        if self in self.start_port.connections:
            self.start_port. connections.remove(self)
        if self in self.end_port.connections:
            self.end_port.connections.remove(self)
        
        if self in self.start_port.parent_node.edges:
            self.start_port.parent_node.edges.remove(self)
        if self in self.end_port.parent_node.edges:
            self. end_port.parent_node. edges.remove(self)
        
        if self. scene():
            self.scene(). removeItem(self)

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
            
            mid_x = (p1.x() + p2.x()) / 2
            path.lineTo(mid_x, p1.y())
            path.lineTo(mid_x, p2.y())
            path.lineTo(p2. x(), p2.y())
            
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
        if self. temp_line:
            self. removeItem(self.temp_line)
            self.temp_line = None
        
        if self. start_port:
            print(f"⚠️  连接已取消: 未找到有效的目标端口")
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
        src_port_idx = self.start_port. index
        dst_name = end_port.parent_node.name
        dst_port_idx = end_port.index
        
        self.start_port = None
        
        direction = "反向(上方绕行)" if edge._is_reverse_connection() else "正向"
        print(f"✅ 连线建立: [{src_name}:Out{src_port_idx+1}] --> [{dst_name}:In{dst_port_idx+1}] ({direction}, 颜色: {edge.color})")
        self.signals.connection_created.emit(src_name, src_port_idx, dst_name, dst_port_idx)
    
    def remove_connection(self, input_port):
        if not input_port.has_connection():
            return
        
        edge = input_port.get_connection()
        
        src_name = edge.start_port.parent_node.name
        src_port_idx = edge.start_port. index
        dst_name = edge.end_port.parent_node.name
        dst_port_idx = edge.end_port. index
        edge_color = edge.color
        
        edge.remove()
        
        print(f"🗑️  连线已断开: [{src_name}:Out{src_port_idx+1}] -X-> [{dst_name}:In{dst_port_idx+1}] (颜色: {edge_color})")
        self.signals. connection_removed.emit(src_name, src_port_idx, dst_name, dst_port_idx)

# --- 7. 画布视图 (View) ---
class DiagramView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event. mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData(). hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        component_name = event.mimeData().text()
        position = self.mapToScene(event.position(). toPoint())
        
        port_config = {
            "数据源 A": (8, 8),
            "处理器 B": (8, 8),
            "过滤器 C": (8, 8),
            "AI模型 D": (8, 8),
            "终端显示 E": (8, 8),
        }
        
        num_in, num_out = port_config. get(component_name, (2, 2))
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
        self.setWindowTitle("PySide6 节点流编辑器 - 最小折叠路由")
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
        print(f" >> 执行业务逻辑: 数据从 {src}:Out{src_port+1} 传输到 {dst}:In{dst_port+1}...")
    
    def handle_connection_removed(self, src, src_port, dst, dst_port):
        print(f" >> 清理业务逻辑: 断开 {src}:Out{src_port+1} 到 {dst}:In{dst_port+1} 的数据流...")

# 程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())