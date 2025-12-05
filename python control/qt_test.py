import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QListWidget, QGraphicsView, QGraphicsScene, 
                               QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem,
                               QSplitter)
from PySide6.QtCore import Qt, QMimeData, QPointF, QRectF, Signal, QObject
from PySide6.QtGui import QDrag, QPainter, QPen, QBrush, QPainterPath, QColor, QFont

# --- 1. 信号通信类 ---
class NodeSignals(QObject):
    # 当连接建立时发射信号: (source_node_name, target_node_name)
    connection_created = Signal(str, str)

# --- 2. 端口类 (Port) ---
class PortItem(QGraphicsItem):
    def __init__(self, parent, port_type, radius=6):
        super().__init__(parent)
        self.parent_node = parent
        self.port_type = port_type  # 'in' 或 'out'
        self.radius = radius
        
        # 设置端口颜色和位置
        if self.port_type == 'in':
            # 输入口：红色，位于节点左侧
            self.brush = QBrush(QColor("#E74C3C"))
            self.setPos(-parent.width/2, 0) 
        else:
            # 输出口：蓝色，位于节点右侧
            self.brush = QBrush(QColor("#3498DB"))
            self.setPos(parent.width/2, 0)
            
        # 允许鼠标悬停检测
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        return QRectF(-self.radius, -self.radius, 2*self.radius, 2*self.radius)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        # 去掉边框，让颜色更纯粹
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(-self.radius, -self.radius, 2*self.radius, 2*self.radius)

# --- 3. 节点类 (Node) ---
class NodeItem(QGraphicsItem):
    def __init__(self, name, position):
        super().__init__()
        self.name = name
        self.width = 120
        self.height = 60
        self.setPos(position)
        
        # 设置节点标志：可移动、可选择
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        # 创建输入和输出端口
        self.in_port = PortItem(self, 'in')
        self.out_port = PortItem(self, 'out')
        
        # 存储连接到此节点的线（用于移动节点时更新线的位置）
        self.edges = []

    def boundingRect(self):
        return QRectF(-self.width/2, -self.height/2, self.width, self.height)

    def paint(self, painter, option, widget):
        # 绘制圆角矩形背景
        rect = self.boundingRect()
        painter.setBrush(QBrush(QColor("#2C3E50")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawRoundedRect(rect, 8, 8)
        
        # 绘制文字
        painter.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.name)

    def itemChange(self, change, value):
        # 当节点位置改变时，通知所有连接线重绘
        if change == QGraphicsItem.ItemPositionChange:
            for edge in self.edges:
                edge.update_path()
        return super().itemChange(change, value)

# --- 4. 连线类 (Edge) ---
class EdgeItem(QGraphicsPathItem):
    def __init__(self, start_port, end_port):
        super().__init__()
        self.start_port = start_port
        self.end_port = end_port
        self.setZValue(-1) # 让连线显示在节点下方
        
        # 设置连线样式
        pen = QPen(QColor("#BDC3C7"))
        pen.setWidth(3)
        self.setPen(pen)
        
        self.update_path()

    def update_path(self):
        if not self.start_port or not self.end_port:
            return

        # 获取端口在场景中的绝对坐标
        p1 = self.start_port.scenePos()
        p2 = self.end_port.scenePos()

        path = QPainterPath()
        path.moveTo(p1)
        
        # 绘制贝塞尔曲线 (Cubic Bezier)
        # 控制点决定了曲线的弯曲程度，水平拉伸
        dx = abs(p2.x() - p1.x())
        ctrl1 = QPointF(p1.x() + dx * 0.5, p1.y())
        ctrl2 = QPointF(p2.x() - dx * 0.5, p2.y())
        
        path.cubicTo(ctrl1, ctrl2, p2)
        self.setPath(path)

# --- 5. 场景类 (Scene) ---
class DiagramScene(QGraphicsScene):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.temp_line = None   # 正在拖拽中的临时虚线
        self.start_port = None  # 连线的起点端口
        
        # 设置背景色和虚拟画布大小
        self.setBackgroundBrush(QBrush(QColor("#1E1E1E")))
        self.setSceneRect(0, 0, 5000, 5000)

    def mousePressEvent(self, event):
        # 使用 items() 获取点击位置的所有对象，而不是只获取最上面的一个
        # 这解决了有时候选不中端口的问题
        items = self.items(event.scenePos())
        port = None
        for item in items:
            if isinstance(item, PortItem):
                port = item
                break

        if port:
            # 逻辑A: 点击输出口 -> 开始连线
            if port.port_type == 'out':
                self.start_port = port
                # 创建临时虚线
                self.temp_line = QGraphicsPathItem()
                pen = QPen(Qt.white)
                pen.setStyle(Qt.DashLine)
                pen.setWidth(2)
                self.temp_line.setPen(pen)
                self.addItem(self.temp_line)
                return # 吞噬事件，防止节点被拖动

            # 逻辑B: 点击输入口 -> 如果正在连线中，尝试结束
            elif port.port_type == 'in' and self.start_port:
                self.finalize_connection(port)
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.temp_line and self.start_port:
            # 更新临时虚线，跟随鼠标
            p1 = self.start_port.scenePos()
            p2 = event.scenePos()
            
            path = QPainterPath()
            path.moveTo(p1)
            path.lineTo(p2)
            self.temp_line.setPath(path)
        
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # 逻辑C: 拖拽松开判定
        # 如果正在连线，并且松开鼠标的位置是一个有效的输入口
        if self.temp_line and self.start_port:
            items = self.items(event.scenePos())
            end_port = None
            for item in items:
                if isinstance(item, PortItem):
                    end_port = item
                    break
            
            # 验证：必须是输入口，且不能连到同一个节点
            if end_port and end_port.port_type == 'in' and end_port.parent_node != self.start_port.parent_node:
                self.finalize_connection(end_port)
            else:
                # 如果松开的地方是空白处，我们保持连线状态（允许点击-点击模式），
                # 或者如果你希望松开即取消，可以在这里 removeItem(self.temp_line) 并重置
                pass 
                
        super().mouseReleaseEvent(event)

    def finalize_connection(self, end_port):
        # 1. 创建实体连线
        edge = EdgeItem(self.start_port, end_port)
        self.addItem(edge)
        
        # 2. 绑定数据结构
        self.start_port.parent_node.edges.append(edge)
        end_port.parent_node.edges.append(edge)
        
        # 3. 清理临时状态
        if self.temp_line:
            self.removeItem(self.temp_line)
        self.temp_line = None
        
        # 4. 提取信息并清理起点
        src_name = self.start_port.parent_node.name
        dst_name = end_port.parent_node.name
        self.start_port = None
        
        # 5. 发射函数信号
        print(f"【系统日志】连线建立: [{src_name}] --> [{dst_name}]")
        self.signals.connection_created.emit(src_name, dst_name)

# --- 6. 画布视图 (View) ---
class DiagramView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing) # 抗锯齿，线条更平滑
        self.setAcceptDrops(True) # 允许拖放进入

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        # 获取拖拽的数据
        component_name = event.mimeData().text()
        # 将屏幕坐标转换为场景坐标
        position = self.mapToScene(event.position().toPoint())
        
        # 在场景中创建新节点
        node = NodeItem(component_name, position)
        self.scene().addItem(node)
        
        event.acceptProposedAction()

