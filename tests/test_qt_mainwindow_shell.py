import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QWidget

from tests.qt_test_support import ensure_app
from qt_ui_mainwindow import MainWindow


class MainWindowShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = QSettings(
            f"{self.temp_dir.name}/ui.ini", QSettings.IniFormat
        )
        self.window = MainWindow(settings=self.settings)
        self.window.resize(1280, 720)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def test_b2_shell_has_named_regions_and_canvas_first_split(self):
        for name in ("left_rail", "command_bar", "inspector_panel", "status_bar"):
            self.assertIsNotNone(self.window.findChild(QWidget, name))
        self.assertTrue(self.window.agent_toggle_btn.isHidden())
        self.assertTrue(self.window.agent_fab.isHidden())
        self.assertTrue(self.window.settings_rail_btn.isHidden())
        self.assertFalse(self.window.is_log_expanded())

    def test_existing_controls_and_slots_are_reused(self):
        self.assertEqual(self.window.connect_btn.text(), "连接设备")
        self.assertIs(self.window.workspace_splitter.widget(0), self.window.view)
        self.assertIs(self.window.workspace_splitter.widget(1), self.window.side_panel)

    def test_stderr_expands_log_and_preserves_message(self):
        self.window.set_log_expanded(False)
        self.window._append_error_text("route failed\n")
        self.app.processEvents()
        self.assertTrue(self.window.is_log_expanded())
        self.assertIn("route failed", self.window.log_output.toPlainText())

    def test_ui_state_round_trip_restores_log_and_splitter(self):
        self.window.set_log_expanded(True)
        self.window.workspace_splitter.setSizes([900, 310])
        self.window._save_ui_state()
        expected = self.window.workspace_splitter.sizes()
        self.window.close()
        restored = MainWindow(settings=self.settings)
        restored.resize(1280, 720)
        restored.show()
        self.app.processEvents()
        try:
            self.assertTrue(restored.is_log_expanded())
            actual = restored.workspace_splitter.sizes()
            self.assertAlmostEqual(actual[1], expected[1], delta=12)
        finally:
            restored.close()

    def test_clear_refreshes_route_status(self):
        from PySide6.QtCore import QPointF
        from qt_module import ModuleScaler

        source = ModuleScaler("线性缩放器", 0, QPointF(-200, 0))
        target = ModuleScaler("线性缩放器", 1, QPointF(200, 0))
        self.window.scene.addItem(source)
        self.window.scene.addItem(target)
        self.window.scene.create_connection(source.out_ports[0], target.in_ports[0])
        self.window._refresh_ui_status()
        self.assertEqual(self.window.route_status_label.text(), "1 routes")
        self.window._clear_canvas(False)
        self.assertEqual(self.window.route_status_label.text(), "0 routes")

    def test_offline_route_and_bad_config_expand_error_log(self):
        self.window.set_log_expanded(False)
        self.assertIsNone(self.window._ensure_router())
        self.assertTrue(self.window.is_log_expanded())
        self.assertIn("serial port not open", self.window.log_output.toPlainText())

        bad_config = Path(self.temp_dir.name) / "bad.json"
        bad_config.write_text("{not json", encoding="utf-8")
        self.window.set_log_expanded(False)
        with patch(
            "qt_ui_mainwindow.QFileDialog.getOpenFileName",
            return_value=(str(bad_config), "JSON (*.json)"),
        ):
            self.window.load_configuration()
        self.assertTrue(self.window.is_log_expanded())
        self.assertIn("load failed", self.window.log_output.toPlainText())

    def test_partial_config_reports_skipped_items_instead_of_success(self):
        config = Path(self.temp_dir.name) / "partial.json"
        config.write_text(
            '{"version": 1, "mode": "Free Mode", '
            '"nodes": [{"component_name": "未知模块", "index": 0}], '
            '"edges": []}',
            encoding="utf-8",
        )
        with patch(
            "qt_ui_mainwindow.QFileDialog.getOpenFileName",
            return_value=(str(config), "JSON (*.json)"),
        ):
            self.window.load_configuration()
        log = self.window.log_output.toPlainText()
        self.assertIn("skip unknown component", log)
        self.assertIn("partially loaded", log)
        self.assertNotIn(f"[config] loaded: {config}", log)

    def test_config_rail_button_does_not_stay_selected_after_successful_load(self):
        config = Path(self.temp_dir.name) / "empty.json"
        config.write_text(
            '{"version": 1, "mode": "Free Mode", "nodes": [], "edges": []}',
            encoding="utf-8",
        )

        with patch(
            "qt_ui_mainwindow.QFileDialog.getOpenFileName",
            return_value=(str(config), "JSON (*.json)"),
        ):
            self.window.config_rail_btn.click()
        self.app.processEvents()

        self.assertFalse(self.window.config_rail_btn.isChecked())

    def test_serial_constructor_failure_logs_original_exception(self):
        class FakeSerial:
            def isOpen(self):
                return False

            def open(self, _mode):
                return True

            def clear(self):
                pass

            def close(self):
                pass

        self.window.port_ctrl.serial_port = FakeSerial()
        with (
            patch.object(self.window.port_ctrl, "setport"),
            patch("qt_Port.QtSerial", side_effect=RuntimeError("wire failure")),
            patch("qt_Port.qw.QMessageBox.critical"),
        ):
            self.window.port_ctrl.open_port()
        self.assertTrue(self.window.is_log_expanded())
        self.assertIn("wire failure", self.window.log_output.toPlainText())
        self.assertFalse(self.window.port_ctrl.hw_controller.is_initialized())

    def test_disconnect_marks_hardware_uninitialized_for_dry_run(self):
        class FakeOpenSerial:
            def __init__(self):
                self.opened = True

            def isOpen(self):
                return self.opened

            def close(self):
                self.opened = False

        port = FakeOpenSerial()
        self.window.port_ctrl.serial_port = port
        self.window.port_ctrl.qt_serial = object()
        self.window.port_ctrl.hw_controller.ser = object()
        self.window.router = object()

        self.window.port_ctrl.open_port()

        self.assertFalse(port.isOpen())
        self.assertIsNone(self.window.port_ctrl.qt_serial)
        self.assertFalse(self.window.port_ctrl.hw_controller.is_initialized())
        self.assertIsNone(self.window.router)
        self.assertIsNone(self.window.port_ctrl.get_hw_module("PID", 0))

    def test_route_sync_failure_rolls_connection_back_to_disconnected(self):
        class FakeSerial:
            def __init__(self):
                self.opened = False

            def isOpen(self):
                return self.opened

            def open(self, _mode):
                self.opened = True
                return True

            def clear(self):
                pass

            def close(self):
                self.opened = False

        port = FakeSerial()
        self.window.port_ctrl.serial_port = port
        with (
            patch.object(self.window.port_ctrl, "setport"),
            patch("qt_Port.QtSerial", return_value=object()),
            patch.object(
                self.window,
                "sync_from_device",
                side_effect=RuntimeError("route timeout"),
            ),
            patch("qt_Port.qw.QMessageBox.warning") as warning,
        ):
            self.window.port_ctrl.open_port()

        self.assertFalse(port.isOpen())
        self.assertIsNone(self.window.port_ctrl.qt_serial)
        self.assertFalse(self.window.port_ctrl.hw_controller.is_initialized())
        self.assertIsNone(self.window.router)
        self.assertFalse(self.window.init_btn.isEnabled())
        self.assertEqual(self.window.connect_btn.text(), "连接")
        warning.assert_called_once()
        self.assertIn("route timeout", self.window.log_output.toPlainText())

    def test_router_cache_sync_failure_is_not_silently_ignored(self):
        router = Mock()
        router.sync.side_effect = RuntimeError("cache sync timeout")
        with patch.object(self.window, "_ensure_router", return_value=router):
            with self.assertRaisesRegex(RuntimeError, "cache sync timeout"):
                self.window._prime_router_cache_from_device_routes([])

    def test_parameter_refresh_aborts_after_one_register_exhausts_retries(self):
        from PySide6.QtCore import QPointF
        from qt_module import ModulePID

        node = ModulePID("PID控制器", 0, QPointF())
        original = node.get_params()
        with (
            patch.object(self.window.port_ctrl, "get_hw_module", return_value=object()),
            patch.object(
                self.window.port_ctrl,
                "read_module_value",
                side_effect=RuntimeError("offline after 4 attempts"),
            ) as read_value,
        ):
            refreshed = self.window._refresh_node_params_from_device(node)

        self.assertFalse(refreshed)
        self.assertEqual(read_value.call_count, 1)
        self.assertEqual(node.get_params(), original)

    def test_failed_batch_route_is_not_counted_or_uploaded(self):
        class BrokenRouter:
            def __init__(self):
                self.upload_calls = 0

            def set_routing(self, _dst, _src):
                raise RuntimeError("route staging failed")

            def upload(self):
                self.upload_calls += 1

        router = BrokenRouter()
        self.window._config_load_errors = []
        with patch.object(self.window, "_ensure_router", return_value=router):
            success = self.window._apply_routing(
                1,
                2,
                "test route",
                upload_immediately=False,
                error_reporter=self.window._report_config_error,
            )
        self.assertFalse(success)
        self.assertEqual(router.upload_calls, 0)
        self.assertEqual(len(self.window._config_load_errors), 1)
        self.assertIn("route staging failed", self.window._config_load_errors[0])

    def test_missing_router_during_batch_restore_counts_as_config_error(self):
        self.window._config_load_errors = []
        success = self.window._apply_routing(
            1,
            2,
            "offline route",
            upload_immediately=False,
            error_reporter=self.window._report_config_error,
        )
        self.assertFalse(success)
        self.assertEqual(len(self.window._config_load_errors), 1)
        self.assertIn("serial port not open", self.window._config_load_errors[0])


if __name__ == "__main__":
    unittest.main()
