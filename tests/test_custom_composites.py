import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QPointF, QSettings, Qt
from PySide6.QtWidgets import QApplication, QTreeWidget

from tests.qt_test_support import ensure_app
from qt_custom_composite import (
    CustomCompositeDetailsWidget,
    CustomCompositeLibrary,
    CustomCompositeNode,
    CustomCompositeWorkbench,
)
from qt_module import ModuleScaler, NodeItem
from qt_ui_graph import ComponentPalette, DiagramScene, DiagramView, EdgeItem, NodeSignals
from qt_ui_mainwindow import MainWindow
from canvas_bridge import CanvasBridge
from tool_executor import ToolExecutor


class CustomCompositeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.library_path = Path(self.temp_dir.name) / "custom_composites.json"

    def tearDown(self):
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() == "custom_composite_workbench":
                widget.close()
        self.app.processEvents()
        self.temp_dir.cleanup()

    @staticmethod
    def _definition(name="双缩放链路"):
        return {
            "name": name,
            "description": "两级缩放器测试组合",
            "nodes": [
                {
                    "local_id": "n1",
                    "component_name": "线性缩放器",
                    "pos": {"x": 0.0, "y": 0.0},
                    "direct_params": {"scale": 2},
                    "special_methods": {},
                },
                {
                    "local_id": "n2",
                    "component_name": "线性缩放器",
                    "pos": {"x": 240.0, "y": 0.0},
                    "direct_params": {"scale": 3},
                    "special_methods": {},
                },
            ],
            "edges": [
                {
                    "src": {"node_id": "n1", "port_index": 0},
                    "dst": {"node_id": "n2", "port_index": 0},
                }
            ],
            "inputs": [
                {
                    "key": "signal_in",
                    "label": "信号输入",
                    "node_id": "n1",
                    "port_index": 0,
                    "signals": ["level"],
                }
            ],
            "outputs": [
                {
                    "key": "signal_out",
                    "label": "信号输出",
                    "node_id": "n2",
                    "port_index": 0,
                    "signals": ["level"],
                }
            ],
            "parameters": [
                {
                    "key": "first_stage_scale",
                    "label": "一级缩放系数",
                    "type": "int",
                    "default": 2,
                    "min": -32768,
                    "max": 32767,
                    "mapping": {
                        "node_id": "n1",
                        "kind": "direct",
                        "target_key": "scale",
                    },
                }
            ],
        }

    def test_library_round_trip_update_and_delete(self):
        library = CustomCompositeLibrary(self.library_path)
        saved = library.save_definition(self._definition())

        reloaded = CustomCompositeLibrary(self.library_path)
        self.assertEqual(len(reloaded.definitions()), 1)
        self.assertEqual(reloaded.get(saved["id"])["name"], "双缩放链路")

        updated = self._definition("双缩放链路 v2")
        updated["description"] = "更新后的描述"
        reloaded.save_definition(updated, definition_id=saved["id"])
        self.assertEqual(reloaded.get(saved["id"])["description"], "更新后的描述")

        self.assertTrue(reloaded.delete(saved["id"] ))
        self.assertEqual(reloaded.definitions(), [])

    def test_library_rejects_empty_and_duplicate_names(self):
        library = CustomCompositeLibrary(self.library_path)
        library.save_definition(self._definition())

        with self.assertRaisesRegex(ValueError, "名称"):
            library.save_definition(self._definition("  "))
        with self.assertRaisesRegex(ValueError, "已存在"):
            library.save_definition(self._definition("双缩放链路"))

    def test_palette_exposes_custom_section_and_searchable_drag_item(self):
        library = CustomCompositeLibrary(self.library_path)
        saved = library.save_definition(self._definition())
        palette = ComponentPalette()
        palette.set_custom_composites(library.definitions())

        matches = palette.findItems("双缩放链路", Qt.MatchExactly)
        self.assertEqual(len(matches), 1)
        self.assertTrue(matches[0].flags() & Qt.ItemIsDragEnabled)
        self.assertEqual(matches[0].data(Qt.UserRole)["id"], saved["id"])

        palette.filter_items("双缩放")
        self.assertFalse(matches[0].isHidden())
        palette.filter_items("不存在")
        self.assertTrue(matches[0].isHidden())

    def test_definition_instantiates_named_black_box_backed_by_runtime_graph(self):
        signals = NodeSignals()
        routed = []
        signals.connection_created.connect(lambda *args: routed.append(args))
        scene = DiagramScene(signals)
        view = DiagramView(scene)
        created = view.instantiate_custom_composite(
            self._definition(), QPointF(100.0, 80.0)
        )

        self.assertIsInstance(created, CustomCompositeNode)
        self.assertEqual(created.display_name, "双缩放链路")
        self.assertEqual(created.pos(), QPointF(100.0, 80.0))
        self.assertEqual(len(created.runtime_nodes), 2)
        self.assertEqual(len(created.in_ports), 1)
        self.assertEqual(len(created.out_ports), 1)
        self.assertEqual(created.inputs_display_name, ["信号输入"])
        self.assertEqual(created.outputs_display_name, ["信号输出"])
        self.assertEqual(created.get_params(), {"first_stage_scale": 2})
        self.assertEqual(created.param_schema()[0]["label"], "一级缩放系数")
        self.assertEqual(
            created.runtime_port_reference("in", 0),
            (created.runtime_nodes["n1"].name, 0),
        )
        self.assertEqual(
            created.runtime_port_reference("out", 0),
            (created.runtime_nodes["n2"].name, 0),
        )
        self.assertEqual(len(routed), 1)
        self.assertEqual(routed[0][0], created.runtime_nodes["n1"].name)
        self.assertEqual(routed[0][2], created.runtime_nodes["n2"].name)
        self.assertEqual(
            len([item for item in scene.items() if isinstance(item, NodeItem)]), 1
        )
        self.assertEqual(
            len([item for item in scene.items() if isinstance(item, EdgeItem)]), 0
        )

        details = CustomCompositeDetailsWidget(created)
        tree = details.findChild(QTreeWidget, "custom_composite_details_tree")
        self.assertIsNotNone(tree)
        self.assertEqual(tree.topLevelItemCount(), 3)
        details.deleteLater()

    def test_repeated_black_box_names_receive_definition_scoped_ordinals(self):
        scene = DiagramScene(NodeSignals())
        view = DiagramView(scene)
        definition = self._definition("双级反馈控制器")

        first = view.instantiate_custom_composite(definition, QPointF(100, 80))
        second = view.instantiate_custom_composite(definition, QPointF(420, 80))

        self.assertEqual(first.display_name, "双级反馈控制器")
        self.assertEqual(first.display_ordinal, 1)
        self.assertEqual(second.display_name, "双级反馈控制器2")
        self.assertEqual(second.display_ordinal, 2)

        second.release_runtime(view, scene)
        scene.removeItem(second)
        replacement = view.instantiate_custom_composite(
            definition, QPointF(420, 240)
        )
        self.assertEqual(replacement.display_name, "双级反馈控制器2")
        self.assertEqual(replacement.display_ordinal, 2)

    def test_workbench_serializes_and_saves_user_graph(self):
        library = CustomCompositeLibrary(self.library_path)
        workbench = CustomCompositeWorkbench(library)
        first = ModuleScaler("线性缩放器", workbench.view._alloc_index("线性缩放器"), QPointF(0, 0))
        second = ModuleScaler("线性缩放器", workbench.view._alloc_index("线性缩放器"), QPointF(220, 0))
        workbench.scene.addItem(first)
        workbench.scene.addItem(second)
        self.assertTrue(workbench.scene.create_connection(first.out_ports[0], second.in_ports[0]))
        workbench._name_edit.setText("用户反馈链路")

        saved = workbench.save_current_definition()

        self.assertEqual(saved["name"], "用户反馈链路")
        self.assertEqual(len(saved["nodes"]), 2)
        self.assertEqual(len(saved["edges"]), 1)
        self.assertEqual(len(saved["inputs"]), 1)
        self.assertEqual(len(saved["outputs"]), 1)
        self.assertGreaterEqual(len(saved["parameters"]), 2)
        self.assertIsNotNone(library.get(saved["id"]))
        workbench.close()

    def test_workbench_keyboard_activation_adds_non_composite_module(self):
        library = CustomCompositeLibrary(self.library_path)
        workbench = CustomCompositeWorkbench(library)
        item = workbench.palette.findItems("线性缩放器", Qt.MatchExactly)[0]

        created = workbench._add_palette_module(item)

        self.assertIsInstance(created, ModuleScaler)
        self.assertIs(created.scene(), workbench.scene)
        self.assertTrue(created.isSelected())
        workbench.close()

    def test_mainwindow_opens_one_workbench_and_refreshes_custom_library(self):
        settings = QSettings(
            f"{self.temp_dir.name}/ui.ini", QSettings.IniFormat
        )
        window = MainWindow(
            settings=settings,
            custom_composite_path=self.library_path,
        )
        window.show()
        self.app.processEvents()
        saved = window.custom_composite_library.save_definition(self._definition())
        self.app.processEvents()

        item = window.palette.findItems("双缩放链路", Qt.MatchExactly)[0]
        self.assertEqual(item.data(Qt.UserRole)["id"], saved["id"])
        window.custom_composite_btn.click()
        self.app.processEvents()
        first = window._custom_composite_workbench
        window.custom_composite_btn.click()
        self.app.processEvents()

        self.assertIsNotNone(first)
        self.assertIs(first, window._custom_composite_workbench)
        self.assertTrue(first.isVisible())
        self.assertFalse(first.isModal())
        window.close()
        self.app.processEvents()

    def test_mainwindow_saves_black_box_snapshot_and_restores_runtime_endpoint(self):
        settings = QSettings(f"{self.temp_dir.name}/config.ini", QSettings.IniFormat)
        window = MainWindow(
            settings=settings,
            custom_composite_path=self.library_path,
        )
        routed = []
        window._apply_routing = lambda dst, src, label, **_kwargs: routed.append(
            (dst, src, label)
        ) or True
        saved = window.custom_composite_library.save_definition(self._definition())
        black_box = window.view.instantiate_custom_composite(
            saved, QPointF(320.0, 180.0)
        )
        self.assertTrue(
            window.scene.create_connection(
                window.scene.left_ports[0], black_box.in_ports[0]
            )
        )

        config = window._build_config_dict()
        self.assertEqual(len(config["nodes"]), 1)
        self.assertEqual(config["nodes"][0]["kind"], "custom_composite")
        self.assertEqual(
            config["nodes"][0]["embedded_definition"]["name"], "双缩放链路"
        )
        self.assertEqual(len(config["edges"]), 1)

        window._clear_canvas()
        restored = window._create_node_from_config(config["nodes"][0])
        self.assertIsInstance(restored, CustomCompositeNode)
        node_map = {
            restored.name: restored,
            f"{restored.component_name}@{restored.index}": restored,
        }
        routed.clear()
        window._restore_edges(config["edges"], node_map)
        self.assertEqual(len(routed), 1)
        self.assertIn(restored.runtime_nodes["n1"].name, routed[0][2])
        window.close()
        self.app.processEvents()

    def test_configuration_preserves_repeated_black_box_display_ordinals(self):
        settings = QSettings(f"{self.temp_dir.name}/ordinal.ini", QSettings.IniFormat)
        window = MainWindow(
            settings=settings,
            custom_composite_path=self.library_path,
        )
        saved = window.custom_composite_library.save_definition(
            self._definition("双级反馈控制器")
        )
        window.view.instantiate_custom_composite(saved, QPointF(100, 100))
        window.view.instantiate_custom_composite(saved, QPointF(420, 100))
        config = window._build_config_dict()
        self.assertEqual(
            sorted(node["display_ordinal"] for node in config["nodes"]),
            [1, 2],
        )

        window._clear_canvas()
        restored = [window._create_node_from_config(node) for node in config["nodes"]]
        self.assertEqual(
            sorted(node.display_name for node in restored),
            ["双级反馈控制器", "双级反馈控制器2"],
        )
        window.close()
        self.app.processEvents()

    def test_agent_can_list_and_create_user_named_black_box(self):
        settings = QSettings(f"{self.temp_dir.name}/agent.ini", QSettings.IniFormat)
        window = MainWindow(
            settings=settings,
            custom_composite_path=self.library_path,
        )
        window.custom_composite_library.save_definition(self._definition())
        bridge = CanvasBridge(window)
        executor = ToolExecutor(bridge, module_registry=None)

        available = executor._list_modules({"scope": "available"})[
            "available_modules"
        ]
        custom = next(item for item in available if item["name"] == "双缩放链路")
        self.assertEqual(custom["category"], "custom_composite")
        self.assertEqual(custom["exposed_parameters"], ["first_stage_scale"])

        created = bridge.create_node("双缩放链路", position=(120, 90))
        self.assertTrue(created["success"])
        self.assertTrue(created["custom"])
        self.assertEqual(created["display_name"], "双缩放链路")
        self.assertEqual(len(bridge.list_nodes()), 1)
        window.close()
        self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
