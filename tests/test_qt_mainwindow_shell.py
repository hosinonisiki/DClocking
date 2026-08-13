import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