# --- 7. 右侧组件列表 (Palette) ---
class ComponentPalette(QListWidget):
    def __init__(self):
        super().__init__()
        self.setDragEnabled(True) # 开启拖拽源功能
        self.setStyleSheet("font-size: 14px; padding: 5px;")
        
        # 添加示例组件
        items = ["数据源 A", "处理器 B", "过滤器 C", "AI模型 D", "终端显示 E"]
        for i in items:
            self.addItem(i)

    def startDrag(self, supportedActions):
        # 打包拖拽数据
        item = self.currentItem()
        mimeData = QMimeData()
        mimeData.setText(item.text())
        
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec(Qt.CopyAction)

# --- 8. 主窗口 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 节点流编辑器")
        self.resize(1200, 800)

        # 初始化信号处理器
        self.signals = NodeSignals()
        self.signals.connection_created.connect(self.run_business_logic)

        # 初始化核心组件
        self.scene = DiagramScene(self.signals)
        self.view = DiagramView(self.scene)
        self.palette = ComponentPalette()

        # 使用 Splitter 进行左右布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.view)     # 左：画布
        splitter.addWidget(self.palette)  # 右：列表
        
        # 设置初始宽度比例 (4:1)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def run_business_logic(self, src, dst):
        # === 用户要求的“发射函数”在这里实现 ===
        print(f" >> 执行业务逻辑: 数据正在从 {src} 传输到 {dst}...")
        # 这里可以添加实际的后端处理代码

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置全局样式，让界面看起来现代一点
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())