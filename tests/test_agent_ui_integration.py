import tempfile
import unittest
import sys
from unittest.mock import patch

from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QTextBrowser

from tests.qt_test_support import ensure_app
from agent_chat_widget import AgentChatWidget
from qt_ui_mainwindow import MainWindow


class AgentUiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = QSettings(
            f"{self.temp_dir.name}/ui.ini", QSettings.IniFormat
        )
        self.window = MainWindow(settings=self.settings)
        self.window.resize(1280, 720)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def test_registered_agent_is_hidden_by_default_and_two_controls_share_state(self):
        chat = AgentChatWidget(self.window)
        action = self.window.register_agent_dock(chat)
        self.app.processEvents()
        self.assertFalse(chat.isVisible())
        self.assertFalse(action.isChecked())
        self.window.agent_toggle_btn.click()
        self.app.processEvents()
        self.assertTrue(chat.isVisible())
        self.window.agent_fab.click()
        self.app.processEvents()
        self.assertFalse(chat.isVisible())

    def test_legacy_qt_ui1_entrypoint_registers_agent_workbench(self):
        from qt_UI1 import create_window

        legacy_window = create_window(settings=self.settings)
        legacy_window.show()
        self.app.processEvents()
        try:
            self.assertIsNotNone(legacy_window._agent_dock)
            self.assertIsNotNone(legacy_window._agent_action)
            self.assertFalse(legacy_window.agent_toggle_btn.isHidden())
            self.assertFalse(legacy_window.agent_fab.isHidden())
        finally:
            legacy_window.close()

    def test_hiding_agent_does_not_destroy_messages(self):
        chat = AgentChatWidget(self.window)
        self.window.register_agent_dock(chat)
        chat.add_assistant_message("persistent message")
        chat.show()
        chat.hide()
        chat.show()
        self.app.processEvents()
        messages = chat._msg_container.findChildren(QTextBrowser)
        self.assertTrue(any("persistent message" in msg.toPlainText() for msg in messages))

    def test_chat_uses_workstation_colors_and_accessible_controls(self):
        chat = AgentChatWidget(self.window)
        self.assertIn("#85172E", chat.widget().styleSheet())
        self.assertEqual(chat._send_btn.accessibleName(), "发送 Agent 消息")
        self.assertTrue(callable(chat.open_settings))

    def test_markdown_fallback_uses_qt_renderer_without_raw_markers(self):
        chat = AgentChatWidget(self.window)
        with patch.dict(sys.modules, {"markdown": None}):
            chat.add_assistant_message("## Ready\n\n**connected**")
        message = chat._msg_container.findChildren(QTextBrowser)[0]
        self.assertNotIn("##", message.toPlainText())
        self.assertNotIn("**", message.toPlainText())

    def test_message_bubbles_fit_short_content_without_internal_scrollbars(self):
        chat = AgentChatWidget(self.window)
        self.window.register_agent_dock(chat)
        chat.show()
        chat.add_user_message("短消息")
        chat.add_assistant_message("简短回复")
        self.app.processEvents()

        messages = chat._msg_container.findChildren(QTextBrowser)
        self.assertEqual(len(messages), 2)
        for message in messages:
            self.assertLess(message.height(), 100)
            self.assertEqual(
                message.verticalScrollBarPolicy(),
                Qt.ScrollBarAlwaysOff,
            )

        short_assistant_height = messages[1].height()
        chat.add_assistant_message("这是一段用于验证自适应高度的长回复。" * 20)
        self.app.processEvents()
        messages = chat._msg_container.findChildren(QTextBrowser)
        self.assertGreater(messages[2].height(), short_assistant_height)
        self.assertEqual(
            messages[2].verticalScrollBarPolicy(),
            Qt.ScrollBarAlwaysOff,
        )

    def test_enter_sends_and_shift_enter_inserts_a_newline(self):
        chat = AgentChatWidget(self.window)
        submitted = []
        chat.user_message_submitted.connect(submitted.append)

        chat._input.setPlainText("立即发送")
        QTest.keyClick(chat._input, Qt.Key_Return)
        self.app.processEvents()
        self.assertEqual(submitted, ["立即发送"])
        self.assertEqual(chat._input.toPlainText(), "")

        chat._input.setPlainText("第一行")
        chat._input.moveCursor(chat._input.textCursor().MoveOperation.End)
        QTest.keyClick(chat._input, Qt.Key_Return, Qt.ShiftModifier)
        self.app.processEvents()
        self.assertEqual(submitted, ["立即发送"])
        self.assertEqual(chat._input.toPlainText(), "第一行\n")

    def test_agent_visibility_and_dock_state_restore_after_registration(self):
        chat = AgentChatWidget(self.window)
        self.window.register_agent_dock(chat)
        self.window.resizeDocks([chat], [360], Qt.Horizontal)
        self.window._agent_action.setChecked(True)
        self.app.processEvents()
        self.window._save_ui_state()
        self.window.close()

        restored = MainWindow(settings=self.settings)
        restored.resize(1280, 720)
        restored_chat = AgentChatWidget(restored)
        action = restored.register_agent_dock(restored_chat)
        restored.show()
        self.app.processEvents()
        try:
            self.assertTrue(action.isChecked())
            self.assertTrue(restored_chat.isVisible())
            self.assertEqual(
                restored.dockWidgetArea(restored_chat), Qt.RightDockWidgetArea
            )
            self.assertGreaterEqual(restored_chat.width(), 320)
        finally:
            restored.close()


if __name__ == "__main__":
    unittest.main()
