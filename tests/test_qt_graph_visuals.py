import unittest

from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage, QPainter

from tests.qt_test_support import ensure_app
from qt_module import ModuleScaler
from qt_ui_graph import ComponentPalette, DiagramScene, EdgeItem, NodeSignals
from qt_ui_theme import UiColors


class GraphVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def assert_path_touches_ports(self, edge):
        path = edge.path()
        first = path.elementAt(0)
        last = path.elementAt(path.elementCount() - 1)
        start = edge.start_port.scenePos()
        end = edge.end_port.scenePos()
        self.assertAlmostEqual(first.x, start.x(), delta=0.01)
        self.assertAlmostEqual(first.y, start.y(), delta=0.01)
        self.assertAlmostEqual(last.x, end.x(), delta=0.01)
        self.assertAlmostEqual(last.y, end.y(), delta=0.01)

    def _edge(self, source_pos, target_pos):
        scene = DiagramScene(NodeSignals())
        source = ModuleScaler("线性缩放器", 0, source_pos)
        target = ModuleScaler("线性缩放器", 1, target_pos)
        scene.addItem(source)
        scene.addItem(target)
        edge = EdgeItem(source.out_ports[0], target.in_ports[0])
        scene.addItem(edge)
        return scene, source, target, edge

    def test_forward_reverse_bypass_and_fanout_edges_touch_port_centers(self):
        layouts = (
            (QPointF(0, 0), QPointF(420, 0)),
            (QPointF(0, 0), QPointF(420, 280)),
            (QPointF(420, 0), QPointF(0, 0)),
        )
        for source_pos, target_pos in layouts:
            scene, source, target, edge = self._edge(source_pos, target_pos)
            self.assert_path_touches_ports(edge)

        scene = DiagramScene(NodeSignals())
        source = ModuleScaler("线性缩放器", 0, QPointF(0, 0))
        scene.addItem(source)
        edges = []
        for index, y in ((1, -140), (2, 140)):
            target = ModuleScaler("线性缩放器", index, QPointF(420, y))
            scene.addItem(target)
            edge = EdgeItem(source.out_ports[0], target.in_ports[0])
            scene.addItem(edge)
            edges.append(edge)
        for edge in edges:
            edge.update_path()
            self.assert_path_touches_ports(edge)

    def test_edge_updates_to_new_port_center_after_node_move(self):
        scene, source, target, edge = self._edge(QPointF(0, 0), QPointF(420, 0))
        target.setPos(520, 180)
        self.app.processEvents()
        edge.update_path()
        self.assert_path_touches_ports(edge)

    def test_temporary_edge_snaps_to_hovered_port_center(self):
        scene = DiagramScene(NodeSignals())
        source = ModuleScaler("线性缩放器", 0, QPointF(0, 0))
        target = ModuleScaler("线性缩放器", 1, QPointF(420, 0))
        scene.addItem(source)
        scene.addItem(target)
        scene.start_port = source.out_ports[0]
        cursor = target.in_ports[0].scenePos() + QPointF(2, 1)
        path = scene._preview_connection_path(cursor, target.in_ports[0])
        last = path.elementAt(path.elementCount() - 1)
        center = target.in_ports[0].scenePos()
        self.assertAlmostEqual(last.x, center.x(), delta=0.01)
        self.assertAlmostEqual(last.y, center.y(), delta=0.01)

    def test_palette_filter_hides_nonmatching_modules_and_keeps_section_headers(self):
        palette = ComponentPalette()
        palette.filter_items("PID")
        visible = [
            palette.item(i).text()
            for i in range(palette.count())
            if not palette.item(i).isHidden()
        ]
        self.assertIn("PID控制器", visible)
        self.assertNotIn("累加器", visible)
        self.assertIn("非组合模块", visible)
        self.assertNotIn("组合模块", visible)

    def test_selected_node_renders_wine_accent_strip(self):
        node = ModuleScaler("线性缩放器", 0, QPointF())
        node.setSelected(True)
        image = QImage(220, 180, QImage.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        painter.translate(110, 90)
        node.paint(painter, None, None)
        painter.end()
        accent_x = int(110 + node.boundingRect().left() + 10)
        accent_y = int(90 + node.boundingRect().top() + 12)
        self.assertEqual(
            image.pixelColor(accent_x, accent_y).name().upper(),
            UiColors.PKU_WINE,
        )


if __name__ == "__main__":
    unittest.main()
