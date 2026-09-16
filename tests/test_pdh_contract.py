"""Regression checks for the existing PDH register ABI and its UI vocabulary."""

import unittest
import sys
import os
import subprocess
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _module_dir in (_PROJECT_ROOT / "python control", _PROJECT_ROOT / "FPGA_Agent"):
    if str(_module_dir) not in sys.path:
        sys.path.insert(0, str(_module_dir))

from module import ModulePDHFSM
from module_registry import get_module
from qt_module_schema import PDH_SCHEMA


class _RecordingBus:
    def __init__(self):
        self.writes = []
        self.reads = []

    def write(self, module_name, address, data, hold=False):
        self.writes.append((module_name, address, data, hold))
        return True

    def read(self, module_name, address):
        self.reads.append((module_name, address))
        return (16384).to_bytes(2, "big")


class PDHParameterContractTests(unittest.TestCase):
    def test_agent_registry_imports_without_ui_launcher_bootstrap(self):
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable, "-c",
             "from FPGA_Agent.module_registry import get_module; "
             "assert len(get_module('PDH状态机')['direct_params']) == 7"],
            cwd=_PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_seven_existing_keys_keep_their_register_addresses(self):
        expected = [
            "pc_cmd", "threshold_signal_lock", "threshold_signal_scan",
            "time_scan", "time_lock", "coef_scan", "coef_lock",
        ]
        self.assertEqual([field["key"] for field in PDH_SCHEMA], expected)
        module = ModulePDHFSM(_RecordingBus(), "PDHS")
        for address, key in enumerate(expected):
            with self.subTest(key=key):
                self.assertEqual(module.process_designator(key), address)

    def test_coefficient_names_read_and_write_existing_slots(self):
        bus = _RecordingBus()
        module = ModulePDHFSM(bus, "PDHS")
        module.write("coef_scan", 16384)
        module.write("coef_lock", -1)
        self.assertEqual(bus.writes, [
            ("PDHS", 5, 16384, False),
            ("PDHS", 6, 65535, False),
        ])
        self.assertEqual(module.read("coef_scan"), (16384).to_bytes(2, "big"))
        self.assertEqual(module.read("coef_lock"), (16384).to_bytes(2, "big"))
        self.assertEqual(bus.reads, [("PDHS", 5), ("PDHS", 6)])

    def test_labels_describe_what_causes_each_transition(self):
        fields = {field["key"]: field for field in PDH_SCHEMA}
        self.assertIn("入锁", fields["threshold_signal_scan"]["label"])
        self.assertIn("失锁", fields["threshold_signal_lock"]["label"])
        self.assertIn("确认", fields["time_scan"]["label"])
        self.assertIn("确认", fields["time_lock"]["label"])
        self.assertNotIn("超时", fields["time_lock"]["label"])
        self.assertNotIn("模式", fields["pc_cmd"]["label"])
        self.assertNotIn("3=auto lock", fields["pc_cmd"]["note"])
        self.assertNotIn("自动锁定退出", fields["pc_cmd"]["note"])

    def test_raw_adc_and_q15_descriptions_do_not_claim_calibration(self):
        fields = {field["key"]: field for field in PDH_SCHEMA}
        for key in ("threshold_signal_scan", "threshold_signal_lock"):
            with self.subTest(key=key):
                self.assertNotIn("display_voltage", fields[key])
                self.assertIn("ADC", fields[key]["note"])
        for key in ("coef_scan", "coef_lock"):
            with self.subTest(key=key):
                self.assertIn("Q1.15", fields[key]["note"])
                self.assertIn("32768", fields[key]["note"])

    def test_agent_lists_same_editable_keys_and_labels_as_qt(self):
        registry_params = get_module("PDH状态机")["direct_params"]
        self.assertEqual(
            [(param["key"], param["label"]) for param in registry_params],
            [(field["key"], field["label"]) for field in PDH_SCHEMA],
        )
        self.assertEqual(
            [param["type"] for param in registry_params],
            [field["type"] for field in PDH_SCHEMA],
        )
        self.assertNotIn(
            "HIGH = PID active",
            get_module("PDH状态机")["outputs"][0]["description"],
        )


if __name__ == "__main__":
    unittest.main()
