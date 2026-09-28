"""Regression contracts shared by the native and Harness host boundary."""

import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from tests.qt_test_support import ensure_app
from PySide6.QtCore import QSettings
from agent_core import AgentCore, _AgentWorker
from runtime_agent_core import RuntimeAgentCore, configured_engine


class _Gateway:
    supports_run_context = True

    def __init__(self):
        self.calls = []

    def dispatch(self, name, args, **context):
        self.calls.append((name, args, context))
        return json.dumps({"status": "read_only", "success": True})


class _Model:
    def chat(self, messages, tools, **kwargs):
        if messages[-1]["role"] == "tool":
            return {"content": "查询完成"}
        return {"tool_calls": [{"id": "query-1", "function": {
            "name": "list_modules", "arguments": '{"scope":"on_canvas"}'
        }}]}


class _QtCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def wait_until(self, predicate):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return True
            time.sleep(.005)
        return predicate()


class AgentRuntimeHostTests(_QtCase):
    def test_native_gateway_receives_run_context_and_publishes_real_result(self):
        gateway = _Gateway()
        with patch.object(AgentCore, "_load_system_prompt", return_value="system"):
            agent = AgentCore(_Model(), gateway, None, None, {"agent": {}})
        events, legacy_results, replies = [], [], []
        agent.tool_event.connect(lambda *args: events.append(args))
        agent.tool_executed.connect(lambda *args: legacy_results.append(args))
        agent.response_ready.connect(replies.append)
        try:
            self.assertTrue(agent.send_message("查询模块"))
            self.assertTrue(self.wait_until(lambda: replies))
            self.assertEqual(len(gateway.calls), 1)
            context = gateway.calls[0][2]
            self.assertIsInstance(context["cancel_event"], threading.Event)
            self.assertEqual(context["call_id"], "native:0:0:query-1")
            self.assertTrue(context["run_id"])
            self.assertEqual([event[-1] for event in events], ["running", "read_only"])
            self.assertEqual(events[0][:2], events[1][:2])
            self.assertIn('"success": true', legacy_results[-1][-1])
        finally:
            agent.shutdown(2000)

    def test_readonly_call_does_not_trigger_hidden_layout(self):
        class Bridge:
            calls = 0

            def auto_layout(self):
                self.calls += 1

        gateway = _Gateway()
        bridge = Bridge()
        worker = _AgentWorker(_Model(), [], gateway,
                              [{"role": "user", "content": "query"}], 2, bridge)
        worker.start()
        self.assertTrue(worker.wait(2000))
        self.assertEqual(worker.outcome, "completed")
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(bridge.calls, 0)

    def test_finished_worker_cannot_be_replaced_before_receipts_are_delivered(self):
        with patch.object(AgentCore, "_load_system_prompt", return_value="system"):
            agent = AgentCore(_Model(), _Gateway(), None, None, {"agent": {}})
        responses = []
        agent.response_ready.connect(responses.append)
        try:
            agent.send_message("第一轮")
            self.assertTrue(agent._worker.wait(2000))
            self.assertTrue(agent.is_busy)
            self.assertFalse(agent.send_message("不能吞掉第一轮结果"))
            self.assertFalse(agent.reset_conversation())
            self.assertTrue(self.wait_until(lambda: responses))
            self.assertFalse(agent.is_busy)
            self.assertEqual(len([m for m in agent._messages if m["role"] == "tool"]), 1)
            self.assertTrue(agent.send_message("第二轮"))
            self.assertTrue(self.wait_until(lambda: len(responses) == 2))
        finally:
            agent.shutdown(2000)

    def test_malformed_arguments_never_execute_default_tool(self):
        class Model(_Model):
            def chat(self, messages, tools, **kwargs):
                if messages[-1]["role"] == "tool":
                    return {"content": "bad call rejected"}
                return {"tool_calls": [{"id": "malformed", "function": {
                    "name": "list_modules", "arguments": "{not-json"
                }}]}

        gateway = _Gateway()
        worker = _AgentWorker(Model(), [], gateway,
                              [{"role": "user", "content": "query"}], 2, None)
        worker.start()
        self.assertTrue(worker.wait(2000))
        self.assertEqual(worker.outcome, "completed")
        self.assertEqual(gateway.calls, [])
        self.assertIn("JSON object", worker.messages[-2]["content"])

    def test_reused_provider_call_ids_keep_distinct_receipts_and_cards(self):
        from PySide6.QtCore import QCoreApplication, QEvent
        from agent_chat_widget import AgentChatWidget

        class Model:
            def chat(self, messages, tools, **kwargs):
                completed = sum(message["role"] == "tool" for message in messages)
                if completed == 2:
                    return {"content": "两次查询完成"}
                name, args = (("list_modules", {"scope": "on_canvas"}) if completed == 0
                              else ("get_module_info", {"module_type": "累加器"}))
                return {"tool_calls": [{"id": "call_1", "function": {
                    "name": name, "arguments": json.dumps(args),
                }}]}

        gateway = _Gateway()
        with patch.object(AgentCore, "_load_system_prompt", return_value="system"):
            agent = AgentCore(Model(), gateway, None, None, {"agent": {}})
        chat = AgentChatWidget()
        agent.tool_event.connect(chat.update_tool_call)
        try:
            self.assertTrue(agent.send_message("连续查询两次"))
            self.assertTrue(self.wait_until(lambda: not agent.is_busy))
            host_ids = [context["call_id"] for _, _, context in gateway.calls]
            self.assertEqual(len(set(host_ids)), 2)
            self.assertEqual(len(chat._pending_tool_frames), 2)
            # The provider's own protocol IDs must not be rewritten.
            self.assertEqual([message["tool_call_id"] for message in agent._messages
                              if message["role"] == "tool"], ["call_1", "call_1"])
        finally:
            agent.shutdown(2000)
            chat.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


