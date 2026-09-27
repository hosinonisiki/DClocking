"""Real Harness -> authenticated bridge -> actual Qt canvas, with a local model.

Set DCLOCKING_TEST_HARNESS_RUNTIME=1 to run. For native visual verification use
QT_QPA_PLATFORM=cocoa and DCLOCKING_HARNESS_SCREENSHOTS=/absolute/output/folder.
No saved user configuration, external model, or experimental device is used.
"""

import json
import gc
import os
from pathlib import Path
import queue
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from tests.qt_test_support import ensure_app
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton, QFrame, QTextBrowser
from FPGA_Agent.main import create_window


class _ProgrammedModel:
    """Deterministic SSE responses exercise the real SDK, not a fake SDK."""

    def __init__(self):
        self.steps = queue.Queue()
        self.requests = []
        self.waiting = threading.Event()
        self.release = threading.Event()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                owner.requests.append(body)
                try:
                    step = owner.steps.get_nowait()
                except queue.Empty:
                    self.send_error(500, "No scripted response; unexpected retry")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                if step == "wait":
                    owner.waiting.set()
                    owner.release.wait(30)
                    return
                if isinstance(step, tuple):
                    name, args = step
                    delta = {"role": "assistant", "tool_calls": [{
                        "index": 0, "id": "call-" + str(len(owner.requests)),
                        "type": "function", "function": {
                            "name": name, "arguments": json.dumps(args, ensure_ascii=False),
                        },
                    }]}
                    reason = "tool_calls"
                else:
                    delta, reason = {"role": "assistant", "content": step}, "stop"
                for event in ({"delta": delta, "finish_reason": None},
                              {"delta": {}, "finish_reason": reason}):
                    event["index"] = 0
                    payload = {"id": "qt-e2e", "model": "deepseek-chat",
                               "object": "chat.completion.chunk", "choices": [event]}
                    self.wfile.write(("data: " + json.dumps(payload) + "\n\n").encode())
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={"poll_interval": .05}, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1"

    def plan(self, *steps):
        for step in steps:
            self.steps.put(step)

    def close(self):
        self.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(1)


@unittest.skipUnless(os.environ.get("DCLOCKING_TEST_HARNESS_RUNTIME") == "1",
                     "opt in to installed real Harness Qt E2E")
class HarnessQtEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        # Earlier Qt fixtures can leave closed dialogs in Python cycles. Drain
        # them on their owning thread before SDK imports allocate on a worker.
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        gc.collect()
        self.storage = tempfile.TemporaryDirectory(prefix="dclocking-harness-qt-")
        self.provider = _ProgrammedModel()
        config = {"agent": {"engine": "harness", "run_timeout_seconds": 30},
                  "llm": {"endpoint": self.provider.url, "model": "deepseek-chat"}}
        settings = QSettings(str(Path(self.storage.name) / "ui.ini"), QSettings.IniFormat)
        with patch("secret_store.load_agent_configuration", return_value=(config, "local-only-key", "")):
            self.window = create_window(settings=settings)
        parts = self.window._agent_components
        self.chat, self.agent, self.bridge = parts["chat"], parts["agent"], parts["bridge"]
        self.gateway = parts["gateway"]
        self.receipts, self.errors = [], []
        self.gateway.audit_recorded.connect(self.receipts.append)
        self.agent.error_occurred.connect(self.errors.append)
        self.window.resize(1440, 900)
        self.window.show()
        self.chat.show()
        self.window.resizeDocks([self.chat], [460], Qt.Horizontal)
        self.app.processEvents()
        self.chat.clear_chat()

    def tearDown(self):
        self.gateway.shutdown()
        self.agent.shutdown(6000)
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        self.provider.close()
        self.storage.cleanup()
        gc.collect()

    def wait_until(self, predicate, timeout=25):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return
            QTest.qWait(10)
        self.fail(f"Qt E2E timed out; errors={self.errors!r}")

    def send(self, text):
        self.chat._input.setPlainText(text)
        QTest.keyClick(self.chat._input, Qt.Key_Return)
        self.assertTrue(self.agent.is_busy)

    def capture(self, name):
        directory = os.environ.get("DCLOCKING_HARNESS_SCREENSHOTS")
        if directory:
            target = Path(directory)
            target.mkdir(parents=True, exist_ok=True)
            QTest.qWait(150)
            self.assertTrue(self.window.grab().save(str(target / f"{name}.png")))

    def pending_approval(self):
        return next((frame for frame in self.chat.findChildren(QFrame, "tool_approval_frame")
                     if frame.property("approval_pending")), None)

    def test_actual_runtime_canvas_approval_cancel_and_next_turn(self):
        self.provider.plan(
            ("create_module", {"module_type": "累加器", "position_x": 250, "position_y": 160}),
            ("set_parameter", {"node_name": "ACCM", "params": {"freq": 3200.0}}),
            "累加器频率已在本地配置为 3200 Hz；未写入或验证实验硬件。",
        )
        self.send("离线创建一个累加器，并把频率设为 3200 Hz")
        self.wait_until(lambda: not self.agent.is_busy)
        self.assertFalse(self.errors)
        node = self.bridge._find_node("ACCM")
        self.assertIsNotNone(node)
        self.assertEqual(node.get_params()["freq"], 3200.0)
        # The main canvas has a large scene; explicitly bring the created node
        # into the viewport for real visual inspection, not an empty screenshot.
        for view in node.scene().views():
            view.centerOn(node)
        self.assertEqual([receipt["status"] for receipt in self.receipts], ["local_staged", "local_staged"])
        self.assertEqual(len(self.chat._pending_tool_frames), 2)
        self.capture("01-harness-offline-parameter")

        self.provider.plan(("clear_canvas", {"confirm": True}), "用户已拒绝清空；画布保持不变。")
        self.send("清空画布")
        self.wait_until(lambda: self.pending_approval() is not None)
        viewport = self.chat._scroll.viewport()
        buttons = [self.pending_approval().findChild(QPushButton, name)
                   for name in ("approval_allow_once", "approval_deny")]
        self.wait_until(lambda: all(
            0 <= button.mapTo(viewport, QPoint(0, 0)).y()
            and button.mapTo(viewport, QPoint(0, button.height())).y() <= viewport.height()
            for button in buttons
        ))
        self.capture("02-harness-approval")
        QTest.mouseClick(self.pending_approval().findChild(QPushButton, "approval_deny"), Qt.LeftButton)
        self.wait_until(lambda: not self.agent.is_busy)
        self.assertIsNotNone(self.bridge._find_node("ACCM"))
        self.assertEqual(self.receipts[-1]["status"], "denied")

        # Cancelling approval is nonmodal, rejects the pending write, and the
        # run's process remains usable for a later model request.
        self.provider.plan(("clear_canvas", {"confirm": True}))
        self.send("再次提出清空请求，然后停止")
        self.wait_until(lambda: self.pending_approval() is not None)
        QTest.mouseClick(self.chat._send_btn, Qt.LeftButton)
        self.wait_until(lambda: not self.agent.is_busy)
        self.assertIsNotNone(self.bridge._find_node("ACCM"))
        self.assertEqual(self.chat._send_btn.text(), "↑")

        self.provider.plan("wait")
        self.send("等待模型输出，然后停止")
        self.wait_until(self.provider.waiting.is_set)
        QTest.mouseClick(self.chat._send_btn, Qt.LeftButton)
        self.wait_until(lambda: not self.agent.is_busy, timeout=8)
        self.provider.release.set()
        self.assertEqual(self.chat._send_btn.text(), "↑")

        self.provider.plan(("list_modules", {"scope": "on_canvas"}), "已重新查询，累加器仍在本地画布。")
        self.send("停止后重新查询模块")
        self.wait_until(lambda: not self.agent.is_busy)
        self.assertFalse(self.errors)
        self.assertEqual(self.receipts[-1]["status"], "read_only")
        self.assertEqual(self.bridge._find_node("ACCM").get_params()["freq"], 3200.0)
        self.capture("03-harness-recovered")
        self.assertTrue(any("重新查询" in widget.toPlainText()
                            for widget in self.chat.findChildren(QTextBrowser)))

        self.provider.plan(("clear_canvas", {"confirm": True}), "已按本次授权清空本地画布。")
        self.send("确认清空测试画布")
        self.wait_until(lambda: self.pending_approval() is not None)
        QTest.mouseClick(self.pending_approval().findChild(QPushButton, "approval_allow_once"), Qt.LeftButton)
        self.wait_until(lambda: not self.agent.is_busy)
        self.assertIsNone(self.bridge._find_node("ACCM"))
        self.assertEqual(self.receipts[-1]["status"], "local_staged")

    def test_deadline_cancels_pending_approval_and_is_not_user_cancellation(self):
        # Exercise an execution deadline, not platform-dependent cold startup
        # time for the bundled Windows/macOS runtime.
        self.provider.plan("本地测试运行时已就绪")
        self.send("初始化测试运行时")
        self.wait_until(lambda: not self.agent.is_busy)
        self.assertFalse(self.errors)
        self.agent._harness.timeout_seconds = 5
        cancelled = []
        self.agent.generation_cancelled.connect(lambda: cancelled.append(True))
        self.provider.plan(("clear_canvas", {"confirm": True}))
        self.send("让确认请求自然超时")
        self.wait_until(lambda: self.pending_approval() is not None)
        self.wait_until(lambda: not self.agent.is_busy, timeout=10)
        self.assertTrue(self.errors)
        self.assertIn("超时", self.errors[-1])
        self.assertEqual(cancelled, [])
        self.assertIsNone(self.pending_approval())
        self.assertEqual(self.receipts[-1]["status"], "cancelled")

    def test_shutdown_wakes_approval_wait_without_gui_event_pump(self):
        self.provider.plan(("clear_canvas", {"confirm": True}))
        self.send("等待确认时关闭")
        self.wait_until(lambda: self.pending_approval() is not None)
        start = time.monotonic()
        self.gateway.shutdown()
        self.assertTrue(self.agent.shutdown(6000))
        self.assertLess(time.monotonic() - start, 6)
        self.assertFalse(self.agent._worker.isRunning())
        self.assertIsNone(self.agent._harness)


if __name__ == "__main__":
    unittest.main()
