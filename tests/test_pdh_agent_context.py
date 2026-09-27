"""Read-only Agent experiment context and source-verified PDH reference roles."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from FPGA_Agent.canvas_bridge import CanvasBridge
from FPGA_Agent.module_registry import MODULE_REGISTRY, PDH_LOCKING_PATTERN


class _Node:
    def __init__(self, name="PDHS", component="PDH状态机"):
        self.name, self.component_name = name, component
        self.display_name = component + "1"
        self.index, self.num_inputs, self.num_outputs = 0, 2, 3

    def pos(self):
        return SimpleNamespace(x=lambda: 10, y=lambda: 20)

    def get_params(self):
        return {"pc_cmd": 1}


class PDHAgentContextTests(unittest.TestCase):
    def setUp(self):
        self.node = _Node()
        self.snapshot = {
            "profile": {"name": "腔 A", "clock_hz": None},
            "parameters": {"pc_cmd": 1, "threshold_signal_scan": 500},
            "parameter_source": "本地画布缓存（未读设备）",
            "runtime_state": "unknown", "hardware_state_available": False,
            "routes": {"signal": "FIR2 → PDHS"}, "topology_issues": [],
            "connected": True,
        }
        self.window = SimpleNamespace(
            scene=SimpleNamespace(items=lambda: [self.node, _Node("PIDC", "PID控制器")]),
            view=SimpleNamespace(), pdh_experiment_snapshot=Mock(return_value=self.snapshot),
            _open_pdh_designer=Mock(side_effect=AssertionError("must not open UI")),
            hw=Mock(),
        )
        self.bridge = CanvasBridge(self.window)
        self.modules = patch.dict("sys.modules", {"qt_module": SimpleNamespace(NodeItem=_Node)})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def test_list_nodes_includes_read_only_context_only_for_pdh(self):
        nodes = self.bridge.list_nodes()
        context = nodes[0]["pdh_experiment"]
        self.assertEqual(context["profile"]["name"], "腔 A")
        self.assertEqual(context["runtime_state"], "unknown")
        self.assertFalse(context["hardware_state_available"])
        self.assertIn("未读设备", context["parameter_source"])
        self.assertIn("不是", context["interpretation_note"])
        self.assertNotIn("pdh_experiment", nodes[1])
        self.window.pdh_experiment_snapshot.assert_called_once_with(self.node)
        self.window._open_pdh_designer.assert_not_called()
        self.assertEqual(self.window.hw.mock_calls, [])

    def test_context_is_detached_and_command_is_never_inferred_as_lock(self):
        result = self.bridge.list_nodes()[0]["pdh_experiment"]
        result["profile"]["name"] = "changed"
        result["parameters"]["pc_cmd"] = 3
        self.assertEqual(self.snapshot["profile"]["name"], "腔 A")
        self.assertEqual(self.snapshot["parameters"]["pc_cmd"], 1)
        self.assertEqual(result["runtime_state"], "unknown")

    def test_snapshot_absent_fails_closed_without_opening_or_device_access(self):
        del self.window.pdh_experiment_snapshot
        context = self.bridge.list_nodes()[0]["pdh_experiment"]
        self.assertEqual(context["runtime_state"], "unknown")
        self.assertFalse(context["hardware_state_available"])
        self.assertEqual(context["parameter_source"], "unavailable")
        self.window._open_pdh_designer.assert_not_called()

    def test_snapshot_failure_does_not_break_canvas_introspection(self):
        self.window.pdh_experiment_snapshot.side_effect = RuntimeError("unavailable")
        context = self.bridge.list_nodes()[0]["pdh_experiment"]
        self.assertEqual(context["runtime_state"], "unknown")
        self.assertEqual(context["context_error"], "snapshot_unavailable")

    def test_invalid_snapshot_does_not_break_canvas_introspection(self):
        self.window.pdh_experiment_snapshot.return_value = None
        context = self.bridge.list_nodes()[0]["pdh_experiment"]
        self.assertEqual(context["context_error"], "snapshot_unavailable")

    def test_canvas_state_and_parameter_query_use_same_context(self):
        with patch.object(self.bridge, "list_connections", return_value=[]):
            state = self.bridge.get_canvas_state()
        queried = self.bridge.get_node_params("PDHS")
        self.assertEqual(state["nodes"][0]["pdh_experiment"]["profile"], queried["pdh_experiment"]["profile"])
        self.assertEqual(queried["params"], {"pc_cmd": 1})

    def test_unavailable_hardware_state_cannot_be_labelled_locked(self):
        self.snapshot["runtime_state"] = "locked"
        context = self.bridge.list_nodes()[0]["pdh_experiment"]
        self.assertEqual(context["runtime_state"], "unknown")


class PDHReferenceTests(unittest.TestCase):
    def test_pdh_identifiers_and_port_counts_stay_compatible(self):
        spec = MODULE_REGISTRY["PDH状态机"]
        self.assertEqual(spec["internal_names"], ["PDHS"])
        self.assertEqual([p["name"] for p in spec["inputs"]], ["IN_POWER", "IN_SCAN"])
        self.assertEqual([p["name"] for p in spec["outputs"]],
                         ["PID_RESET_CTRL", "MIXER_RESET_CTRL", "SCAN_RESET_CTRL"])
        self.assertEqual(len(spec["direct_params"]), 7)

    def test_power_description_does_not_assume_transmission_or_adc_scaling(self):
        power = MODULE_REGISTRY["PDH状态机"]["inputs"][0]
        self.assertIn("判锁", power["display"])
        self.assertNotIn("透射", power["display"])
        self.assertIn("internal", power["description"])
        self.assertIn("below", power["description"])

    def test_reference_tracks_existing_setup_roles_without_impossible_mixer_gate(self):
        self.assertIn("qt_env.setup_pdh", PDH_LOCKING_PATTERN)
        self.assertIn("FIR2.OUT", PDH_LOCKING_PATTERN)
        self.assertIn("FIRF.OUT", PDH_LOCKING_PATTERN)
        self.assertIn("ACC2.PAUSE(port 3)", PDH_LOCKING_PATTERN)
        self.assertIn("LTRN", PDH_LOCKING_PATTERN)
        self.assertIn("not a verified physical wiring", PDH_LOCKING_PATTERN)
        self.assertNotIn("→ MIXR.IN_B gating", PDH_LOCKING_PATTERN)
        self.assertNotIn("→ ACCM.RESET", PDH_LOCKING_PATTERN)


if __name__ == "__main__":
    unittest.main()
