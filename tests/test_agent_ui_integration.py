import tempfile
import unittest

from PySide6.QtCore import QSettings
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
        settings = QSettings(f"{self.temp_dir.name}/ui.ini", QSettings.IniFormat)
        self.window = MainWindow(settings=settings)
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


if __name__ == "__main__":
    unittest.main()
