from PySide6.QtCore import Qt, QMimeData, QPointF, QRectF, Signal, QObject, QByteArray, QPoint, QTimer
from PySide6.QtGui import QDrag, QPainter, QPen, QBrush, QPainterPath, QColor, QFont, QPixmap, QImage, QCursor
from PySide6.QtWidgets import (
    QApplication,
    QListWidget,
    QListWidgetItem,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsEllipseItem,
)

from qt_module import (
    PortItem,
    NodeItem,
    ModulePID,
    ModuleAccumulator,
    ModuleConstantBool,
    ModuleBase,
    ModuleScaler,
    ModuleFIRFilter,
    ModuleIIRFilter,
    ModuleSCLOFSM,
    ModulePDHFSM,
    ModuleLinerTransformer,
    SINGenerator,
    DigitalControlledOscillator,
    module_maxm,
)


class NodeSignals(QObject):
    connection_created = Signal(str, int, str, int)
    connection_removed = Signal(str, int, str, int)


class BorderPort(PortItem):
    def __init__(self, port_type, index, position, signals=None, display_text=None, name=None):
        if signals is None:
            signals = ["bool", "level", "phase", "differential"]
        super().__init__(None, port_type, index, signals)
        self.name = name if name is not None else f"Border_{port_type}_{index}"
        self.port_type = port_type
        self.index = index
        self.radius = 6
        self.width = 20
        self.height = 20
        self.connections = []

        self.channel_name = chr(65 + index)
        if display_text is not None:
            self.display_text = display_text
        elif self.port_type == "out":
            self.display_text = f"输入通道{self.channel_name}"
        else:
            self.display_text = f"输出通道{self.channel_name}"

        self.setPos(position)
        self.setAcceptHoverEvents(True)
        self.setZValue(10)

    def boundingRect(self):
        if self.port_type == "out":
            return QRectF(-self.radius, -15, 2 * self.radius + 100, 30)
        return QRectF(-self.radius - 100, -15, 2 * self.radius + 100, 30)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(QPen(Qt.white, 1))
        painter.drawEllipse(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

        painter.setPen(Qt.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)

        if self.port_type == "out":
            text_rect = QRectF(15, -10, 80, 20)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.display_text)
        else:
            text_rect = QRectF(-95, -10, 80, 20)
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, self.display_text)

    def has_connection(self):
        return len(self.connections) > 0

    def get_connection(self):
        return self.connections[0] if self.connections else None

    def get_turn_distance(self):
        return 30 + (self.index * 7)

    def get_bypass_offset(self):
        return 30 + (self.index * 7)

    def get_reverse_h_extend(self):
        return 30 + (self.index * 7)


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
        self.horizontal_offset = 0
        self.reverse_horizontal_offset = 0

        start_port.connections.append(self)
        end_port.connections.append(self)

        self.setFlag(QGraphicsItem.ItemIsSelectable)
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

    def _lane_offset(self):
        """Spread sibling edges from the same output port into parallel lanes."""
        if not self.start_port:
            return 0.0
        siblings = self.start_port.connections
        if not siblings:
            return 0.0
        try:
            idx = siblings.index(self)
        except ValueError:
            return 0.0
        center = (len(siblings) - 1) / 2.0
        return (idx - center) * 10.0

    def _is_reverse_connection(self):
        p1 = self.start_port.scenePos()
        p2 = self.end_port.scenePos()
        return p2.x() < p1.x()

    def _compute_node_extents(self):
        s_node = self.start_port.parent_node if hasattr(self.start_port, "parent_node") and self.start_port.parent_node else self.start_port
        e_node = self.end_port.parent_node if hasattr(self.end_port, "parent_node") and self.end_port.parent_node else self.end_port
        s_top = s_node.scenePos().y() - s_node.height / 2
        s_bottom = s_node.scenePos().y() + s_node.height / 2
        e_top = e_node.scenePos().y() - e_node.height / 2
        e_bottom = e_node.scenePos().y() + e_node.height / 2
        return (s_top, s_bottom, e_top, e_bottom)

    def _calculate_bypass_y(self, bypass_offset, lane_offset=0.0):
        p1_node = self.start_port.parent_node if hasattr(self.start_port, "parent_node") and self.start_port.parent_node else self.start_port
        p2_node = self.end_port.parent_node if hasattr(self.end_port, "parent_node") and self.end_port.parent_node else self.end_port
        s_pos = p1_node.scenePos()
        e_pos = p2_node.scenePos()

        dx = abs(e_pos.x() - s_pos.x())
        dy = abs(e_pos.y() - s_pos.y())
        node_w = max(p1_node.width, p2_node.width)
        node_h = max(p1_node.height, p2_node.height)

        s_top, s_bottom, e_top, e_bottom = self._compute_node_extents()

        if dy > node_h:
            base_clearance = 15
            port_offset = self.start_port.index * 10
            if e_pos.y() > s_pos.y():
                return e_top - base_clearance - port_offset + lane_offset
            return e_bottom + base_clearance + port_offset + lane_offset

        if dx <= node_w:
            if self.start_port.pos().y() > 0 and self.end_port.pos().y() < 0:
                return ((s_top - bypass_offset) + (e_bottom + bypass_offset)) / 2.0 + lane_offset
            if self.start_port.pos().y() < 0 and self.end_port.pos().y() > 0:
                return ((s_bottom + bypass_offset) + (e_top - bypass_offset)) / 2.0 + lane_offset
            if self.end_port.pos().y() > 0:
                return max(s_bottom, e_bottom) + bypass_offset + lane_offset
            return min(s_top, e_top) - bypass_offset + lane_offset

        if self.end_port.pos().y() > 0:
            return max(s_bottom, e_bottom) + bypass_offset + lane_offset
        return min(s_top, e_top) - bypass_offset + lane_offset

    def _calculate_route_using_bypass(self, p1, p2, bypass_y, h_extend, lane_offset=0.0):
        lane_x = lane_offset * 0.6
        return [
            p1,
            QPointF(p1.x() + h_extend + lane_x, p1.y()),
            QPointF(p1.x() + h_extend + lane_x, bypass_y),
            QPointF(p2.x() - h_extend + self.reverse_horizontal_offset - lane_x, bypass_y),
            QPointF(p2.x() - h_extend, p2.y()),
            p2,
        ]

    def _calculate_reverse_route(self, p1, p2, lane_offset=0.0):
        h_extend = self.start_port.get_reverse_h_extend()
        bypass_offset = self.start_port.get_bypass_offset()
        bypass_y = self._calculate_bypass_y(bypass_offset, lane_offset=lane_offset)
        return self._calculate_route_using_bypass(p1, p2, bypass_y, h_extend, lane_offset=lane_offset)

    def _calculate_simple_z_route(self, p1, p2, lane_offset=0.0):
        vertical_x = p1.x() + 30 + (self.start_port.index * 7) + lane_offset
        return [p1, QPointF(vertical_x, p1.y()), QPointF(vertical_x, p2.y()), p2]

    def update_path(self):
        if not self.start_port or not self.end_port:
            return

        p1 = self.start_port.scenePos()
        p2 = self.end_port.scenePos()
        path = QPainterPath()
        path.moveTo(p1)

        s_node = self.start_port.parent_node if hasattr(self.start_port, "parent_node") and self.start_port.parent_node else self.start_port
        e_node = self.end_port.parent_node if hasattr(self.end_port, "parent_node") and self.end_port.parent_node else self.end_port
        dx = abs(e_node.scenePos().x() - s_node.scenePos().x())
        dy = abs(e_node.scenePos().y() - s_node.scenePos().y())
        node_w = max(s_node.width, e_node.width)
        node_h = max(s_node.height, e_node.height)
        is_reverse = self._is_reverse_connection()
        lane_offset = self._lane_offset()

        if not is_reverse and dx > node_w * 1.5 and dy > node_h:
            route = self._calculate_simple_z_route(p1, p2, lane_offset=lane_offset)
            for point in route[1:]:
                path.lineTo(point)
        elif dy > node_h:
            h_extend = self.start_port.get_reverse_h_extend()
            bypass_y = self._calculate_bypass_y(self.start_port.get_bypass_offset(), lane_offset=lane_offset)
            route = self._calculate_route_using_bypass(p1, p2, bypass_y, h_extend, lane_offset=lane_offset)
            for point in route[1:]:
                path.lineTo(point)
        else:
            if is_reverse:
                route = self._calculate_reverse_route(p1, p2, lane_offset=lane_offset)
                for point in route[1:]:
                    path.lineTo(point)
            else:
                turn_x = p1.x() + self.start_port.get_turn_distance() + lane_offset
                y1_with_offset = p1.y() + self.horizontal_offset + lane_offset
                y2_with_offset = p2.y() + self.horizontal_offset + lane_offset
                path.lineTo(turn_x, p1.y())
                path.lineTo(turn_x, y1_with_offset)
                path.lineTo(turn_x, y2_with_offset)
                path.lineTo(turn_x, p2.y())
                path.lineTo(p2.x(), p2.y())

        self.setPath(path)

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
        was_first = self.start_port.connections.index(self) == 0 if self in self.start_port.connections else False

        for cp in self.control_points:
            if cp.scene():
                cp.scene().removeItem(cp)
        self.control_points.clear()

        if self in self.start_port.connections:
            self.start_port.connections.remove(self)
        if self in self.end_port.connections:
            self.end_port.connections.remove(self)

        start_node = self.start_port.parent_node if hasattr(self.start_port, "parent_node") and self.start_port.parent_node else None
        end_node = self.end_port.parent_node if hasattr(self.end_port, "parent_node") and self.end_port.parent_node else None

        if start_node and self in start_node.edges:
            start_node.edges.remove(self)
        if end_node and self in end_node.edges:
            end_node.edges.remove(self)

        if was_first and self.start_port.connections:
            for edge in self.start_port.connections:
                edge._create_control_points()
                break

        # Re-route siblings after removal to keep lane offsets balanced.
        for edge in list(self.start_port.connections):
            edge.update_path()

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
        self.setSceneRect(-2400, -1350, 4800, 2700)

        self.left_ports = []
        self.right_ports = []
        self.constant_out_ports = []
        for i in range(8):
            left_port = BorderPort("out", i, QPointF(0, 0))
            self.addItem(left_port)
            self.left_ports.append(left_port)
            right_port = BorderPort("in", i, QPointF(0, 0))
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
            if not matched and self.developer_mode and (start_set & physical) and (end_set & physical):
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
            if not matched and self.developer_mode and (start_set & physical) and (end_set & physical):
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
            if port.port_type == "out":
                self.start_port = port
                self.temp_line = QGraphicsPathItem()
                pen = QPen(QColor(port.line_color))
                self._apply_preview_style(pen, port)
                pen.setWidth(self._preview_width(port))
                self.temp_line.setPen(pen)
                self.addItem(self.temp_line)
                return

            if port.port_type == "in":
                if port.has_connection():
                    self.remove_connection(port)
                    return
                if self.start_port:
                    self.finalize_connection(port)
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.temp_line and self.start_port:
            p1 = self.start_port.scenePos()
            p2 = event.scenePos()

            path = QPainterPath()
            path.moveTo(p1)

            s_node = self.start_port.parent_node if hasattr(self.start_port, "parent_node") and self.start_port.parent_node else self.start_port
            hovered_items = self.items(event.scenePos())
            hovered_port = None
            for it in hovered_items:
                if isinstance(it, (PortItem, BorderPort)) and it is not self.start_port:
                    hovered_port = it
                    break

            if hovered_port:
                p2_ref = hovered_port.scenePos()
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

            dx = abs(p2_ref.x() - s_node.scenePos().x())
            dy = abs(p2_ref.y() - s_node.scenePos().y())
            node_w = s_node.width
            node_h = s_node.height

            if dx <= node_w and dy > node_h:
                h_extend = self.start_port.get_reverse_h_extend()
                bypass_offset = self.start_port.get_bypass_offset()
                if hovered_port:
                    tmp_edge = EdgeItem(self.start_port, hovered_port)
                    bypass_y = tmp_edge._calculate_bypass_y(bypass_offset)
                    tmp_edge.remove()
                else:
                    if p2.y() > p1.y():
                        bypass_y = max(s_node.scenePos().y() + node_h / 2, p2.y()) + bypass_offset
                    else:
                        bypass_y = min(s_node.scenePos().y() - node_h / 2, p2.y()) - bypass_offset

                route = [
                    p1,
                    QPointF(p1.x() + h_extend, p1.y()),
                    QPointF(p1.x() + h_extend, bypass_y),
                    QPointF(p2_ref.x() - h_extend, bypass_y),
                    QPointF(p2_ref.x() - h_extend, p2_ref.y()),
                    p2_ref,
                ]
                for pt in route[1:]:
                    path.lineTo(pt)
            else:
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
                    turn_x = p1.x() + self.start_port.get_turn_distance()
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
        if end_port.port_type != "in":
            print("❌ 连接失败: 只能连接到输入端口")
            return False

        start_node = start_port.parent_node if hasattr(start_port, "parent_node") and start_port.parent_node else None
        end_node = end_port.parent_node if hasattr(end_port, "parent_node") and end_port.parent_node else None

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
            print("⚠️ 连接已取消: 未找到有效的目标端口")
            self.start_port = None

    def _runtime_node_label(self, port):
        node = port.parent_node if hasattr(port, "parent_node") and port.parent_node else None
        if node is None:
            return getattr(port, "name", "Unknown")

        base_name = getattr(node, "name", "Unknown")
        if base_name in ("HIGH", "LOW"):
            return f"{base_name}[{int(getattr(node, 'index', 0))}]"
        return base_name

    def create_connection(self, start_port, end_port):
        if not self._is_valid_connection(start_port, end_port):
            return False

        edge = EdgeItem(start_port, end_port)
        self.addItem(edge)
        edge.refresh_style()

        start_node = start_port.parent_node if hasattr(start_port, "parent_node") and start_port.parent_node else None
        end_node = end_port.parent_node if hasattr(end_port, "parent_node") and end_port.parent_node else None

        if start_node:
            start_node.edges.append(edge)
        if end_node:
            end_node.edges.append(edge)

        src_name = start_port.parent_node.name if hasattr(start_port, "parent_node") and start_port.parent_node else start_port.name
        src_log_name = self._runtime_node_label(start_port)
        src_port_idx = start_port.index
        dst_name = end_port.parent_node.name if hasattr(end_port, "parent_node") and end_port.parent_node else end_port.name
        dst_log_name = self._runtime_node_label(end_port)
        dst_port_idx = end_port.index

        direction = "反向(绕行)" if edge._is_reverse_connection() else "正向"
        print(f"✅ 连线建立: [{src_log_name}:Out{src_port_idx+1}] --> [{dst_log_name}:In{dst_port_idx+1}] ({direction}, 颜色: {edge.color})")
        self.signals.connection_created.emit(src_name, src_port_idx, dst_name, dst_port_idx)
        return True

    def finalize_connection(self, end_port):
        start_port = self.start_port
        if start_port is None:
            return

        self.create_connection(start_port, end_port)

        if self.temp_line:
            self.removeItem(self.temp_line)
        self.temp_line = None
        self.start_port = None

    def remove_connection(self, input_port):
        if not input_port.has_connection():
            return

        edge = input_port.get_connection()
        src_name = edge.start_port.parent_node.name if hasattr(edge.start_port, "parent_node") and edge.start_port.parent_node else edge.start_port.name
        src_log_name = self._runtime_node_label(edge.start_port)
        src_port_idx = edge.start_port.index
        dst_name = edge.end_port.parent_node.name if hasattr(edge.end_port, "parent_node") and edge.end_port.parent_node else edge.end_port.name
        dst_log_name = self._runtime_node_label(edge.end_port)
        dst_port_idx = edge.end_port.index
        edge_color = edge.color

        edge.remove()
        print(f"🗑️ 连线已断开: [{src_log_name}:Out{src_port_idx+1}] -X-> [{dst_log_name}:In{dst_port_idx+1}] (颜色: {edge_color})")
        self.signals.connection_removed.emit(src_name, src_port_idx, dst_name, dst_port_idx)