class _ConfigurationOnlyModel:
    def configuration_snapshot(self):
        return {"endpoint": "http://127.0.0.1:1234/v1/chat/completions",
                "api_key": "test-only", "model": "test-model"}

    def chat(self, *args, **kwargs):
        raise AssertionError("Harness errors must not silently fall back to native")


class HarnessFacadeTests(_QtCase):
    def make_agent(self, factory):
        with patch.object(AgentCore, "_load_system_prompt", return_value="system"):
            return RuntimeAgentCore(_ConfigurationOnlyModel(), _Gateway(), None, None,
                                    {"agent": {}}, runtime_factory=factory)

    def test_harness_default_and_invalid_engines_fail_closed(self):
        self.assertEqual(configured_engine({}), "harness")
        self.assertEqual(configured_engine({"agent": {"engine": "native"}}), "native")
        with self.assertRaises(ValueError):
            configured_engine({"agent": {"engine": "typo"}})

    def test_harness_persists_across_turns_but_resets_on_settings_change(self):
        instances = []

        class Runtime:
            def __init__(self, **kwargs):
                self.closed = False
                self.prompts = []
                instances.append(self)

            def run(self, **kwargs):
                self.prompts.append(kwargs["user_text"])
                kwargs["dispatch"]("list_modules", {"scope": "on_canvas"}, "read-1")
                return "仅查询了本地画布"

            def close(self):
                self.closed = True

        agent = self.make_agent(Runtime)
        responses = []
        agent.response_ready.connect(responses.append)
        try:
            agent.send_message("查询一次")
            self.assertTrue(self.wait_until(lambda: len(responses) == 1))
            agent.send_message("再查询一次")
            self.assertTrue(self.wait_until(lambda: len(responses) == 2))
            self.assertEqual(len(instances), 1)
            self.assertEqual(instances[0].prompts, ["查询一次", "再查询一次"])
            self.assertEqual(len([m for m in agent._messages if m["role"] == "tool"]), 2)
            agent.reconfigure({"agent": {"engine": "native"}})
            self.assertTrue(instances[0].closed)
            self.assertEqual(agent._messages, [])
            self.assertEqual(agent.engine, "native")
        finally:
            agent.shutdown(2000)


    def test_harness_failure_is_visible_and_never_invokes_native(self):
        class Runtime:
            def __init__(self, **kwargs):
                pass

            def run(self, **kwargs):
                raise RuntimeError("runtime unavailable")

            def close(self):
                pass

        agent = self.make_agent(Runtime)
        errors = []
        agent.error_occurred.connect(errors.append)
        try:
            agent.send_message("查询")
            self.assertTrue(self.wait_until(lambda: errors))
            self.assertIn("runtime unavailable", errors[0])
            self.assertNotIn("silently fall back", errors[0])
        finally:
            agent.shutdown(2000)

    def test_output_limit_is_incomplete_retains_receipts_and_allows_next_turn(self):
        from harness_runtime import HarnessOutputLimit

        for partial in ("", "已检查 PID，后续分析尚未完成"):
            with self.subTest(partial=partial):
                class Runtime:
                    def __init__(self, **kwargs):
                        self.calls = 0

                    def run(self, **kwargs):
                        self.calls += 1
                        if self.calls == 1:
                            kwargs["dispatch"]("list_modules", {}, "read-before-limit")
                            if partial:
                                kwargs["on_text"](partial)
                            raise HarnessOutputLimit(partial_text=partial, max_tokens=4096)
                        return "本轮恢复正常，未重复工具操作"

                    def close(self):
                        pass

                agent = self.make_agent(Runtime)
                notices, errors, replies, cancelled = [], [], [], []
                agent.response_incomplete.connect(notices.append)
                agent.error_occurred.connect(errors.append)
                agent.response_ready.connect(replies.append)
                agent.generation_cancelled.connect(lambda: cancelled.append(True))
                try:
                    self.assertTrue(agent.send_message("查询"))
                    self.assertTrue(self.wait_until(lambda: not agent.is_busy))
                    self.assertEqual(agent._worker.outcome, "incomplete")
                    self.assertEqual(len(notices), 1)
                    self.assertIn("4096", notices[0])
                    self.assertIn("未完成", notices[0])
                    self.assertNotIn("Traceback", notices[0])
                    self.assertEqual(errors, [])
                    self.assertEqual(cancelled, [])
                    self.assertEqual(replies, [partial] if partial else [])
                    self.assertEqual(len(agent._tools.calls), 1)
                    self.assertEqual(len([m for m in agent._messages if m["role"] == "tool"]), 1)
                    self.assertIn("未完成", agent._messages[-1]["content"])
                    self.assertEqual(agent._harness.calls, 1)
                    self.assertTrue(agent.send_message("请继续说明，不要重复已完成操作"))
                    self.assertTrue(self.wait_until(lambda: not agent.is_busy))
                    self.assertEqual(agent._worker.outcome, "completed")
                    self.assertEqual(len(agent._tools.calls), 1)
                    self.assertEqual(len(notices), 1)
                    self.assertIn("恢复正常", replies[-1])
                finally:
                    agent.shutdown(2000)

    def test_runtime_close_error_preserves_history_and_engine(self):
        class Runtime:
            def close(self):
                raise RuntimeError("close failed")

        agent = self.make_agent(None)
        agent._harness = Runtime()
        original = [{"role": "user", "content": "keep history"}]
        agent._messages = list(original)
        with self.assertRaisesRegex(RuntimeError, "close failed"):
            agent.reconfigure({"agent": {"engine": "native"}})
        self.assertEqual(agent.engine, "harness")
        self.assertEqual(agent._messages, original)
        agent._harness = None

    def test_stop_event_cancels_runtime_and_blocks_late_callback(self):
        started = threading.Event()

        class Runtime:
            def __init__(self, **kwargs):
                pass

            def run(self, **kwargs):
                started.set()
                kwargs["cancel_event"].wait(2)
                kwargs["dispatch"]("set_parameter", {"node_name": "ACCM", "params": {}}, "late")
                return "late response"

            def close(self):
                pass

        agent = self.make_agent(Runtime)
        cancelled, responses = [], []
        agent.generation_cancelled.connect(lambda: cancelled.append(True))
        agent.response_ready.connect(responses.append)
        try:
            agent.send_message("开始")
            self.assertTrue(started.wait(1))
            self.assertFalse(agent.reset_conversation())
            with self.assertRaises(RuntimeError):
                agent.reconfigure({"agent": {"engine": "native"}})
            self.assertTrue(agent.stop_generation())
            self.assertTrue(self.wait_until(lambda: cancelled))
            self.assertEqual(agent._tools.calls, [])
            self.assertEqual(responses, [])
        finally:
            agent.shutdown(2000)


class IntegratedSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def test_busy_or_close_failure_does_not_partially_replace_provider(self):
        from FPGA_Agent.main import create_window

        class BrokenRuntime:
            def close(self):
                raise RuntimeError("close failed")

        with tempfile.TemporaryDirectory() as directory:
            config = {"agent": {"engine": "harness"},
                      "llm": {"endpoint": "https://old.example/v1", "model": "old-model"}}
            with patch("secret_store.load_agent_configuration", return_value=(config, "old-key", "")):
                window = create_window(QSettings(str(Path(directory) / "ui.ini"), QSettings.IniFormat))
            parts = window._agent_components
            agent, llm, chat = parts["agent"], parts["llm"], parts["chat"]
            previous = llm.configuration_snapshot()
            payload = {"config": {"agent": {"engine": "native"},
                                   "llm": {"endpoint": "https://new.example/v1", "model": "new-model"}},
                       "api_key": "new-key"}
            try:
                agent._active_turn = True
                chat.settings_saved.emit(payload)
                self.assertEqual(llm.configuration_snapshot(), previous)
                self.assertEqual(agent.engine, "harness")
                agent._active_turn = False
                agent._harness = BrokenRuntime()
                chat.settings_saved.emit(payload)
                self.assertEqual(llm.configuration_snapshot(), previous)
                self.assertEqual(config["llm"]["model"], "old-model")
                self.assertEqual(agent.engine, "harness")
            finally:
                agent._harness = None
                agent._active_turn = False
                parts["gateway"].shutdown()
                agent.shutdown(1000)
                window.close()

    def test_output_budget_is_effective_at_launch_and_after_settings_save(self):
        from FPGA_Agent.main import create_window

        with tempfile.TemporaryDirectory() as directory:
            config = {"agent": {"engine": "harness"}, "llm": {
                "endpoint": "https://example.test/v1", "model": "deepseek-v4-pro"}}
            with patch("secret_store.load_agent_configuration", return_value=(config, "test-key", "")):
                window = create_window(QSettings(str(Path(directory) / "ui.ini"), QSettings.IniFormat))
            parts = window._agent_components
            agent, llm, chat = parts["agent"], parts["llm"], parts["chat"]
            try:
                self.assertEqual(llm.configuration_snapshot()["max_tokens"], 32768)
                for fields, expected, policy in (
                    ({"max_tokens": 8192}, 8192, 8192),
                    ({"model": "gpt-4o"}, 8192, 8192),
                    ({"model": "deepseek-v4-pro", "max_tokens": None}, 32768, None),
                    ({"model": "gpt-4o"}, 4096, None),
                ):
                    chat.settings_saved.emit({"config": {"agent": {"engine": "harness"}, "llm": {
                        "endpoint": "https://example.test/v1", **fields}}, "api_key": "test-key"})
                    self.assertEqual(llm.configuration_snapshot()["max_tokens"], expected)
                    self.assertEqual(config["llm"]["max_tokens"], policy)
                    captured = []
                    agent._runtime_factory = lambda **kwargs: captured.append(kwargs) or object()
                    agent._get_harness()
                    self.assertEqual(captured[0]["max_tokens"], expected)
                    agent._harness = None
                previous = llm.configuration_snapshot()
                chat.settings_saved.emit({"config": {"llm": {"max_tokens": False}}, "api_key": "test-key"})
                self.assertEqual(llm.configuration_snapshot(), previous)
                self.assertIsNone(config["llm"]["max_tokens"])
            finally:
                parts["gateway"].shutdown()
                agent.shutdown(1000)
                window.close()


if __name__ == "__main__":
    unittest.main()
