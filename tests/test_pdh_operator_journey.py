"""PDH first-use journeys driven through Qt controls, without a connected FPGA."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tests.qt_test_support import ensure_app
from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QPushButton, QScrollArea

from FPGA_Agent.pdh_experiment import ExperimentProfile, WaveformTrace, demo_trace
from qt_module import ModulePDHFSM
from qt_pdh_experiment import PDHExperimentWorkbench
from qt_ui_mainwindow import MainWindow


PARAMS = dict(pc_cmd=0, threshold_signal_scan=2000, threshold_signal_lock=6000,
              time_scan=250000, time_lock=500000, coef_scan=8192, coef_lock=24576)


class _QtJourney(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.errors = []
        self.dialogs = []
        hook = patch("sys.excepthook", lambda *exc: self.errors.append(exc))
        hook.start()
        self.addCleanup(hook.stop)
        for method in ("warning", "critical", "information", "question"):
            dialog = patch.object(QMessageBox, method, side_effect=self._record_dialog)
            dialog.start()
            self.addCleanup(dialog.stop)
        self.temp = tempfile.TemporaryDirectory(prefix="pdh-journey-")
        self.addCleanup(self.temp.cleanup)

    def _record_dialog(self, *args, **kwargs):
        self.dialogs.append((args, kwargs))
        return QMessageBox.Cancel

    def assert_no_callback_errors(self):
        self.assertEqual([(type(exc).__name__, str(exc)) for _, exc, _ in self.errors], [])
        self.assertEqual(self.dialogs, [], "An unexpected modal dialog interrupted the journey")

    def click(self, owner, name):
        button = owner.findChild(QPushButton, name)
        self.assertIsNotNone(button, name)
        self.reveal(button)
        self.assertTrue(button.isVisible(), name)
        self.assertTrue(button.isEnabled(), name)
        QTest.mouseClick(button, Qt.LeftButton)
        self.app.processEvents()

    def type_text(self, editor, text):
        self.reveal(editor)
        editor.setFocus()
        editor.selectAll()
        QTest.keyClicks(editor, text)
        QTest.keyClick(editor, Qt.Key_Return)
        self.app.processEvents()

    def reveal(self, widget):
        parent = widget.parentWidget()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                parent.ensureWidgetVisible(widget)
            parent = parent.parentWidget()
        self.app.processEvents()


class PDHFirstUseJourneyTests(_QtJourney):
    def setUp(self):
        super().setUp()
        self.widget = PDHExperimentWorkbench()
        self.widget.set_parameters(PARAMS, "离线原始配置")
        self.widget.resize(1400, 920)
        self.widget.show()
        self.app.processEvents()
        self.commands, self.writes = [], []
        self.widget.command_requested.connect(self.commands.append)
        self.widget.apply_requested.connect(self.writes.append)

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()
        self.app.processEvents()
        self.assert_no_callback_errors()

    def test_guide_demo_selection_drag_and_mode_switch_are_only_drafts(self):
        self.assertEqual(self.widget.current_step, 0)
        self.assertIsNone(self.widget.trace)
        self.type_text(self.widget.profile_fields["clock_hz"], "250000000")
        self.assertEqual(self.widget.profile.clock_hz, 250000000)
        self.click(self.widget, "pdh_step_next")
        self.assertEqual(self.widget.current_step, 1)
        self.click(self.widget, "pdh_demo_trace")
        self.assertEqual(self.widget.trace.source, "demo")
        self.assertIn("非实测", self.widget.trace_badge.text())

        canvas = self.widget.waveform
        rect = canvas._plot_rect()
        start = QPoint(int(rect.left() + rect.width() * 0.3), int(rect.top() + 10))
        end = QPoint(int(rect.left() + rect.width() * 0.7), start.y())
        QTest.mousePress(canvas, Qt.LeftButton, pos=start)
        QTest.mouseMove(canvas, end)
        QTest.mouseRelease(canvas, Qt.LeftButton, pos=end)
        self.assertAlmostEqual(canvas.selection[0], 0.006, delta=0.0001)
        self.assertAlmostEqual(canvas.selection[1], 0.014, delta=0.0001)

        self.click(self.widget, "pdh_step_next")
        self.assertEqual(self.widget.current_step, 2)
        for key, delta in (("threshold_signal_scan", QPoint(0, -15)), ("time_scan", QPoint(30, 0))):
            marker = canvas.marker_position(key).toPoint()
            QTest.mousePress(canvas, Qt.LeftButton, pos=marker)
            QTest.mouseMove(canvas, marker + delta)
            QTest.mouseRelease(canvas, Qt.LeftButton, pos=marker + delta)
            self.assertNotEqual(self.widget.preview_parameters()[key], PARAMS[key])
        self.assertEqual(self.widget.baseline_parameters(), PARAMS)
        self.assertIn("离线判据预演", self.widget.replay_label.text())
        self.widget.mode_combo.setFocus()
        QTest.keyClick(self.widget.mode_combo, Qt.Key_Down)
        self.assertEqual(self.widget.mode_combo.currentIndex(), 1)
        self.assertFalse(self.widget.operator_editors["time_scan"].isEnabled())
        self.assertIn("不代表自动生效值", self.widget.replay_label.text())
        QTest.keyClick(self.widget.mode_combo, Qt.Key_Up)
        self.assertEqual(self.widget.mode_combo.currentIndex(), 0)
        self.assertEqual(self.commands, [])
        self.assertEqual(self.writes, [])

    def test_bundle_buttons_roundtrip_legacy_uint32_and_never_execute_saved_command(self):
        path = Path(self.temp.name) / "方案 with spaces.json"
        legacy = dict(PARAMS, time_scan=2**32 - 1, pc_cmd=2)
        self.widget.set_parameters(legacy, "历史文件配置")
        self.widget.set_profile(ExperimentProfile(name="旧实验", clock_hz=None))
        self.widget.set_trace(demo_trace())
        self.widget.waveform.set_selection(0.006, 0.014)
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(path), "JSON")):
            self.click(self.widget, "pdh_bundle_save")
        self.assertEqual(json.loads(path.read_text())["parameters"]["time_scan"], 2**32 - 1)

        self.widget.set_parameters(PARAMS, "当前画布配置")
        with patch.object(QFileDialog, "getOpenFileName", return_value=(str(path), "JSON")):
            self.click(self.widget, "pdh_bundle_open")
        self.assertEqual(self.widget.preview_parameters()["time_scan"], 2**32 - 1)
        self.assertEqual(self.widget.preview_parameters()["pc_cmd"], 0)
        self.assertEqual(self.widget.waveform.selection, (0.006, 0.014))
        self.assertFalse(self.widget.operator_editors["time_scan"].isEnabled())
        self.assertIsNone(self.widget.waveform.marker_position("time_scan"))
        self.assertFalse(self.widget.scope_mapping_confirmed.isChecked())
        self.assertEqual(self.commands, [])
        self.assertEqual(self.writes, [])

    def test_invalid_clock_blocks_navigation_and_invalid_bundle_is_atomic(self):
        self.type_text(self.widget.profile_fields["clock_hz"], "not-a-frequency")
        self.click(self.widget, "pdh_step_next")
        self.assertEqual(self.widget.current_step, 0)
        self.assertIsNone(self.widget.profile.clock_hz)
        self.assertEqual(self.widget.preview_parameters(), PARAMS)
        self.type_text(self.widget.profile_fields["clock_hz"], "250000000")
        before = self.widget.export_bundle()
        malformed = json.loads(json.dumps(before))
        malformed["profile"]["clock_hz"] = -250000000
        path = Path(self.temp.name) / "bad-clock.json"
        path.write_text(json.dumps(malformed), encoding="utf-8")
        with patch.object(QFileDialog, "getOpenFileName", return_value=(str(path), "JSON")):
            self.click(self.widget, "pdh_bundle_open")
        self.assertIn("方案未载入", self.widget.operation_feedback.text())
        self.assertEqual(self.widget.export_bundle(), before)
        self.assertEqual(self.commands, [])
        self.assertEqual(self.writes, [])

    def test_signal_mapping_changes_require_fresh_channel_confirmation(self):
        self.widget.set_profile(ExperimentProfile(detector_source="Detector A", signal_path="ADC A"))
        self.widget.scope_mapping_confirmed.setChecked(True)
        live = WaveformTrace((0, 0.001, 0.002), (10000, 2000, 10000), "live", "CH1 测试快照")
        self.widget.set_trace(live)
        self.type_text(self.widget.profile_fields["signal_path"], "ADC B")
        self.assertFalse(self.widget.scope_mapping_confirmed.isChecked())
        self.assertIsNone(self.widget.trace)
        self.widget.scope_mapping_confirmed.setChecked(True)
        self.type_text(self.widget.profile_fields["units_per_count"], "0.001")
        self.assertFalse(self.widget.scope_mapping_confirmed.isChecked())
        self.widget.scope_mapping_confirmed.setChecked(True)
        self.widget.set_profile(ExperimentProfile(detector_source="Detector C", signal_path="ADC C"))
        self.assertFalse(self.widget.scope_mapping_confirmed.isChecked())
        self.widget.scope_mapping_confirmed.setChecked(True)
        self.widget.set_trace(live)
        self.widget.set_context(dict(connected=False, routes={"signal": "ADC D"}, topology_issues=[]))
        self.assertFalse(self.widget.scope_mapping_confirmed.isChecked())
        self.assertIsNone(self.widget.trace)


class PDHMainWindowJourneyTests(_QtJourney):
    def setUp(self):
        super().setUp()
        root = Path(self.temp.name)
        self.window = MainWindow(
            settings=QSettings(str(root / "ui.ini"), QSettings.IniFormat),
            experiment_repository_path=root / "records", custom_composite_path=root / "composites.json",
        )
        self.window.resize(1600, 1000)
        self.window.show()
        self.app.processEvents()
        self.write_patch = patch.object(self.window.port_ctrl, "send_param")
        self.write = self.write_patch.start()
        self.addCleanup(self.write_patch.stop)
        self.serial_patch = patch.object(self.window.serial_port, "write")
        self.serial_write = self.serial_patch.start()
        self.addCleanup(self.serial_patch.stop)
        self.open_patch = patch.object(self.window.serial_port, "open")
        self.serial_open = self.open_patch.start()
        self.addCleanup(self.open_patch.stop)

    def tearDown(self):
        self.window._oscilloscope_workbench = None  # Stub receiver never owns a socket or timer.
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.write.assert_not_called()
        self.serial_write.assert_not_called()
        self.serial_open.assert_not_called()
        self.assert_no_callback_errors()

    def open_via_rail(self):
        QTest.mouseClick(self.window.pdh_rail_btn, Qt.LeftButton)
        self.app.processEvents()
        self.assertEqual(len(self.window._pdh_designers), 1)
        return next(iter(self.window._pdh_designers.values()))

    def test_repeated_node_doubleclick_and_rail_reuse_same_tab(self):
        widget = self.open_via_rail()
        node = next(item for item in self.window.scene.items() if isinstance(item, ModulePDHFSM))
        count = self.window.workspace_tabs.count()
        for _ in range(2):
            self.window.workspace_tabs.show_home()
            self.window.view.centerOn(node)
            self.app.processEvents()
            point = self.window.view.mapFromScene(node.mapToScene(node.boundingRect().center()))
            self.assertIs(self.window.view.itemAt(point), node)
            # Separate gestures: the view intentionally deduplicates click and
            # double-click notifications within one OS double-click interval.
            QTest.qWait(QApplication.doubleClickInterval() + 10)
            QTest.mouseDClick(self.window.view.viewport(), Qt.LeftButton, pos=point)
            self.app.processEvents()
            self.assertIs(self.window.workspace_tabs.currentWidget(), widget)
            self.assertEqual(self.window.workspace_tabs.count(), count)
        self.assertIs(self.open_via_rail(), widget)
        self.assertEqual(len([item for item in self.window.scene.items() if isinstance(item, ModulePDHFSM)]), 1)

    def test_explicit_local_stage_changes_node_and_creates_real_experiment_record(self):
        widget = self.open_via_rail()
        node = next(item for item in self.window.scene.items() if isinstance(item, ModulePDHFSM))
        widget.set_parameters(PARAMS, "本地配置")
        node._params.update(PARAMS)
        widget.set_profile(ExperimentProfile(name="离线验收", clock_hz=250000000))
        self.click(widget, "pdh_step_2")
        editor = widget.operator_editors["threshold_signal_scan"].lineEdit()
        self.type_text(editor, "3000")
        self.assertEqual(node.get_params()["threshold_signal_scan"], 2000)
        self.click(widget, "pdh_stage_local")
        self.assertEqual(node.get_params()["threshold_signal_scan"], 3000)
        self.assertEqual(widget.staged_parameters(), {})
        self.assertIn("未写入 FPGA", widget.operation_feedback.text())
        self.click(widget, "pdh_record")
        record = self.window._experiment_workbench
        self.assertTrue(record.current_path.is_file())
        self.assertTrue(record.current_path.resolve().is_relative_to((Path(self.temp.name) / "records").resolve()))
        text = record.current_path.read_text(encoding="utf-8")
        self.assertIn("离线验收", text)
        self.assertIn("3000", text)
        self.assertIn("不能确认已锁定", text)
        self.assertFalse(record.editor.document().isModified())

    def test_snapshot_requires_channel_confirmation_and_available_observation(self):
        widget = self.open_via_rail()
        self.click(widget, "pdh_step_1")
        scope = SimpleNamespace(pdh_snapshot=Mock(return_value=None), shutdown=Mock())
        self.window._oscilloscope_workbench = scope
        self.click(widget, "pdh_scope_snapshot")
        self.assertIsNone(widget.trace)
        self.assertIn("请先确认 CH1", widget.operation_feedback.text())
        scope.pdh_snapshot.assert_not_called()
        QTest.mouseClick(widget.scope_mapping_confirmed, Qt.LeftButton,
                         pos=QPoint(8, widget.scope_mapping_confirmed.height() // 2))
        self.assertTrue(widget.scope_mapping_confirmed.isChecked())
        self.click(widget, "pdh_scope_snapshot")
        self.assertIsNone(widget.trace)
        self.assertIn("尚无可分析", widget.operation_feedback.text())
        observation = dict(time_s=[index / 1000 for index in range(8)],
                           values=[10000, 8000, 4000, 2000, 2500, 5000, 8000, 10000],
                           source="live", label="CH1 实测快照")
        scope.pdh_snapshot.return_value = observation
        self.click(widget, "pdh_scope_snapshot")
        self.assertEqual(widget.trace.source, "live")
        self.assertEqual(len(widget.trace.value), 8)
        self.assertAlmostEqual(widget.trace.time_s[-1], 0.007)
        self.assertIn("非连续遥测", widget.trace_badge.text())
        self.assertIn("无包序号", widget.operation_feedback.text())
        self.assertIn("未提供", widget.runtime_badge.text())
        scope.pdh_snapshot.return_value = dict(observation, source="demo", label="CH1 仿真快照")
        self.click(widget, "pdh_scope_snapshot")
        self.assertEqual(widget.trace.source, "demo")
        self.assertIn("非实测", widget.trace_badge.text())


if __name__ == "__main__":
    unittest.main()