class DiagramView(QGraphicsView):
    module_factory = {
        "PID控制器": ModulePID,
        "累加器": ModuleAccumulator,
        "布尔值：是": ModuleConstantBool,
        "布尔值：否": ModuleConstantBool,
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

    composite_modules = {
        "正弦波发生器": SINGenerator,
        "数字控制振荡器": DigitalControlledOscillator,
    }

    def __init__(self, scene):
        super().__init__(scene)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)

        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, False)

        self._used_indices = {k: set() for k in self.module_factory}
        self._maxnum = {k: module_maxm.get(k, 1) for k in self.module_factory}
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

        if hasattr(scene, "constant_out_ports") and len(scene.constant_out_ports) >= 2:
            high_pos = self.mapToScene(QPoint(5 * self.scale_factor, int(spacing * 0.35)))
            low_pos = self.mapToScene(QPoint(5 * self.scale_factor, int(spacing * 0.75)))
            scene.constant_out_ports[0].setPos(high_pos)
            scene.constant_out_ports[1].setPos(low_pos)

        for item in scene.items():
            if isinstance(item, EdgeItem):
                item.update_path()

    def _alloc_index(self, component_name: str):
        used = self._used_indices[component_name]
        max_count = self._maxnum[component_name]

        if max_count is None or max_count <= 0:
            i = 0
            while i in used:
                i += 1
            used.add(i)
            return i

        for i in range(max_count):
            if i not in used:
                used.add(i)
                return i
        return None

    def _free_index(self, component_name: str, idx: int):
        self._used_indices.get(component_name, set()).discard(idx)

    def _apply_mode_to_node(self, node):
        scene = self.scene()
        if not scene or not node:
            return
        developer_mode = getattr(scene, "developer_mode", False)
        if hasattr(node, "free_mode"):
            node.free_mode = not developer_mode

    def _is_near_node(self, scene_pos, margin=10):
        for item in self.scene().items():
            if isinstance(item, NodeItem):
                node_scene_rect = item.mapRectToScene(item.boundingRect())
                if node_scene_rect.adjusted(-margin, -margin, margin, margin).contains(scene_pos):
                    return True
        return False

    def _is_near_port(self, scene_pos, margin=10):
        for item in self.scene().items():
            if isinstance(item, PortItem):
                port_scene_rect = item.mapRectToScene(item.boundingRect())
                if port_scene_rect.adjusted(-margin, -margin, margin, margin).contains(scene_pos):
                    return True
        return False

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        component_name = event.mimeData().text()
        position = self.mapToScene(event.position().toPoint())

        if component_name in self.composite_modules:
            composite_cls = self.composite_modules[component_name]
            composite_cls.create_sub_modules(
                self.scene(),
                position,
                self._alloc_index,
                connect_func=self.scene().create_connection,
            )
            event.acceptProposedAction()
            return

        module_cls = self.module_factory.get(component_name)
        if module_cls:
            idx = self._alloc_index(component_name)
            if idx is None:
                print(f"❌ 超出 {component_name} 模块数量上限")
                return
            if component_name == "解卷绕机":
                node = module_cls(component_name, idx, position, 1, 1)
            else:
                node = module_cls(component_name, idx, position)
            self._apply_mode_to_node(node)
            self.scene().addItem(node)
            event.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            items = self.scene().items(scene_pos)

            self._drag_candidate_node = None
            self._drag_start_pos = None
            self._is_dragging_view = False
            self._view_drag_start_pos = None

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
        if (event.buttons() & Qt.LeftButton) and self._is_dragging_view and self._view_drag_start_pos:
            delta = event.position().toPoint() - self._view_drag_start_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.update_border_ports()
            self._view_drag_start_pos = event.position().toPoint()
            event.accept()
            return

        if (event.buttons() & Qt.LeftButton) and self._drag_candidate_node and self._drag_start_pos:
            dist = (event.position().toPoint() - self._drag_start_pos).manhattanLength()
            if dist >= QApplication.startDragDistance():
                gp = event.globalPosition().toPoint()
                top_left = self.viewport().mapToGlobal(self.viewport().rect().topLeft())
                bottom_right = self.viewport().mapToGlobal(self.viewport().rect().bottomRight())

                outside_view = gp.x() > bottom_right.x() and top_left.y() <= gp.y() <= bottom_right.y()
                node = self._drag_candidate_node

                if not outside_view:
                    node.setPos(self.mapToScene(event.position().toPoint()))
                    event.accept()
                    return

                orig_visible = node.isVisible()
                node.setVisible(False)
                for edge in node.edges:
                    edge.setVisible(False)
                self.scene().clearSelection()

                mime = QMimeData()
                mime.setData("application/x-node-instance", QByteArray(str(id(node)).encode("utf-8")))
                mime.setText(getattr(node, "name", ""))

                drag = QDrag(self)
                drag.setMimeData(mime)
                try:
                    pix = self._node_pixmap(node)
                    drag.setPixmap(pix)
                    drag.setHotSpot(pix.rect().center())
                except Exception:
                    pass

                result = drag.exec(Qt.MoveAction)
                if result == Qt.MoveAction:
                    self.remove_node(node)
                else:
                    global_pos = QCursor.pos()
                    scene_pos = self.mapToScene(self.viewport().mapFromGlobal(global_pos))
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
        if event.modifiers() & Qt.ControlModifier:
            delta_scale_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.scale_factor *= delta_scale_factor
            self.scale(delta_scale_factor, delta_scale_factor)
            event.accept()
            self.sync_scene_to_viewport()
            self.update_border_ports()
            return

        super().wheelEvent(event)
        self.sync_scene_to_viewport()
        self.update_border_ports()

    def _node_pixmap(self, node, thumbnail_size=(100, 100)):
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
        p.drawText(title_rect, Qt.AlignCenter, getattr(node, "name", "Node"))

        font.setBold(False)
        font.setPointSize(8)
        p.setFont(font)
        type_rect = QRectF(rect.left(), rect.top() + 25, rect.width(), 20)
        p.drawText(type_rect, Qt.AlignCenter, getattr(node, "component_name", "Unknown"))

        p.end()
        return QPixmap.fromImage(img)

    def remove_node(self, node: NodeItem):
        delay_ms = 200
        edges = list(node.edges)

        def remove_next_edge(i=0):
            if i >= len(edges):
                if node.scene():
                    self._free_index(node.component_name, int(node.index))
                    node.scene().removeItem(node)
                node.edges.clear()
                self.scene().update()
                self.viewport().update()
                print(f"🗑️ 已移除组件: {node.name}")
                return

            edge = edges[i]
            if edge and edge.start_port and edge.end_port:
                src_name = edge.start_port.parent_node.name if getattr(edge.start_port, "parent_node", None) else edge.start_port.name
                dst_name = edge.end_port.parent_node.name if getattr(edge.end_port, "parent_node", None) else edge.end_port.name
                self.scene().signals.connection_removed.emit(src_name, edge.start_port.index, dst_name, edge.end_port.index)
                edge.remove()

            QTimer.singleShot(delay_ms, lambda: remove_next_edge(i + 1))

        remove_next_edge(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_scene_to_viewport()
        self.update_border_ports()

    def auto_fit_nodes(self, padding_ratio=0.12, min_padding=70.0, max_padding=180.0, max_scale=1.15):
        scene = self.scene()
        if not scene:
            return

        node_rects = [item.sceneBoundingRect() for item in scene.items() if isinstance(item, NodeItem)]
        if not node_rects:
            self.resetTransform()
            self.scale_factor = 1.0
            self.sync_scene_to_viewport()
            self.update_border_ports()
            return

        bounds = QRectF(node_rects[0])
        for rect in node_rects[1:]:
            bounds = bounds.united(rect)

        content_size = max(bounds.width(), bounds.height(), 1.0)
        padding = max(min_padding, min(max_padding, content_size * padding_ratio))
        fit_rect = bounds.adjusted(-padding, -padding, padding, padding)
        if fit_rect.isEmpty():
            return

        viewport_rect = self.viewport().rect()
        view_margin_x = max(240.0, viewport_rect.width() * 0.75)
        view_margin_y = max(180.0, viewport_rect.height() * 0.75)
        scene.setSceneRect(fit_rect.adjusted(-view_margin_x, -view_margin_y, view_margin_x, view_margin_y))

        self.resetTransform()
        self.fitInView(fit_rect, Qt.KeepAspectRatio)
        scale = self.transform().m11() if self.transform().m11() > 0 else 1.0
        if scale > max_scale:
            self.resetTransform()
            self.scale(max_scale, max_scale)
            scale = max_scale

        self.centerOn(bounds.center())
        self.scale_factor = scale
        self.sync_scene_to_viewport()
        self.update_border_ports()

    def center_on_nodes(self, margin_ratio=0.5, min_margin=180.0):
        scene = self.scene()
        if not scene:
            return

        node_rects = [item.sceneBoundingRect() for item in scene.items() if isinstance(item, NodeItem)]
        if not node_rects:
            return

        bounds = QRectF(node_rects[0])
        for rect in node_rects[1:]:
            bounds = bounds.united(rect)

        viewport_rect = self.viewport().rect()
        margin_x = max(min_margin, viewport_rect.width() * margin_ratio)
        margin_y = max(min_margin, viewport_rect.height() * margin_ratio)
        scene.setSceneRect(bounds.adjusted(-margin_x, -margin_y, margin_x, margin_y))
        self.centerOn(bounds.center())
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
            "布尔值：是",
            "布尔值：否",
            "三角函数运算器",
            "反三角函数运算器",
            "线性缩放器",
            "FIR滤波器",
            "IIR滤波器",
            "线性变换器",
            "混频器",
            "解卷绕器",
            "PDH状态机",
            "LO自动校准状态机",
        ]
        composite_items = ["正弦波发生器", "数字控制振荡器"]
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

        mime_data = QMimeData()
        mime_data.setText(item.text())

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        pixmap = self._create_component_thumbnail(item.text())
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

    def dragMoveEvent(self, event):
        md = event.mimeData()
        if md.hasFormat("application/x-node-instance"):
            event.setDropAction(Qt.MoveAction)
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        md = event.mimeData()
        if md.hasFormat("application/x-node-instance"):
            event.setDropAction(Qt.MoveAction)
            event.acceptProposedAction()
            return
        super().dropEvent(event)
