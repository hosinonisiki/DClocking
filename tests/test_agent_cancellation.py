import io
import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from tests.qt_test_support import ensure_app
from agent_core import AgentCore, _AgentWorker
from llm_client import LLMCancelled, LLMClient


class _NoopExecutor:
    def __init__(self):
        self.calls = []

    def dispatch(self, name, args):
        self.calls.append((name, args))
        return "{}"


class _BlockingLLM:
    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()
        self.cancel_calls = 0

    def chat(self, messages, tools, *, cancel_event, request_id):
        self.started.set()
        while not self.release.wait(0.01):
            if cancel_event.is_set():
                raise LLMCancelled("cancelled")
        return {"content": "不应显示的迟到响应", "tool_calls": None}

    def cancel_request(self, request_id):
        self.cancel_calls += 1
        self.release.set()
        return True


class _FirstCallBlocksLLM:
    def __init__(self):
        self.first_started = threading.Event()
        self.release_first = threading.Event()
        self._lock = threading.Lock()
        self.calls = 0

    def chat(self, messages, tools, *, cancel_event, request_id):
        with self._lock:
            self.calls += 1
            call_number = self.calls
        if call_number == 1:
            self.first_started.set()
            while not self.release_first.wait(0.01):
                if cancel_event.is_set():
                    raise LLMCancelled("cancelled")
            return {"content": "第一轮迟到响应", "tool_calls": None}
        return {"content": "第二轮正常响应", "tool_calls": None}

    def cancel_request(self, request_id):
        return True


class _ToolCallingLLM:
    def chat(self, messages, tools, *, cancel_event, request_id):
        return {
            "content": "",
            "tool_calls": [
                {
                    "id": "call-1",
                    "function": {"name": "first", "arguments": "{}"},
                },
                {
                    "id": "call-2",
                    "function": {"name": "second", "arguments": "{}"},
                },
            ],
        }


class _TransportErrorOnCancelLLM:
    def __init__(self):
        self.started = threading.Event()

    def chat(self, messages, tools, *, cancel_event, request_id):
        self.started.set()
        cancel_event.wait(2)
        raise RuntimeError("socket closed")

    def cancel_request(self, request_id):
        return True


class _BlockingExecutor(_NoopExecutor):
    def __init__(self):
        super().__init__()
        self.first_started = threading.Event()
        self.release_first = threading.Event()

    def dispatch(self, name, args):
        self.calls.append((name, args))
        if name == "first":
            self.first_started.set()
            self.release_first.wait(2)
        return "{}"


class _FakeProcess:
    def __init__(self):
        self.terminated = False

    def poll(self):
        return -15 if self.terminated else None

    def terminate(self):
        self.terminated = True


class _CompletedProcess:
    def __init__(self, output: bytes):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(output)
        self.stderr = io.BytesIO()

    def poll(self):
        return 0

    def wait(self, timeout=None):
        return 0


class AgentCancellationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def _wait_until(self, predicate, timeout=2.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return True
            time.sleep(0.01)
        self.app.processEvents()
        return predicate()

    def test_worker_cancels_promptly_without_emitting_late_response(self):
        llm = _BlockingLLM()
        executor = _NoopExecutor()
        worker = _AgentWorker(
            llm=llm,
            tools_def=[],
            tool_executor=executor,
            messages=[{"role": "user", "content": "开始"}],
            max_iterations=2,
            bridge=None,
        )
        try:
            worker.start()
            self.assertTrue(llm.started.wait(1))
            worker.cancel()
            self.assertTrue(worker.wait(1000))
            self.app.processEvents()

            self.assertEqual(llm.cancel_calls, 1)
            self.assertEqual(worker.outcome, "cancelled")
            self.assertEqual(worker.final_text, "")
            self.assertEqual(executor.calls, [])
        finally:
            llm.release.set()
            worker.wait(1000)

    def test_agent_can_start_new_turn_and_ignores_cancelled_late_result(self):
        llm = _FirstCallBlocksLLM()
        executor = _NoopExecutor()
        with patch.object(AgentCore, "_load_system_prompt", return_value="system"):
            agent = AgentCore(llm, executor, None, None, {"agent": {}})

        responses = []
        cancelled = []
        running_when_cancelled = []
        agent.response_ready.connect(responses.append)
        agent.generation_cancelled.connect(lambda: (
            cancelled.append(True),
            running_when_cancelled.append(agent._worker.isRunning()),
        ))

        try:
            agent.send_message("第一轮")
            self.assertTrue(llm.first_started.wait(1))
            self.assertTrue(agent.stop_generation())
            self.assertTrue(self._wait_until(lambda: cancelled == [True]))
            self.assertEqual(running_when_cancelled, [False])
            self.assertEqual(agent._messages[-1], {
                "role": "user", "content": "第一轮"
            })

            self.assertTrue(agent.send_message("第二轮"))
            self.assertTrue(
                self._wait_until(lambda: responses == ["第二轮正常响应"])
            )

            llm.release_first.set()
            time.sleep(0.05)
            self.app.processEvents()
            self.assertEqual(responses, ["第二轮正常响应"])
        finally:
            llm.release_first.set()
            worker = getattr(agent, "_worker", None)
            if worker is not None:
                worker.wait(1000)

    def test_cancellation_stops_before_the_next_tool_call(self):
        executor = _BlockingExecutor()
        worker = _AgentWorker(
            llm=_ToolCallingLLM(),
            tools_def=[],
            tool_executor=executor,
            messages=[{"role": "user", "content": "执行工具"}],
            max_iterations=2,
            bridge=None,
        )
        try:
            worker.start()
            self.assertTrue(executor.first_started.wait(1))
            self.assertTrue(worker.cancel())
            executor.release_first.set()
            self.assertTrue(worker.wait(1000))
            self.app.processEvents()

            self.assertEqual([name for name, _args in executor.calls], ["first"])
            self.assertEqual(worker.outcome, "cancelled")
            tool_messages = [
                message for message in worker.messages
                if message.get("role") == "tool"
            ]
            self.assertEqual(
                [message["tool_call_id"] for message in tool_messages],
                ["call-1", "call-2"],
            )
            self.assertIn("Cancelled before execution", tool_messages[1]["content"])
        finally:
            executor.release_first.set()
            worker.wait(1000)

    def test_transport_error_after_cancel_is_reported_as_normal_cancellation(self):
        llm = _TransportErrorOnCancelLLM()
        worker = _AgentWorker(
            llm=llm,
            tools_def=[],
            tool_executor=_NoopExecutor(),
            messages=[{"role": "user", "content": "停止"}],
            max_iterations=1,
            bridge=None,
        )
        worker.start()
        self.assertTrue(llm.started.wait(1))
        worker.cancel()
        self.assertTrue(worker.wait(1000))
        self.app.processEvents()

        self.assertEqual(worker.outcome, "cancelled")
        self.assertEqual(worker.error_text, "")

    def test_agent_shutdown_cancels_and_joins_active_worker(self):
        llm = _BlockingLLM()
        with patch.object(AgentCore, "_load_system_prompt", return_value="system"):
            agent = AgentCore(llm, _NoopExecutor(), None, None, {"agent": {}})

        agent.send_message("退出前仍在生成")
        self.assertTrue(llm.started.wait(1))
        self.assertTrue(agent.shutdown(timeout_ms=1000))
        self.assertFalse(agent._worker.isRunning())

    def test_default_shutdown_waits_for_an_atomic_tool_to_finish(self):
        executor = _BlockingExecutor()
        with patch.object(AgentCore, "_load_system_prompt", return_value="system"):
            agent = AgentCore(
                _ToolCallingLLM(), executor, None, None, {"agent": {}}
            )

        agent.send_message("执行后退出")
        self.assertTrue(executor.first_started.wait(1))
        release = threading.Timer(0.05, executor.release_first.set)
        release.start()
        try:
            self.assertTrue(agent.shutdown())
            self.assertFalse(agent._worker.isRunning())
            self.assertEqual(agent._worker.outcome, "cancelled")
        finally:
            executor.release_first.set()
            release.cancel()

    def test_llm_client_reassembles_streamed_content_and_tool_calls(self):
        lines = [
            b'data: {"choices":[{"delta":{"content":"hello "}}]}',
            b'data: {"choices":[{"delta":{"content":"world","tool_calls":[{"index":0,"id":"call-1","type":"function","function":{"name":"set_","arguments":"{\\"x\\":"}}]},"finish_reason":null}]}',
            b'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"name":"parameter","arguments":"1}"}}]},"finish_reason":"tool_calls"}]}',
            b'data: [DONE]',
        ]
        client = LLMClient("https://example.test/v1", "test-key")

        result = client._parse_event_stream(lines, threading.Event())

        self.assertEqual(result["content"], "hello world")
        self.assertEqual(result["tool_calls"][0]["function"], {
            "name": "set_parameter", "arguments": '{"x":1}'
        })
        self.assertEqual(result["finish_reason"], "tool_calls")

    def test_llm_client_rejects_truncated_or_error_streams(self):
        client = LLMClient("https://example.test/v1", "test-key")
        with self.assertRaisesRegex(Exception, "completion marker"):
            client._parse_event_stream([
                b'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call-1","function":{"name":"set_parameter","arguments":"{\\"x\\":"}}]}}]}',
            ], threading.Event())
        with self.assertRaisesRegex(Exception, "provider failed"):
            client._parse_event_stream([
                b'data: {"error":{"message":"provider failed"}}',
                b'data: [DONE]',
            ], threading.Event())

    def test_llm_client_limits_stream_event_count_without_splitlines(self):
        client = LLMClient("https://example.test/v1", "test-key")
        client._MAX_STREAM_LINES = 2

        with self.assertRaisesRegex(Exception, "too many events"):
            client._parse_event_stream([
                b": first",
                b": second",
                b"data: [DONE]",
            ], threading.Event())

    def test_llm_client_cancels_only_the_requested_generation(self):
        client = LLMClient("https://example.test/v1", "test-key")
        first_process = _FakeProcess()
        second_process = _FakeProcess()
        first_event = threading.Event()
        second_event = threading.Event()
        first_id = object()
        second_id = object()
        client._active_requests = {
            first_id: {
                "process": first_process,
                "cancel_event": first_event,
            },
            second_id: {
                "process": second_process,
                "cancel_event": second_event,
            },
        }

        self.assertTrue(client.cancel_request(first_id))
        self.assertTrue(first_event.is_set())
        self.assertTrue(first_process.terminated)
        self.assertFalse(second_event.is_set())
        self.assertFalse(second_process.terminated)

    def test_curl_transport_disables_user_curl_configuration(self):
        stream = (
            b'data: {"choices":[{"delta":{"content":"ok"},'
            b'"finish_reason":"stop"}]}\n\n'
            b'data: [DONE]\n\n'
            b'__DCLOCKING_HTTP_STATUS__:200\n'
        )
        process = _CompletedProcess(stream)
        client = LLMClient("https://example.test/v1", "test-key")

        with patch("llm_client.subprocess.Popen", return_value=process) as popen:
            result = client.chat([{"role": "user", "content": "hello"}])

        self.assertEqual(result["content"], "ok")
        self.assertEqual(
            popen.call_args.args[0],
            [client._curl_binary, "--disable", "--config", "-"],
        )

    def test_curl_transport_enforces_response_limit_with_bounded_reads(self):
        process = _CompletedProcess(b"x" * 512)
        client = LLMClient("https://example.test/v1", "test-key")
        client._MAX_RESPONSE_BYTES = 32

        with self.assertRaisesRegex(Exception, "safety limit"):
            client._read_process_output(process, threading.Event())

    def test_curl_transport_cancels_while_server_withholds_headers(self):
        request_started = threading.Event()

        class SlowHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(content_length)
                request_started.set()
                time.sleep(3)

            def log_message(self, _format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), SlowHandler)
        server.daemon_threads = True
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        client = LLMClient(
            f"http://127.0.0.1:{server.server_port}/v1",
            "test-key",
            timeout=10,
        )
        if not client._curl_binary:
            self.skipTest("curl is unavailable")
        request_id = object()
        cancel_event = threading.Event()
        errors = []

        def call_api():
            try:
                client.chat(
                    [{"role": "user", "content": "wait"}],
                    cancel_event=cancel_event,
                    request_id=request_id,
                )
            except Exception as exc:
                errors.append(exc)

        caller = threading.Thread(target=call_api)
        try:
            caller.start()
            self.assertTrue(request_started.wait(2))
            started_at = time.monotonic()
            self.assertTrue(client.cancel_request(request_id))
            caller.join(2)
            self.assertFalse(caller.is_alive())
            self.assertLess(time.monotonic() - started_at, 2)
            self.assertEqual(len(errors), 1)
            self.assertIsInstance(errors[0], LLMCancelled)
        finally:
            server.shutdown()
            server.server_close()

    def test_curl_transport_round_trip_parses_openai_stream(self):
        received_payloads = []

        class StreamHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(content_length)
                received_payloads.append(body)
                stream = (
                    b'data: {"choices":[{"delta":{"content":"ok"},'
                    b'"finish_reason":"stop"}]}\n\n'
                    b'data: [DONE]\n\n'
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(stream)))
                self.end_headers()
                self.wfile.write(stream)

            def log_message(self, _format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), StreamHandler)
        server.daemon_threads = True
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        client = LLMClient(
            f"http://127.0.0.1:{server.server_port}/v1",
            "test-key",
            timeout=5,
        )
        if not client._curl_binary:
            self.skipTest("curl is unavailable")

        try:
            result = client.chat([{"role": "user", "content": "你好"}])
            payload = json.loads(received_payloads[0].decode("utf-8"))
            self.assertTrue(payload["stream"])
            self.assertEqual(payload["messages"][0]["content"], "你好")
            self.assertEqual(result["content"], "ok")
            self.assertEqual(result["finish_reason"], "stop")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
