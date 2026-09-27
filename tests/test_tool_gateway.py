"""The Agent may propose tools, but Qt and the operator own execution."""

import json
import threading
import time
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests.qt_test_support import ensure_app
from PySide6.QtCore import QSettings, QThread

from tool_gateway import ToolGateway


class FakeNode:
    name = "ACCM"
    component_name = "累加器"

    def __init__(self):
        self.values = {"freq": 1000.0, "ratio": 1}

    def param_schema(self):
        return [
            {"key": "freq", "type": "float", "min": 0, "max": 1e9},
            {"key": "ratio", "type": "int", "min": 1, "max": 32768},
        ]

    def get_params(self):
        return dict(self.values)


class FakeBridge:
    def __init__(self):
        self.online = False
        self.node = FakeNode()
        self.errors = []
        self._mw = SimpleNamespace(
            port_ctrl=SimpleNamespace(is_open=lambda: self.online),
            _report_error=self.errors.append,
        )

    def _find_node(self, name):
        return self.node if name == "ACCM" else None


class FakeExecutor:
    def __init__(self, bridge):
        self.bridge = bridge
        self.calls = []
        self.threads = []
        self.fail_by_report = False

    def dispatch(self, name, args):
        self.calls.append((name, args))
        self.threads.append(QThread.currentThread())
        if self.fail_by_report:
            self.bridge._mw._report_error("[param] failed ACCM: transport failed")
        elif name == "set_parameter":
            self.bridge.node.values.update(args["params"])
        return json.dumps({"success": True, "detail": "executor result"})


class ToolGatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.bridge = FakeBridge()
        self.executor = FakeExecutor(self.bridge)
        self.gateway = ToolGateway(self.executor, self.bridge)
        self.workers = []

    def tearDown(self):
        self.gateway.shutdown()
        for worker in self.workers:
            worker.join(1)
            self.assertFalse(worker.is_alive())
        self.app.processEvents()

    def start_call(self, name, args, **kwargs):
        results = []
        worker = threading.Thread(target=lambda: results.append(json.loads(
            self.gateway.dispatch(name, args, **kwargs)
        )))
        self.workers.append(worker)
        worker.start()
        return results, worker

    def wait_until(self, predicate):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return True
            time.sleep(0.005)
        return bool(predicate())

    def test_worker_read_runs_on_gui_thread_and_keeps_correlation(self):
        results, _ = self.start_call("list_modules", {}, run_id="run1", call_id="call1")
        self.assertTrue(self.wait_until(lambda: results))
        self.assertEqual(self.executor.threads, [self.app.thread()])
        self.assertEqual(results[0]["status"], "read_only")
        self.assertEqual(results[0]["run_id"], "run1")
        self.assertEqual(results[0]["call_id"], "call1")
        self.assertEqual(results[0]["result"]["detail"], "executor result")

    def test_gui_thread_non_approval_call_is_direct(self):
        result = json.loads(self.gateway.dispatch("list_modules", {}))
        self.assertEqual(result["status"], "read_only")

    def test_offline_parameter_update_is_local_staged(self):
        result = json.loads(self.gateway.dispatch("set_parameter", {
            "node_name": "ACCM", "params": {"freq": 2000},
        }))
        self.assertEqual(result["status"], "local_staged")
        self.assertFalse(result["readback_verified"])
        self.assertEqual(self.bridge.node.values["freq"], 2000)

    def test_online_parameter_update_requires_real_approval(self):
        self.bridge.online = True
        approvals = []
        self.gateway.approval_requested.connect(lambda *args: approvals.append(args))
        results, _ = self.start_call("set_parameter", {
            "node_name": "ACCM", "params": {"freq": 2000},
        })
        self.assertTrue(self.wait_until(lambda: approvals))
        self.assertEqual(self.executor.calls, [])
        self.gateway.resolve_approval(approvals[0][0], True)
        self.assertTrue(self.wait_until(lambda: results))
        self.assertEqual(results[0]["status"], "hardware_unverified")
        self.assertFalse(results[0]["readback_verified"])

    def test_confirm_true_does_not_authorize_clear(self):
        approvals = []
        self.gateway.approval_requested.connect(lambda *args: approvals.append(args))
        results, _ = self.start_call("clear_canvas", {"confirm": True})
        self.assertTrue(self.wait_until(lambda: approvals))
        self.assertEqual(self.executor.calls, [])
        self.gateway.resolve_approval(approvals[0][0], False)
        self.assertTrue(self.wait_until(lambda: results))
        self.assertEqual(results[0]["status"], "denied")
        self.assertEqual(self.executor.calls, [])

    def test_cancel_approval_never_executes_even_after_late_allow(self):
        cancel = threading.Event()
        approvals = []
        self.gateway.approval_requested.connect(lambda *args: approvals.append(args))
        results, worker = self.start_call("clear_canvas", {"confirm": True},
                                          cancel_event=cancel, run_id="old")
        self.assertTrue(self.wait_until(lambda: approvals))
        cancel.set()
        worker.join(1)  # no main-thread event processing needed to cancel
        self.assertFalse(worker.is_alive())
        self.gateway.resolve_approval(approvals[0][0], True)
        self.assertEqual(results[0]["status"], "cancelled")
        self.assertEqual(self.executor.calls, [])

    def test_cancel_run_before_gui_dispatch_invalidates_late_queue(self):
        results, worker = self.start_call("list_modules", {}, run_id="old")
        self.gateway.cancel_pending("old")
        worker.join(1)
        self.app.processEvents()
        self.assertEqual(results[0]["status"], "cancelled")
        self.assertEqual(self.executor.calls, [])
        again = json.loads(self.gateway.dispatch("list_modules", {}, run_id="old"))
        self.assertEqual(again["status"], "cancelled")

    def test_unknown_fields_types_nonfinite_and_out_of_range_do_not_dispatch(self):
        bad = [
            ("list_modules", {"shell": "ignored?"}),
            ("list_modules", {"scope": "invalid"}),
            ("connect_modules", {"source_node": "A", "source_port": True,
                                 "destination_node": "B", "destination_port": 0}),
            ("set_parameter", {"node_name": "ACCM", "params": {"freq": float("nan")}}),
            ("set_parameter", {"node_name": "ACCM", "params": {"freq": "1MHz"}}),
            ("set_parameter", {"node_name": "ACCM", "params": {"freq": -1}}),
            ("set_parameter", {"node_name": "ACCM", "params": {"ratio": 1.5}}),
            ("set_parameter", {"node_name": "ACCM", "params": {"__special_method__": "write"}}),
        ]
        for name, args in bad:
            with self.subTest(name=name, args=args):
                result = json.loads(self.gateway.dispatch(name, args))
                self.assertEqual(result["status"], "failed")
        denied = json.loads(self.gateway.dispatch("Shell", {"command": "echo bad"}))
        self.assertEqual(denied["status"], "denied")
        self.assertEqual(self.executor.calls, [])

    def test_target_replaced_while_approval_pending_invalidates_permission(self):
        self.bridge.online = True
        approvals = []
        self.gateway.approval_requested.connect(lambda *args: approvals.append(args))
        results, _ = self.start_call("set_parameter", {
            "node_name": "ACCM", "params": {"freq": 2000},
        })
        self.assertTrue(self.wait_until(lambda: approvals))
        self.bridge.node = FakeNode()
        self.gateway.resolve_approval(approvals[0][0], True)
        self.assertTrue(self.wait_until(lambda: results))
        self.assertEqual(results[0]["status"], "denied")
        self.assertEqual(self.executor.calls, [])

    def test_swallowed_transport_error_cannot_be_reported_as_success(self):
        self.bridge.online = True
        self.executor.fail_by_report = True
        self.gateway.approval_requested.connect(
            lambda request_id, *_: self.gateway.resolve_approval(request_id, True)
        )
        results, _ = self.start_call("set_parameter", {
            "node_name": "ACCM", "params": {"freq": 2000},
        })
        self.assertTrue(self.wait_until(lambda: results))
        self.assertEqual(results[0]["status"], "failed")
        self.assertFalse(results[0]["success"])
        self.assertFalse(results[0]["readback_verified"])

    def test_generate_rejects_path_and_template_injection_before_approval(self):
        spec = {"module_name": "new_filter", "display_name": "新滤波器",
                "description": "Filter", "inputs": [], "outputs": []}
        for field, value in (("module_name", "../../escape"),
                             ("display_name", 'bad"; import os'),
                             ("display_name", '{__import__("os")}')):
            with self.subTest(field=field, value=value):
                result = json.loads(self.gateway.dispatch("generate_module", {**spec, field: value}))
                self.assertEqual(result["status"], "failed")
        self.assertEqual(self.executor.calls, [])

    def test_unknown_transport_requires_approval(self):
        self.bridge._mw.port_ctrl = None
        approvals = []
        self.gateway.approval_requested.connect(lambda *args: approvals.append(args))
        results, _ = self.start_call("set_parameter", {
            "node_name": "ACCM", "params": {"freq": 2000},
        })
        self.assertTrue(self.wait_until(lambda: approvals))
        self.assertEqual(approvals[0][2]["transport_state"], "unknown")
        self.assertEqual(self.executor.calls, [])
        self.gateway.resolve_approval(approvals[0][0], False)
        self.assertTrue(self.wait_until(lambda: results))
        self.assertEqual(results[0]["status"], "denied")

    def test_schema_is_rechecked_after_approval(self):
        self.bridge.online = True
        approvals = []
        self.gateway.approval_requested.connect(lambda *args: approvals.append(args))
        results, _ = self.start_call("set_parameter", {
            "node_name": "ACCM", "params": {"freq": 2000},
        })
        self.assertTrue(self.wait_until(lambda: approvals))
        self.bridge.node.param_schema = lambda: []
        self.gateway.resolve_approval(approvals[0][0], True)
        self.assertTrue(self.wait_until(lambda: results))
        self.assertEqual(results[0]["status"], "failed")
        self.assertEqual(self.executor.calls, [])

    def test_shutdown_wakes_worker_without_gui_pump(self):
        results, worker = self.start_call("list_modules", {}, run_id="shutdown")
        self.gateway.shutdown()
        worker.join(1)
        self.assertFalse(worker.is_alive())
        self.app.processEvents()
        self.assertEqual(results[0]["status"], "cancelled")
        self.assertEqual(self.executor.calls, [])

    def test_cancel_after_execution_started_preserves_atomic_receipt(self):
        cancel = threading.Event()
        original = self.executor.dispatch

        def execute_then_cancel(name, args):
            result = original(name, args)
            cancel.set()
            self.gateway.cancel_pending("active")
            return result

        self.executor.dispatch = execute_then_cancel
        result = json.loads(self.gateway.dispatch("set_parameter", {
            "node_name": "ACCM", "params": {"freq": 3000},
        }, run_id="active", cancel_event=cancel))
        self.assertEqual(result["status"], "local_staged")
        self.assertEqual(self.bridge.node.values["freq"], 3000)
        again = json.loads(self.gateway.dispatch("list_modules", {}, run_id="active"))
        self.assertEqual(again["status"], "cancelled")

    def test_direct_gui_call_cannot_wait_on_operator_approval(self):
        before = time.monotonic()
        result = json.loads(self.gateway.dispatch("clear_canvas", {"confirm": True}))
        self.assertLess(time.monotonic() - before, 0.2)
        self.assertEqual(result["status"], "denied")
        self.assertEqual(self.executor.calls, [])

    def test_offline_node_removal_still_requires_approval(self):
        approvals = []
        self.gateway.approval_requested.connect(lambda *args: approvals.append(args))
        results, _ = self.start_call("disconnect_module", {"node_name": "ACCM"})
        self.assertTrue(self.wait_until(lambda: approvals))
        self.assertEqual(self.executor.calls, [])
        self.gateway.resolve_approval(approvals[0][0], True)
        self.assertTrue(self.wait_until(lambda: results))
        self.assertEqual(results[0]["status"], "local_staged")


class ToolGatewayQtIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        from canvas_bridge import CanvasBridge
        from qt_ui_mainwindow import MainWindow
        from tool_executor import ToolExecutor
        self.temp = tempfile.TemporaryDirectory()
        self.window = MainWindow(
            settings=QSettings(f"{self.temp.name}/settings.ini", QSettings.IniFormat),
            custom_composite_path=f"{self.temp.name}/composites.json",
            experiment_repository_path=f"{self.temp.name}/experiments",
        )
        self.bridge = CanvasBridge(self.window)
        self.gateway = ToolGateway(ToolExecutor(self.bridge, None), self.bridge)

    def tearDown(self):
        self.gateway.shutdown()
        self.window.close()
        self.app.processEvents()
        self.temp.cleanup()

    def test_module_info_uses_authoritative_current_mode_accumulator_schema(self):
        from qt_module_schema import ACCM_SCHEMA
        result = json.loads(self.gateway.dispatch("get_module_info", {"module_type": "累加器"}))
        self.assertEqual(result["status"], "read_only")
        self.assertEqual(result["available_mode"], "free")
        fields = {item["key"]: item for item in result["parameter_schema"]}
        expected = {item["key"]: item for item in ACCM_SCHEMA if item.get("free", True)}
        self.assertEqual(set(fields), set(expected))
        self.assertEqual(fields["freq"]["max"], expected["freq"]["max"])
        self.assertEqual(fields["freq"]["min"], 0)
        self.assertEqual(fields["freq"]["unit"], "Hz")
        self.assertIn("reference", result["legacy_parameter_note"])
        self.assertIn("direct_params", result)
        self.window.mode_combo.setCurrentText("Developer Mode")
        developer = json.loads(self.gateway.dispatch("get_module_info", {"module_type": "累加器"}))
        self.assertEqual(developer["available_mode"], "developer")
        self.assertEqual({item["key"] for item in developer["parameter_schema"]},
                         {item["key"] for item in ACCM_SCHEMA})

    def test_pdh_info_exposes_raw_units_and_safe_writable_limits(self):
        from qt_module_schema import PDH_SCHEMA
        result = json.loads(self.gateway.dispatch("get_module_info", {"module_type": "PDH状态机"}))
        fields = {item["key"]: item for item in result["parameter_schema"]}
        self.assertEqual(set(fields), {item["key"] for item in PDH_SCHEMA})
        self.assertEqual(fields["time_scan"]["unit"], "clk")
        self.assertEqual(fields["time_scan"]["max"], 2**31 - 1)
        self.assertEqual(fields["coef_scan"]["min"], -32768)
        self.assertIn("非实时状态", fields["pc_cmd"]["label"])

    def test_custom_black_box_info_is_readonly_and_does_not_expose_private_mapping(self):
        definition = {
            "name": "实验黑盒", "description": "本地黑盒", "nodes": [],
            "inputs": [{"key": "input_1", "label": "输入", "signals": ["level"]}],
            "outputs": [{"key": "output_1", "label": "输出", "signals": ["phase"]}],
            "parameters": [{"key": "frequency", "label": "频率", "type": "float",
                            "min": 0, "max": 1e9, "unit": "Hz",
                            "mapping": {"node_id": "inner", "target_key": "freq"}}],
        }
        with patch.object(self.window.custom_composite_library, "find_by_name", return_value=definition), \
             patch.object(self.window.port_ctrl, "send_param") as send:
            result = json.loads(self.gateway.dispatch("get_module_info", {"module_type": "实验黑盒"}))
        self.assertEqual(result["status"], "read_only")
        self.assertEqual(result["category"], "custom_composite")
        self.assertEqual(result["inputs"][0]["index"], 0)
        self.assertEqual(result["inputs"][0]["signal"], ["level"])
        self.assertEqual(result["parameter_schema"][0]["key"], "frequency")
        self.assertNotIn("mapping", result["parameter_schema"][0])
        self.assertFalse(send.called)
        self.assertIsNone(self.bridge._find_node("inner"))

    def test_real_offline_parameters_stage_without_touching_transport_or_handler(self):
        original = self.window.scene.param_apply_handler
        with patch.object(self.window.port_ctrl, "send_param") as send:
            created = json.loads(self.gateway.dispatch("create_module", {
                "module_type": "累加器", "params": {"freq": 1500.0, "ratio": 2},
            }))
            self.assertEqual(created["status"], "local_staged")
            node = self.bridge._find_node("ACCM")
            self.assertEqual(node.get_params()["freq"], 1500)
            self.window._open_param_panel(node)
            panel = self.window._param_panels["ACCM@累加器:0"]
            edited = json.loads(self.gateway.dispatch("set_parameter", {
                "node_name": "ACCM", "params": {"freq": 3200.0},
            }))
            self.assertEqual(edited["status"], "local_staged")
            self.assertEqual(node.get_params()["freq"], 3200)
            self.assertEqual(panel._param_widget._committed_values["freq"], 3200)
            self.assertFalse(send.called)
        self.assertEqual(self.window.scene.param_apply_handler, original)
        self.assertIsNone(node._pending_cache_state)

    def test_real_online_swallowed_error_is_failed_and_cache_rolls_back(self):
        self.gateway.dispatch("create_module", {
            "module_type": "累加器", "params": {"freq": 1500.0, "ratio": 2},
        })
        node = self.bridge._find_node("ACCM")
        original = self.window.scene.param_apply_handler
        results = []
        self.gateway.approval_requested.connect(
            lambda request_id, *_: self.gateway.resolve_approval(request_id, True)
        )
        with patch.object(self.window.port_ctrl, "is_open", return_value=True), \
             patch.object(self.window.port_ctrl, "send_param", side_effect=RuntimeError("test transport failure")), \
             patch.object(self.window, "_refresh_node_params_from_device"):
            worker = threading.Thread(target=lambda: results.append(json.loads(
                self.gateway.dispatch("set_parameter", {
                    "node_name": "ACCM", "params": {"freq": 3200.0},
                })
            )))
            worker.start()
            try:
                deadline = time.monotonic() + 2
                while not results and time.monotonic() < deadline:
                    self.app.processEvents()
                    time.sleep(0.005)
                self.assertTrue(results)
                self.assertEqual(results[0]["status"], "failed")
                self.assertIn("test transport failure", str(results[0]["execution_errors"]))
                self.assertEqual(node.get_params()["freq"], 1500)
            finally:
                self.gateway.shutdown()
                worker.join(1)
        self.assertEqual(self.window.scene.param_apply_handler, original)


if __name__ == "__main__":
    unittest.main()
