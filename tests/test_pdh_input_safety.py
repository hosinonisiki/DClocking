"""Rejected visible edits must not silently start or save the previous values."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.qt_test_support import ensure_app
from PySide6.QtCore import QSettings
from qt_module import ModulePDHFSM
from qt_pdh_experiment import PDHExperimentWorkbench
from qt_ui_mainwindow import MainWindow
from FPGA_Agent.pdh_experiment import ExperimentProfile


PARAMETERS = dict(pc_cmd=0, threshold_signal_scan=20, threshold_signal_lock=70,
                  time_scan=2, time_lock=2, coef_scan=8192, coef_lock=21299)


class PDHInputSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.widget = PDHExperimentWorkbench()
        self.widget.set_parameters(PARAMETERS, "设备参数已读取")
        self.widget.set_profile(ExperimentProfile(
            clock_hz=1_000_000, polarity="dip", detector_source="已确认探测器",
            signal_path="ADC C → FIR2", error_path="MIXR → FIRF → PID",
            scan_path="ACC2", actuator_path="DAC B；已核对执行器范围",
        ))
        self.widget.set_context({"connected": True, "topology_issues": [], "routes": {}})
        self.commands, self.writes = [], []
        self.widget.command_requested.connect(self.commands.append)
        self.widget.apply_requested.connect(self.writes.append)

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()
        self.app.processEvents()

    def test_rejected_operator_duration_cannot_start_using_previous_value(self):
        self.widget.operator_editors["time_scan"].setValue(2**31)
        self.assertEqual(self.widget.preview_parameters()["time_scan"], 2)
        self.widget.start_experiment()
        self.assertEqual(self.commands, [], "输入失败后不能按隐藏的旧时间启动")
        self.assertEqual(self.writes, [])

    def test_rejected_operator_duration_cannot_silently_save_previous_value(self):
        self.widget.operator_editors["time_scan"].setValue(2**31)
        with self.assertRaises(ValueError):
            self.widget.export_bundle()
        self.assertEqual(self.writes, [])

    def test_invalid_engineering_duration_blocks_start_and_save(self):
        for text in ("invalid", "", "4294967296"):
            with self.subTest(text=text):
                self.commands.clear()
                self.widget.set_parameters(PARAMETERS, "设备参数已读取")
                self.widget._time_scan_editor.setText(text)
                self.assertIn("time_scan", self.widget._invalid_fields)
                self.widget.start_experiment()
                self.assertEqual(self.commands, [])
                with self.assertRaises(ValueError):
                    self.widget.export_bundle()
        self.assertEqual(self.writes, [])

    def test_corrected_engineering_value_restores_save_and_start(self):
        self.widget._time_scan_editor.setText("invalid")
        self.widget._time_scan_editor.setText("2")
        self.assertNotIn("time_scan", self.widget._invalid_fields)
        self.assertEqual(self.widget.export_bundle()["parameters"], PARAMETERS)
        self.widget.start_experiment()
        self.assertEqual(self.commands, [1])
        self.assertEqual(self.writes, [])

    def test_corrected_operator_draft_requires_apply_before_start(self):
        self.widget.operator_editors["time_scan"].setValue(2**31)
        self.widget.operator_editors["time_scan"].setValue(5)
        self.assertEqual(self.widget.export_bundle()["parameters"]["time_scan"], 5)
        self.widget.start_experiment()
        self.assertEqual(self.commands, [], "有效草稿仍需写入并核对后才能启动")
        # Emulate the explicit controller refresh after a successful readback;
        # the test does not emit any real parameter write.
        self.widget.set_parameters(dict(PARAMETERS, time_scan=5), "设备参数已读取")
        self.widget.start_experiment()
        self.assertEqual(self.commands, [1])
        self.assertEqual(self.writes, [])


class PDHLegacyCanvasRestoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.window = MainWindow(
            settings=QSettings(str(self.root / "ui.ini"), QSettings.IniFormat),
            experiment_repository_path=self.root / "records",
        )

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.temp.cleanup()

    def test_offline_canvas_roundtrip_preserves_legacy_uint32_without_writes(self):
        designer = self.window.open_pdh_workbench()
        node = next(n for n in self.window.scene.items() if isinstance(n, ModulePDHFSM))
        historical = dict(PARAMETERS, time_scan=2**32 - 1, time_lock=2**31, coef_scan=-1)
        node._params.update(historical)
        designer.set_parameters(historical, "历史设备读回值")
        payload = self.window._build_config_dict()
        path = self.root / "historical-canvas.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with patch("qt_ui_mainwindow.QFileDialog.getOpenFileName", return_value=(str(path), "")), \
                patch.object(self.window.port_ctrl, "send_param") as write, \
                patch.object(self.window, "_report_error") as report_error:
            self.window.load_configuration()
        restored = next(n for n in self.window.scene.items() if isinstance(n, ModulePDHFSM))
        self.assertEqual(restored.get_params(), historical)
        write.assert_not_called()
        report_error.assert_not_called()

    def test_new_hardware_write_still_rejects_legacy_out_of_int31_duration(self):
        self.window.open_pdh_workbench()
        node = next(n for n in self.window.scene.items() if isinstance(n, ModulePDHFSM))
        with self.assertRaises(RuntimeError):
            self.window._validate_pdh_inspector_params(node, {"time_scan": 2**31})


if __name__ == "__main__":
    unittest.main()
