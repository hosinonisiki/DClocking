import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QPoint, QPointF, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

from tests.qt_test_support import ensure_app
from qt_module import (
    FIRDesignerWidget,
    IIRDesignerWidget,
    ModuleFIRFilter,
    ModuleIIRFilter,
    ModulePID,
    PIDParamCanvas,
)
from qt_ui_mainwindow import MainWindow


class WorkspaceTabsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        settings = QSettings(
            f"{self.temp_dir.name}/workspace.ini", QSettings.IniFormat
        )
        self.window = MainWindow(
            settings=settings,
            custom_composite_path=Path(self.temp_dir.name) / "composites.json",
            experiment_repository_path=Path(self.temp_dir.name) / "records",
        )
        self.window.resize(1400, 820)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        if self.window._experiment_workbench is not None:
            self.window._experiment_workbench._close_without_prompt = True
        self.window.close()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def test_home_and_tool_workspaces_use_browser_style_tabs(self):
        tabs = self.window.workspace_tabs
        self.assertEqual(tabs.count(), 1)
        self.assertEqual(tabs.tabText(0), "主控制台")
        self.assertEqual(tabs.accessibleName(), "浏览器式工作区标签栏")

        experiment = self.window.open_experiment_workbench()
        custom = self.window.open_custom_composite_workbench()
        self.app.processEvents()

        self.assertEqual(tabs.count(), 3)
        self.assertEqual(tabs.tabText(tabs.indexOf(experiment)), "实验记录")
        self.assertEqual(tabs.tabText(tabs.indexOf(custom)), "自定义组合模块")
        self.assertIs(tabs.currentWidget(), custom)
        self.assertEqual(tabs.tabBar().tabToolTip(tabs.indexOf(custom)), "拖出标签栏可拆分为独立窗口")

    def test_reopening_workspace_focuses_existing_tab_without_duplicates(self):
        first = self.window.open_experiment_workbench()
        tab_count = self.window.workspace_tabs.count()
        self.window.workspace_tabs.show_home()

        second = self.window.open_experiment_workbench()
        self.app.processEvents()

        self.assertIs(first, second)
        self.assertEqual(self.window.workspace_tabs.count(), tab_count)
        self.assertIs(self.window.workspace_tabs.currentWidget(), first)

    def test_tool_tab_can_detach_and_return_to_main_window(self):
        workbench = self.window.open_experiment_workbench()
        tabs = self.window.workspace_tabs

        tab_bar = tabs.tabBar()
        tab_center = tab_bar.tabRect(tabs.indexOf(workbench)).center()
        drag_target = QPoint(tab_center.x(), tab_bar.height() + 100)
        QTest.mousePress(tab_bar, Qt.LeftButton, Qt.NoModifier, tab_center)
        QTest.mouseMove(tab_bar, drag_target, 20)
        QTest.mouseRelease(tab_bar, Qt.LeftButton, Qt.NoModifier, drag_target)
        self.app.processEvents()
        detached = tabs.detached_window("experiment-workbench")

        self.assertIsNotNone(detached)
        self.assertTrue(detached.isWindow())
        self.assertTrue(detached.isVisible())
        self.assertEqual(tabs.indexOf(workbench), -1)
        self.assertIs(tabs.detached_window("experiment-workbench"), detached)

        detached.reattach_button.click()
        self.app.processEvents()

        self.assertIsNone(tabs.detached_window("experiment-workbench"))
        self.assertGreaterEqual(tabs.indexOf(workbench), 1)
        self.assertIs(tabs.currentWidget(), workbench)

    def test_closing_dirty_tool_tab_can_be_cancelled(self):
        workbench = self.window.open_experiment_workbench()
        workbench.create_record("标签关闭保护", when=datetime(2026, 9, 10, 19, 30))
        workbench.editor.setPlainText("未保存")
        index = self.window.workspace_tabs.indexOf(workbench)

        with patch(
            "qt_experiment_workbench.QMessageBox.question",
            return_value=QMessageBox.Cancel,
        ):
            closed = self.window.workspace_tabs.close_tab(index)
        self.app.processEvents()

        self.assertFalse(closed)
        self.assertGreaterEqual(self.window.workspace_tabs.indexOf(workbench), 1)
        self.assertTrue(workbench.isVisible())

    def test_expanded_pid_fir_and_iir_views_open_as_tabs(self):
        cases = (
            (ModulePID("PID控制器", 0, QPointF(0, 0)), PIDParamCanvas, "PID控制器1 · 实时响应"),
            (ModuleFIRFilter("FIR滤波器", 0, QPointF(0, 0)), FIRDesignerWidget, "FIR滤波器1 · 滤波器设计"),
            (ModuleIIRFilter("IIR滤波器", 0, QPointF(0, 0)), IIRDesignerWidget, "IIR滤波器1 · 滤波器设计"),
        )

        for node, widget_type, expected_title in cases:
            with self.subTest(expected_title):
                self.window.scene.addItem(node)
                self.assertTrue(self.window._open_param_panel(node))
                self.app.processEvents()
                panel_key = f"{node.name}@{node.component_name}:{node.index}"
                panel = self.window._param_panels[panel_key]
                designer = panel.findChild(widget_type)
                self.assertIsNotNone(designer)

                expanded = designer.open_expanded_window()
                self.app.processEvents()
                index = self.window.workspace_tabs.indexOf(expanded)
                self.assertGreaterEqual(index, 1)
                self.assertEqual(self.window.workspace_tabs.tabText(index), expected_title)
                self.assertIs(self.window.workspace_tabs.currentWidget(), expanded)

                count = self.window.workspace_tabs.count()
                self.window.workspace_tabs.show_home()
                self.assertIs(designer.open_expanded_window(), expanded)
                self.app.processEvents()
                self.assertEqual(self.window.workspace_tabs.count(), count)
                self.assertIs(self.window.workspace_tabs.currentWidget(), expanded)


if __name__ == "__main__":
    unittest.main()
