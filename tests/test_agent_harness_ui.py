"""Offline UI contracts for the explicitly selected Agent runtime."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from tests.qt_test_support import ensure_app
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QComboBox, QDialog, QFrame, QLabel, QPushButton, QTextBrowser

from agent_chat_widget import AgentChatWidget
from secret_store import load_agent_configuration, save_agent_settings


class HarnessChatUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.chat = AgentChatWidget()
        self.chat.resize(420, 700)
        self.chat.show()
        self.app.processEvents()

    def tearDown(self):
        self.chat.set_thinking(False)
        self.chat.close()
        self.chat.deleteLater()
        self.app.processEvents()

    def test_runtime_status_never_implicitly_changes_engine(self):
        self.chat.set_runtime_status("harness", "运行时不可用，请安装依赖")
        label = self.chat.findChild(QLabel, "agent_runtime_status")
        self.assertIn("Harness", label.text())
        self.assertIn("不可用", label.text())
        self.chat.set_runtime_status("native")
        self.assertIn("Native", label.text())

    def test_stream_chunks_and_final_share_one_bubble_after_thinking_stops(self):
        self.chat.set_thinking(True)
        self.chat.append_assistant_delta("run", "正在")
        self.chat.append_assistant_delta("run", "分析 <b>PID</b>")
        bubbles = self.chat.findChildren(QTextBrowser)
        self.assertEqual(len(bubbles), 1)
        self.assertEqual(bubbles[0].toPlainText(), "正在分析 <b>PID</b>")
        self.chat.set_thinking(False)
        self.chat.finish_assistant_message("**分析完成**")
        self.assertEqual(len(self.chat.findChildren(QTextBrowser)), 1)
        self.assertEqual(bubbles[0].toPlainText(), "分析完成")

    def test_stop_preserves_partial_and_next_run_never_appends_to_it(self):
        self.chat.set_thinking(True)
        self.chat.append_assistant_delta("old", "保留的部分内容")
        self.chat._send_btn.click()
        self.chat.append_assistant_delta("old", "停止后的迟到内容")
        self.chat.set_thinking(False)
        self.chat.append_assistant_delta("old", "结束后的迟到内容")
        self.chat.set_thinking(True)
        self.chat.append_assistant_delta("old", "跨轮迟到内容")
        self.chat.append_assistant_delta("new", "第二轮内容")
        self.chat.append_assistant_delta("old", "错误轮次内容")
        bubbles = self.chat.findChildren(QTextBrowser)
        self.assertEqual([bubble.toPlainText() for bubble in bubbles], ["保留的部分内容", "第二轮内容"])

    def test_nonstreaming_final_message_still_creates_a_bubble(self):
        self.chat.finish_assistant_message("只有最终回复")
        self.assertEqual(self.chat.findChild(QTextBrowser).toPlainText(), "只有最终回复")

    def test_stream_display_is_bounded_and_clear_chat_drops_stream_pointer(self):
        self.chat.set_thinking(True)
        self.chat.append_assistant_delta("old", "x" * (512 * 1024 + 100))
        bubble = self.chat.findChild(QTextBrowser)
        self.assertLess(len(bubble.toPlainText()), 512 * 1024 + 100)
        self.assertIn("截断", bubble.toPlainText())
        self.chat.append_assistant_delta("old", "y" * 1000)
        self.assertNotIn("y", bubble.toPlainText())
        self.chat.clear_chat()
        self.chat.append_assistant_delta("old", "不能恢复已清除的内容")
        self.assertEqual(self.chat._msg_layout.count(), 1)

    def test_tool_lifecycle_updates_one_correlated_card(self):
        self.chat.update_tool_call("run-1", "call-1", "set_parameter", '{"hz":1}', "", "running")
        self.chat.update_tool_call("run-1", "call-1", "set_parameter", '{"hz":1}', '{"status":"offline_updated"}', "completed")
        cards = self.chat.findChildren(QFrame, "tool_call_frame")
        self.assertEqual(len(cards), 1)
        toggle = cards[0].findChild(QPushButton, "tool_toggle")
        self.assertIn("完成", toggle.text())
        toggle.click()
        result = cards[0].findChild(QLabel, "tool_result")
        self.assertIn("offline_updated", result.text())
        self.assertFalse(result.isHidden())

    def test_same_tool_name_and_call_id_in_different_runs_do_not_collide(self):
        for run_id in ("first", "second"):
            self.chat.update_tool_call(run_id, "call-1", "list_modules", "{}", "{}", "completed")
        self.assertEqual(len(self.chat.findChildren(QFrame, "tool_call_frame")), 2)

    def test_legacy_add_tool_call_still_adds_independent_cards(self):
        for _ in range(2):
            self.chat.add_tool_call("list_modules", "{}", "{}")
        self.assertEqual(len(self.chat.findChildren(QFrame, "tool_call_frame")), 2)

    def test_gateway_receipts_distinguish_hardware_from_local_state(self):
        for status, label in (
            ("read_only", "只读查询"),
            ("local_staged", "本地配置已更新"),
            ("hardware_unverified", "硬件状态未验证"),
        ):
            with self.subTest(status=status):
                self.chat.update_tool_call("run", "call", "set_parameter", "{}", "{}", status)
                toggle = self.chat.findChild(QPushButton, "tool_toggle")
                self.assertIn(label, toggle.text())
                self.assertNotIn("完成", toggle.text())

    def test_provider_error_text_is_not_rendered_as_html(self):
        self.chat.add_system_message('<b>provider failure</b> <img src="https://invalid.test/pixel">')
        label = self.chat._msg_layout.itemAt(0).widget()
        self.assertEqual(label.textFormat(), Qt.PlainText)
        self.assertIn("<b>", label.text())

    def test_approval_is_nonmodal_plain_text_and_one_shot(self):
        resolved = []
        self.chat.approval_resolved.connect(lambda key, allowed: resolved.append((key, allowed)))
        with patch.object(QDialog, "exec", side_effect=AssertionError("modal approval")):
            self.chat.show_tool_approval("request-1", "确认写入硬件？", {"arguments": {"module": "<b>PID</b>"}})
        card = self.chat.findChild(QFrame, "tool_approval_frame")
        detail = card.findChild(QLabel, "approval_detail")
        self.assertEqual(detail.textFormat(), Qt.PlainText)
        self.assertIn("<b>PID</b>", detail.text())
        allow = card.findChild(QPushButton, "approval_allow_once")
        deny = card.findChild(QPushButton, "approval_deny")
        allow.click()
        deny.click()
        allow.click()
        self.assertEqual(resolved, [("request-1", True)])
        self.assertFalse(allow.isEnabled())
        self.assertFalse(deny.isEnabled())

    def test_approval_identifiers_are_debug_metadata_not_visible_json(self):
        self.chat.show_tool_approval("request", "确认操作", {
            "tool": "clear_canvas", "arguments": {"confirm": True},
            "run_id": "run-technical", "call_id": "call-technical",
            "transport_state": "offline", "warning": "不会自动撤销",
        })
        card = self.chat.findChild(QFrame, "tool_approval_frame")
        text = card.findChild(QLabel, "approval_detail").text()
        self.assertNotIn("technical", text)
        self.assertNotIn("run_id", text)
        self.assertIn("clear_canvas", text)
        self.assertIn("offline", text)
        self.assertEqual(card.property("run_id"), "run-technical")
        self.assertEqual(card.property("call_id"), "call-technical")
        self.assertIn("call-technical", card.toolTip())

    def test_narrow_dock_keeps_approval_tools_and_bubbles_inside_viewport(self):
        self.chat.resize(320, 700)
        self.chat.add_assistant_message("内容随宽度调整。" * 8)
        self.chat.add_user_message("用户输入 " + "x" * 150)
        self.chat.update_tool_call("run", "call", "very_long_tool_name_" * 5, '{"name":"' + "a" * 200 + '"}', "{}", "hardware_unverified")
        self.chat.findChild(QPushButton, "tool_toggle").click()
        self.chat.show_tool_approval("request", "允许 Agent 执行此画布或硬件操作？", {
            "tool": "clear_canvas", "arguments": {"confirm": True},
            "run_id": "r" * 200, "call_id": "c" * 200,
            "transport_state": "offline", "warning": "停止不会撤销已执行的操作。",
        })
        for _ in range(5):
            self.app.processEvents()
        viewport = self.chat._scroll.viewport()
        self.assertLessEqual(self.chat._msg_container.width(), viewport.width())
        for widget in (
            *self.chat.findChildren(QFrame, "tool_approval_frame"),
            *self.chat.findChildren(QFrame, "tool_call_frame"),
            *self.chat.findChildren(QTextBrowser),
        ):
            with self.subTest(widget=widget.objectName() or "bubble"):
                right = widget.mapTo(viewport, QPoint(widget.width(), 0)).x()
                self.assertLessEqual(right, viewport.width())

    def test_new_approval_actions_are_revealed_after_history_layout_settles(self):
        self.chat.resize(340, 600)
        for index in range(12):
            self.chat.add_assistant_message(f"历史消息 {index}。" * 15)
        self.chat.show_tool_approval("new-approval", "允许执行本次操作？", {
            "tool": "clear_canvas", "arguments": {"confirm": True},
            "transport_state": "offline", "warning": "停止不会撤销已执行的操作。" * 5,
        })
        for _ in range(8):
            self.app.processEvents()
        viewport = self.chat._scroll.viewport()
        for name in ("approval_allow_once", "approval_deny"):
            button = self.chat.findChild(QPushButton, name)
            with self.subTest(button=name):
                top = button.mapTo(viewport, QPoint(0, 0)).y()
                bottom = button.mapTo(viewport, QPoint(0, button.height())).y()
                self.assertGreaterEqual(top, 0)
                self.assertLessEqual(bottom, viewport.height())

    def test_approval_denial_and_repeated_request_are_not_reopened(self):
        resolved = []
        self.chat.approval_resolved.connect(lambda key, allowed: resolved.append((key, allowed)))
        self.chat.show_tool_approval("request-1", "清空画布", {})
        self.chat.show_tool_approval("request-1", "清空画布", {})
        self.assertEqual(len(self.chat.findChildren(QFrame, "tool_approval_frame")), 1)
        self.chat.findChild(QPushButton, "approval_deny").click()
        self.chat.show_tool_approval("request-1", "清空画布", {})
        self.assertEqual(resolved, [("request-1", False)])
        self.assertFalse(self.chat.findChild(QPushButton, "approval_allow_once").isEnabled())

    def test_end_or_cancel_denies_all_pending_approvals(self):
        resolved = []
        self.chat.approval_resolved.connect(lambda key, allowed: resolved.append((key, allowed)))
        self.chat.set_thinking(True)
        self.chat.show_tool_approval("one", "危险操作一", {})
        self.chat.show_tool_approval("two", "危险操作二", {})
        self.chat.set_thinking(False)
        self.chat.dismiss_tool_approvals()
        self.assertEqual(resolved, [("one", False), ("two", False)])

    def test_stop_button_cancels_runtime_before_dismissing_approval(self):
        events = []
        self.chat.approval_resolved.connect(lambda key, allowed: events.append((key, allowed)))
        self.chat.cancel_requested.connect(lambda: events.append("cancel"))
        self.chat.set_thinking(True)
        self.chat.show_tool_approval("pending", "写入参数", {})
        self.chat._input.setPlainText("下一步")
        self.chat._send_btn.click()
        self.assertEqual(events, ["cancel", ("pending", False)])
        self.assertEqual(self.chat._input.toPlainText(), "下一步")

    def test_gateway_expiry_is_silent_idempotent_and_cannot_reapprove(self):
        resolved = []
        self.chat.approval_resolved.connect(lambda key, allowed: resolved.append((key, allowed)))
        self.chat.show_tool_approval("pending", "写入参数", {})
        self.chat.expire_tool_approval("pending")
        self.chat.expire_tool_approval("pending")
        self.chat.expire_tool_approval("unknown")
        self.chat.dismiss_tool_approvals()
        self.chat.findChild(QPushButton, "approval_allow_once").click()
        self.assertEqual(resolved, [])
        self.assertFalse(self.chat.findChild(QPushButton, "approval_allow_once").isEnabled())
        self.assertFalse(self.chat.findChild(QPushButton, "approval_deny").isEnabled())
        self.assertIn("已结束", self.chat.findChild(QLabel, "approval_status").text())

    def test_gateway_expiry_preserves_recorded_operator_decision(self):
        resolved = []
        self.chat.approval_resolved.connect(lambda key, allowed: resolved.append((key, allowed)))
        self.chat.show_tool_approval("pending", "写入参数", {})
        self.chat.findChild(QPushButton, "approval_allow_once").click()
        self.chat.expire_tool_approval("pending")
        self.assertEqual(resolved, [("pending", True)])
        self.assertEqual(self.chat.findChild(QLabel, "approval_status").text(), "已允许一次")

    def test_clear_chat_forgets_card_identity_and_denies_pending(self):
        resolved = []
        self.chat.approval_resolved.connect(lambda key, allowed: resolved.append((key, allowed)))
        self.chat.update_tool_call("run", "call", "list_modules", "{}", "{}", "completed")
        self.chat.show_tool_approval("request", "清空", {})
        self.chat.clear_chat()
        self.assertEqual(self.chat._msg_layout.count(), 1)
        self.assertEqual(resolved, [("request", False)])
        self.chat.update_tool_call("run", "call", "list_modules", "{}", "{}", "completed")
        self.assertEqual(self.chat._msg_layout.count(), 2)

    def test_settings_offer_explicit_harness_and_native_with_harness_default(self):
        observed = []

        def inspect_dialog(dialog):
            picker = dialog.findChild(QComboBox, "agent_engine_selector")
            observed.append((picker.currentData(), [picker.itemData(i) for i in range(picker.count())]))
            return QDialog.Rejected

        with (
            patch("secret_store.load_agent_configuration", return_value=({"llm": {}}, "", "")),
            patch.object(QDialog, "exec", inspect_dialog),
        ):
            self.chat._open_settings()
        self.assertEqual(observed, [("harness", ["harness", "native"])])

    def test_save_settings_emits_only_after_success_and_keeps_legacy_signature(self):
        emitted = []
        self.chat.settings_saved.connect(emitted.append)
        dialog = Mock()
        config = {"llm": {}, "agent": {"engine": "native"}}
        with patch("secret_store.save_agent_settings", return_value=(config, "ephemeral")) as save:
            self.chat._save_settings(dialog, "https://example.test", "", "model", "native")
        self.assertEqual(save.call_args.kwargs["engine"], "native")
        self.assertEqual(emitted, [{"config": config, "api_key": "ephemeral"}])
        dialog.accept.assert_called_once()
        with patch("secret_store.save_agent_settings", return_value=(config, "")):
            self.chat._save_settings(Mock(), "https://example.test", "", "model")

    def test_failed_save_does_not_change_live_configuration(self):
        emitted = []
        self.chat.settings_saved.connect(emitted.append)
        dialog = Mock()
        with (
            patch("secret_store.save_agent_settings", side_effect=OSError("disk failure")),
            patch("agent_chat_widget.QMessageBox.warning"),
        ):
            self.chat._save_settings(dialog, "https://example.test", "", "model", "native")
        self.assertEqual(emitted, [])
        dialog.accept.assert_not_called()


class HarnessSettingsPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "config.json"
        self.keyring = Mock()
        self.keyring.get_password.return_value = None
        self.environment = patch.dict("os.environ", {}, clear=True)
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.directory.cleanup()

    def test_absent_runtime_loads_harness_without_creating_config(self):
        config, _key, _warning = load_agent_configuration(self.path, keyring_backend=self.keyring)
        self.assertEqual(config["agent"]["engine"], "harness")
        self.assertFalse(self.path.exists())

    def test_engine_persists_and_default_save_preserves_explicit_native(self):
        for engine in ("native", None):
            config, _key = save_agent_settings(
                self.path, endpoint="https://example.test/v1", api_key="",
                model="model", engine=engine, keyring_backend=self.keyring,
            )
            self.assertEqual(config["agent"]["engine"], "native")
        disk = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(disk["agent"]["engine"], "native")
        self.assertNotIn("api_key", disk["llm"])

    def test_invalid_engine_fails_before_credential_or_config_write(self):
        with self.assertRaises(ValueError):
            save_agent_settings(
                self.path, endpoint="https://example.test/v1", api_key="test-secret",
                model="model", engine="unknown", keyring_backend=self.keyring,
            )
        self.keyring.set_password.assert_not_called()
        self.assertFalse(self.path.exists())

    def test_invalid_agent_shape_is_rejected(self):
        self.path.write_text('{"agent": []}', encoding="utf-8")
        with self.assertRaises(ValueError):
            load_agent_configuration(self.path, keyring_backend=self.keyring)


if __name__ == "__main__":
    unittest.main()
