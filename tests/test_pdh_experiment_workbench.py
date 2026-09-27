"""Operator journeys: drafts and observations must never masquerade as FPGA state."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.qt_test_support import ensure_app
from PySide6.QtCore import QPointF, QSettings
from qt_module import ModulePDHFSM
from qt_ui_mainwindow import MainWindow
from qt_pdh_experiment import PDHExperimentWorkbench
from FPGA_Agent.pdh_experiment import ExperimentProfile, demo_trace


PARAMS = dict(pc_cmd=0, threshold_signal_scan=2000, threshold_signal_lock=6000,
              time_scan=250, time_lock=1000, coef_scan=8192, coef_lock=24576)


class PDHExperimentWorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.widget = PDHExperimentWorkbench()
        self.widget.set_parameters(PARAMS, source_label="设备离线 · 本地配置（未读取）")
        self.widget.resize(1360, 850)
        self.widget.show()
        self.app.processEvents()

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()
        self.app.processEvents()

    def test_first_open_is_guided_and_does_not_invent_a_signal(self):
        self.assertEqual(self.widget.current_step, 0)
        self.assertIsNone(self.widget.trace)
        self.assertIn("未提供", self.widget.runtime_badge.text())
        self.assertEqual(self.widget.preview_parameters(), PARAMS)

    def test_operator_edits_and_demo_suggestions_are_drafts_only(self):
        writes = []
        self.widget.apply_requested.connect(writes.append)
        self.widget.set_profile(ExperimentProfile(clock_hz=250_000_000, polarity="dip"))
        self.widget.set_trace(demo_trace())
        self.widget.suggest_from_selection()
        self.assertTrue(self.widget.staged_parameters())
        self.assertEqual(writes, [])
        self.assertIn("演示", self.widget.trace_badge.text())
        self.assertEqual(self.widget.baseline_parameters(), PARAMS)

    def test_operator_units_round_trip_without_mutating_baseline(self):
        self.widget.set_profile(ExperimentProfile(clock_hz=250_000_000))
        self.widget.operator_editors["time_scan"].setValue(2.0)
        self.assertEqual(self.widget.staged_parameters()["time_scan"], 500)
        self.assertEqual(self.widget.baseline_parameters()["time_scan"], 250)

    def test_unknown_clock_disables_physical_duration_editing(self):
        self.assertFalse(self.widget.operator_editors["time_scan"].isEnabled())
        self.assertEqual(self.widget.preview_parameters()["time_scan"], 250)

    def test_switching_modes_does_not_send_commands(self):
        commands = []
        self.widget.command_requested.connect(commands.append)
        self.widget.mode_combo.setCurrentIndex(1)
        self.assertEqual(commands, [])
        self.assertFalse(self.widget.operator_editors["time_scan"].isEnabled())

    def test_guided_daily_and_engineering_views_share_one_draft(self):
        self.widget.set_trace(demo_trace())
        self.widget.stage_value("threshold_signal_scan", 3100)
        for index in (1, 2, 0, 1, 0):
            self.widget.views.setCurrentIndex(index)
            self.app.processEvents()
            self.assertEqual(self.widget.staged_parameters()["threshold_signal_scan"], 3100)
            self.assertEqual(self.widget.trace.source, "demo")
            if index != 2:
                self.assertTrue(self.widget.waveform.isVisible())
                self.assertEqual(self.widget._flow.parentWidget(), self.widget.views.currentWidget())

    def test_bundle_roundtrip_retains_profile_draft_and_trace_not_hardware_truth(self):
        self.widget.set_profile(ExperimentProfile(name="光腔 A", clock_hz=250_000_000))
        self.widget.set_trace(demo_trace())
        self.widget.stage_value("threshold_signal_scan", 3000)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pdh.json"
            self.widget.save_bundle(path)
            other = PDHExperimentWorkbench()
            try:
                other.set_parameters(PARAMS, source_label="设备离线 · 本地配置（未读取）")
                other.load_bundle(path)
                self.assertEqual(other.profile.name, "光腔 A")
                self.assertEqual(other.staged_parameters()["threshold_signal_scan"], 3000)
                self.assertEqual(other.trace.source, "demo")
                self.assertIn("未提供", other.runtime_badge.text())
                self.assertEqual(other.baseline_parameters(), PARAMS)
            finally:
                other.close()

    def test_invalid_bundle_does_not_partially_replace_state(self):
        before = self.widget.export_bundle()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps({"version": 99}), encoding="utf-8")
            with self.assertRaises(ValueError):
                self.widget.load_bundle(path)
        self.assertEqual(self.widget.export_bundle(), before)

    def test_import_baseline_overwrites_previous_draft_and_retains_legacy_duration(self):
        payload = self.widget.export_bundle()
        self.widget.stage_value("threshold_signal_scan", 3100)
        payload["parameters"]["time_scan"] = 2**32-1
        self.widget.import_bundle(payload)
        self.assertEqual(self.widget.preview_parameters()["threshold_signal_scan"], PARAMS["threshold_signal_scan"])
        self.assertEqual(self.widget.preview_parameters()["time_scan"], 2**32-1)
        self.assertFalse(self.widget.apply_button.isEnabled())

    def test_file_source_is_replay_even_when_payload_claims_live(self):
        payload = self.widget.export_bundle()
        payload["trace"] = dict(demo_trace().to_dict(), source="live", label="saved CH1")
        self.widget.import_bundle(payload)
        self.assertEqual(self.widget.trace.source, "import")
        self.assertIn("回放", self.widget.trace_badge.text())

    def test_invalid_display_profile_cannot_partially_replace_bundle(self):
        before = self.widget.export_bundle()
        payload = dict(before, profile=dict(before["profile"], units_per_count=1e308))
        with self.assertRaises(ValueError):
            self.widget.import_bundle(payload)
        self.assertEqual(self.widget.export_bundle(), before)

    def test_verified_feedback_does_not_ask_for_duplicate_readback(self):
        self.widget.set_apply_result(True, "参数已回读一致", readback_confirmed=True)
        self.assertNotIn("请回读", self.widget.operation_feedback.text())

    def test_refresh_conflict_keeps_draft_until_explicit_rebase(self):
        self.widget.stage_value("threshold_signal_scan", 3100)
        self.widget.accept_refresh(dict(PARAMS, threshold_signal_scan=2200), "设备参数已读取")
        self.assertEqual(self.widget.preview_parameters()["threshold_signal_scan"], 3100)
        self.assertIsNotNone(self.widget._conflict_message)
        self.widget.resolve_refresh(keep_draft=True)
        self.assertIsNone(self.widget._conflict_message)
        self.assertEqual(self.widget.baseline_parameters()["threshold_signal_scan"], 2200)
        self.assertEqual(self.widget.staged_parameters()["threshold_signal_scan"], 3100)

    def test_preflight_blocks_start_without_experiment_mapping(self):
        commands = []
        self.widget.command_requested.connect(commands.append)
        self.widget.start_experiment()
        self.assertEqual(commands, [])
        self.assertIn("未发送", self.widget.operation_feedback.text())


class PDHExperimentIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.window = MainWindow(settings=QSettings(str(Path(self.temp.name)/"ui.ini"), QSettings.IniFormat),
                                 experiment_repository_path=Path(self.temp.name)/"records")
        self.window.show()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.temp.cleanup()

    def test_rail_opens_one_reusable_pdh_tab_without_hardware_write(self):
        with patch.object(self.window.port_ctrl, "send_param") as write:
            first = self.window.open_pdh_workbench()
            second = self.window.open_pdh_workbench()
        self.assertIs(first, second)
        self.assertIsInstance(first, PDHExperimentWorkbench)
        self.assertEqual(len([n for n in self.window.scene.items() if isinstance(n, ModulePDHFSM)]), 1)
        write.assert_not_called()

    def test_profile_is_embedded_in_existing_config_and_restored(self):
        widget = self.window.open_pdh_workbench()
        widget.set_profile(ExperimentProfile(name="腔 A", clock_hz=250_000_000))
        payload = self.window._build_config_dict()
        saved = next(n for n in payload["nodes"] if n["component_name"] == "PDH状态机")
        self.assertEqual(saved["pdh_experiment"]["profile"]["name"], "腔 A")
        self.window._clear_canvas(False)
        node = self.window._create_node_from_config(saved)
        restored = self.window._open_pdh_designer(node)
        self.assertEqual(restored.profile.name, "腔 A")

    def test_experiment_diagnosis_does_not_report_command_as_lock(self):
        self.window.open_pdh_workbench()
        node = next(n for n in self.window.scene.items() if isinstance(n, ModulePDHFSM))
        node._params["pc_cmd"] = 2
        snapshot = self.window.pdh_experiment_snapshot(node)
        self.assertEqual(snapshot["runtime_state"], "unknown")
        self.assertFalse(snapshot["hardware_state_available"])
        self.assertTrue(snapshot["topology_issues"])

    def test_changed_cache_does_not_inherit_old_verified_source(self):
        widget = self.window.open_pdh_workbench()
        node = next(n for n in self.window.scene.items() if isinstance(n, ModulePDHFSM))
        widget.set_parameters(node.get_params(), "设备参数已读取")
        self.assertIn("设备参数已读取", self.window.pdh_experiment_snapshot(node)["parameter_source"])
        node._params["threshold_signal_scan"] += 1
        snapshot = self.window.pdh_experiment_snapshot(node)
        self.assertNotIn("设备参数已读取", snapshot["parameter_source"])

    def test_invalid_profile_save_is_reported_and_preserves_existing_file(self):
        widget = self.window.open_pdh_workbench()
        widget.profile_fields["clock_hz"].setText("not a clock")
        path = Path(self.temp.name) / "saved.json"
        path.write_text("existing configuration", encoding="utf-8")
        with patch("qt_ui_mainwindow.QFileDialog.getSaveFileName", return_value=(str(path), "")), \
                patch.object(self.window, "_report_error") as report:
            self.window.save_configuration()
        self.assertEqual(path.read_text(encoding="utf-8"), "existing configuration")
        report.assert_called_once()
        self.assertIn("save failed", report.call_args.args[0])

    def test_connection_presentation_refreshes_open_workbench_without_device_io(self):
        widget = self.window.open_pdh_workbench()
        with patch.object(self.window.serial_port, "isOpen", return_value=True), \
                patch.object(self.window, "_refresh_node_params_from_device") as read:
            self.window._refresh_ui_status()
            self.assertIn("已连接", widget.connection_badge.text())
        self.window._refresh_ui_status()
        self.assertIn("离线", widget.connection_badge.text())
        read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
