import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QPoint, QPointF, QRect, QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget

from tests.qt_test_support import ensure_app
from FPGA_Agent.main import create_window as create_integrated_window
from qt_UI1 import create_window as create_ordinary_window
from qt_module import ModuleScaler
from qt_ui_mainwindow import MainWindow


class UiFunctionalRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        settings = QSettings(f"{self.temp_dir.name}/ui.ini", QSettings.IniFormat)
        self.window = MainWindow(settings=settings)
        self.window.resize(1280, 720)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def add_scaler_pair(self):
        source_index = self.window.view._alloc_index("线性缩放器")
        target_index = self.window.view._alloc_index("线性缩放器")
        source = ModuleScaler("线性缩放器", source_index, QPointF(-220, 0))
        target = ModuleScaler("线性缩放器", target_index, QPointF(220, 0))
        self.window.scene.addItem(source)
        self.window.scene.addItem(target)
        return source, target

    def assert_path_touches_ports(self, edge):
        first = edge.path().elementAt(0)
        last = edge.path().elementAt(edge.path().elementCount() - 1)
        self.assertAlmostEqual(first.x, edge.start_port.scenePos().x(), delta=0.01)
        self.assertAlmostEqual(first.y, edge.start_port.scenePos().y(), delta=0.01)
        self.assertAlmostEqual(last.x, edge.end_port.scenePos().x(), delta=0.01)
        self.assertAlmostEqual(last.y, edge.end_port.scenePos().y(), delta=0.01)

    def test_node_create_connect_move_disconnect_and_index_reuse(self):
        source, target = self.add_scaler_pair()
        target_index = target.index
        self.assertTrue(
            self.window.scene.create_connection(
                source.out_ports[0], target.in_ports[0]
            )
        )
        edge = target.in_ports[0].get_connection()
        self.assert_path_touches_ports(edge)
        target.setPos(310, 150)
        self.app.processEvents()
        self.assert_path_touches_ports(edge)
        self.window.scene.remove_connection(target.in_ports[0])
        self.assertFalse(target.in_ports[0].has_connection())
        self.window.view.remove_node(target)
        QTest.qWait(40)
        self.assertEqual(
            self.window.view._alloc_index("线性缩放器"), target_index
        )

    def test_configuration_helpers_round_trip_direct_params_and_edges(self):
        source, target = self.add_scaler_pair()
        key = next(iter(source._params))
        source._params[key] = source._params[key] + 1
        self.assertTrue(
            self.window.scene.create_connection(
                source.out_ports[0], target.in_ports[0]
            )
        )
        expected = self.window._build_config_dict()
        self.window._clear_canvas(emit_connection_removed=False)

        node_map = {}
        loaded = []
        for node_cfg in expected["nodes"]:
            node = self.window._create_node_from_config(node_cfg)
            loaded.append((node_cfg, node))
            node_map[node.name] = node
            node_map[f"{node.component_name}@{node.index}"] = node
        for node_cfg, node in loaded:
            node._params.update(node_cfg["direct_params"])
        self.window._restore_edges(expected["edges"], node_map, batch_upload=False)

        actual = self.window._build_config_dict()
        self.assertEqual(actual["mode"], expected["mode"])
        node_key = lambda item: (item["component_name"], item["index"])
        self.assertEqual(
            sorted(actual["nodes"], key=node_key),
            sorted(expected["nodes"], key=node_key),
        )
        self.assertEqual(
            sorted(actual["edges"], key=str),
            sorted(expected["edges"], key=str),
        )

    def test_parameter_failure_rolls_back_staged_value(self):
        node, _ = self.add_scaler_pair()
        key = next(iter(node._params))
        previous = node._params[key]
        replacement = previous + 1
        node._stage_param_cache_update({key: replacement})
        with patch.object(
            self.window.port_ctrl,
            "send_param",
            side_effect=RuntimeError("offline"),
        ):
            self.window._apply_param_to_hardware(node, {key: replacement})
        self.assertEqual(node._params[key], previous)
        self.assertTrue(self.window.is_log_expanded())
        self.assertIn("offline", self.window.log_output.toPlainText())

    def test_ordinary_and_integrated_windows_construct_at_target_sizes(self):
        self.window.close()
        for width, height in ((1280, 720), (1600, 900), (1920, 1080)):
            for factory in (create_ordinary_window, create_integrated_window):
                window = factory()
                window.resize(width, height)
                window.show()
                self.app.processEvents()
                for object_name in (
                    "command_bar",
                    "canvas_frame",
                    "inspector_panel",
                    "status_bar",
                ):
                    widget = window.findChild(QWidget, object_name)
                    self.assertIsNotNone(widget)
                    top_left = widget.mapTo(window, QPoint(0, 0))
                    self.assertTrue(
                        window.rect().contains(QRect(top_left, widget.size())),
                        f"{object_name} escaped {width}x{height}",
                    )
                window.close()
                self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
