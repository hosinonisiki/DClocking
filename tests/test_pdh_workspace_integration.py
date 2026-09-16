"""Main-window integration checks for the PDH rule designer."""

import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QPointF, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox, QPushButton

from tests.qt_test_support import ensure_app
from qt_module import ModulePDHFSM
from qt_pdh_designer import PDHDesignerWidget
from qt_ui_mainwindow import MainWindow


class PDHWorkspaceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        settings = QSettings(f"{self.temp_dir.name}/ui.ini", QSettings.IniFormat)
        self.window = MainWindow(settings=settings)
        self.window.resize(1280, 720)
        self.window.show()
        self.node = ModulePDHFSM("PDH状态机", 0, QPointF(0, 0))
        self.window.scene.addItem(self.node)
        with patch.object(self.window, "_refresh_node_params_from_device", return_value=False):
            self.assertTrue(self.window._open_param_panel(self.node))
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def _open_designer(self):
        card = next(iter(self.window._param_panels.values()))
        button = card.findChild(QPushButton, "pdh_designer_open_button")
        self.assertIsNotNone(button)
        button.click()
        self.app.processEvents()
        designer = self.window.workspace_tabs.currentWidget()
        self.assertIsInstance(designer, PDHDesignerWidget)
        return designer

    def test_pdh_mixer_port_uses_neutral_label_without_changing_port_contract(self):
        self.assertEqual(self.node.outputs_display_name[0], "PID复位请求")
        self.assertEqual(self.node.outputs_display_name[1], "混频器控制")
        self.assertEqual(self.node.outputs_display_name[2], "扫描累加器复位请求")
        self.assertEqual(self.node.outputs[1], "MIXER_RESET_CTRL")
        self.assertEqual(self.node.num_outputs, 3)

    def test_pdh_inspector_opens_named_designer_tab_with_truthful_source(self):
        designer = self._open_designer()
        self.assertIn("PDH状态机1", self.window.workspace_tabs.tabText(
            self.window.workspace_tabs.currentIndex()
        ))
        self.assertIn("未读取", designer.source_badge.text())
        self.assertIn("规则示意", designer.findChild(
            type(designer.source_badge), "pdh_designer_subtitle"
        ).text())

    def test_inspector_uses_verified_pdh_callback_and_preserves_offline_local_config(self):
        card = next(iter(self.window._param_panels.values()))
        callback = card._param_widget._apply_callback
        self.assertIsNot(callback, self.node.set_params)
        before = self.node.get_params()["threshold_signal_scan"]
        with patch.object(self.node, "set_params") as write, \
             patch.object(self.window.port_ctrl, "send_param") as send:
            callback({"threshold_signal_scan": before + 1})
        write.assert_not_called()
        send.assert_not_called()
        self.assertEqual(self.node.get_params()["threshold_signal_scan"], before + 1)
        self.assertIn("仅本地配置", card._pdh_source_badge.text())
        self.assertIn("未写入 FPGA", card._pdh_source_badge.text())
        config_node = next(item for item in self.window._build_config_dict()["nodes"]
                           if item["name"] == self.node.name)
        self.assertEqual(config_node["direct_params"]["threshold_signal_scan"], before + 1)

    def test_inspector_enter_failure_visibly_marks_value_unconfirmed(self):
        card = next(iter(self.window._param_panels.values()))
        card._pdh_parameter_source = "设备参数已读取 · 内部状态未回读"
        dialog = card._param_widget
        dialog.setEnabled(True)
        _kind, editor = dialog._editors["threshold_signal_scan"]
        before = dialog._committed_values["threshold_signal_scan"]
        editor.setFocus()
        editor.selectAll()
        QTest.keyClicks(editor, "123")
        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.window, "_refresh_node_params_from_device", return_value=True), \
             patch.object(self.node, "set_params"), \
             patch.object(QMessageBox, "warning") as warning:
            QTest.keyClick(editor, Qt.Key_Return)
            self.app.processEvents()
        warning.assert_called()
        self.assertEqual(dialog._committed_values["threshold_signal_scan"], before)
        self.assertFalse(editor.isEnabled())
        self.assertIn("写入未确认", card._pdh_source_badge.text())

    def test_inspector_offline_enter_updates_only_savable_local_config(self):
        card = next(iter(self.window._param_panels.values()))
        dialog = card._param_widget
        _kind, editor = dialog._editors["threshold_signal_scan"]
        self.assertTrue(editor.isEnabled())
        editor.setFocus()
        editor.selectAll()
        QTest.keyClicks(editor, "123")
        with patch.object(self.window.port_ctrl, "send_param") as send, \
             patch.object(QMessageBox, "warning") as warning:
            QTest.keyClick(editor, Qt.Key_Return)
            self.app.processEvents()
        send.assert_not_called()
        warning.assert_not_called()
        self.assertEqual(self.node.get_params()["threshold_signal_scan"], 123)
        self.assertIn("仅本地配置", card._pdh_source_badge.text())
        self.assertIn("未写入 FPGA", card._pdh_source_badge.text())

    def test_inspector_roll_steps_are_preview_only_then_apply_once(self):
        card = next(iter(self.window._param_panels.values()))
        dialog = card._param_widget
        dialog.setEnabled(True)
        _kind, editor = dialog._editors["threshold_signal_scan"]
        with patch.object(dialog, "_apply_callback") as apply:
            editor.setFocus()
            QTest.keyClick(editor, Qt.Key_Right)
            QTest.keyClick(editor, Qt.Key_Up)
            QTest.keyClick(editor, Qt.Key_Up)
            apply.assert_not_called()
            QTest.keyClick(editor, Qt.Key_Return)
            self.app.processEvents()
            self.assertEqual(apply.call_count, 1)

    def test_inspector_read_button_reenables_editor_after_successful_read(self):
        card = next(iter(self.window._param_panels.values()))
        self.window._set_pdh_inspector_unconfirmed(card)
        button = card.findChild(QPushButton, "pdh_inspector_refresh_button")
        self.assertIsNotNone(button)
        with patch.object(self.window, "_refresh_node_params_from_device", return_value=True):
            button.click()
            self.app.processEvents()
        self.assertTrue(card._param_widget.isEnabled())
        self.assertIn("设备参数已读取", card._pdh_source_badge.text())

    def test_inspector_rejects_swallowed_transport_failure(self):
        card = next(iter(self.window._param_panels.values()))
        card._pdh_parameter_source = "设备参数已读取 · 内部状态未回读"
        callback = card._param_widget._apply_callback
        before = self.node.get_params()["threshold_signal_scan"]
        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.window, "_refresh_node_params_from_device", return_value=True), \
             patch.object(self.node, "set_params") as write:
            with self.assertRaisesRegex(RuntimeError, "发送失败"):
                callback({"threshold_signal_scan": before + 1})
        write.assert_called_once()

    def test_inspector_rejects_changed_hardware_baseline_before_write(self):
        card = next(iter(self.window._param_panels.values()))
        card._pdh_parameter_source = "设备参数已读取 · 内部状态未回读"
        callback = card._param_widget._apply_callback
        before = self.node.get_params()["threshold_signal_scan"]

        def drift(_node, **_kwargs):
            self.node._params["threshold_signal_lock"] += 1
            return True

        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.window, "_refresh_node_params_from_device", side_effect=drift), \
             patch.object(self.node, "set_params") as write:
            with self.assertRaisesRegex(RuntimeError, "已变化"):
                callback({"threshold_signal_scan": before + 1})
        write.assert_not_called()
        self.assertIn("本次未写入 FPGA", card._pdh_source_badge.text())
        self.assertTrue(card._param_widget.isEnabled())

    def test_inspector_requires_confirming_register_readback(self):
        card = next(iter(self.window._param_panels.values()))
        card._pdh_parameter_source = "设备参数已读取 · 内部状态未回读"
        callback = card._param_widget._apply_callback
        before = self.node.get_params()["threshold_signal_scan"]

        def sent(changes):
            self.node._params.update(changes)
            self.window._pdh_write_receipts[id(self.node)] = True

        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.window, "_refresh_node_params_from_device", side_effect=[True, False]), \
             patch.object(self.node, "set_params", side_effect=sent):
            with self.assertRaisesRegex(RuntimeError, "回读失败"):
                callback({"threshold_signal_scan": before + 1})

    def test_inspector_commits_only_after_matching_readback(self):
        card = next(iter(self.window._param_panels.values()))
        card._pdh_parameter_source = "设备参数已读取 · 内部状态未回读"
        callback = card._param_widget._apply_callback
        before = self.node.get_params()["threshold_signal_scan"]

        def sent(changes):
            self.node._params.update(changes)
            self.window._pdh_write_receipts[id(self.node)] = True

        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.window, "_refresh_node_params_from_device", return_value=True), \
             patch.object(self.node, "set_params", side_effect=sent) as write:
            callback({"threshold_signal_scan": before + 1})
        write.assert_called_once_with({"threshold_signal_scan": before + 1})

    def test_inspector_command_readback_updates_open_workbench_label(self):
        designer = self._open_designer()
        designer.set_parameters(self.node.get_params(), source_label="设备参数已读取 · 内部状态未回读")
        card = next(iter(self.window._param_panels.values()))
        card._pdh_parameter_source = "设备参数已读取 · 内部状态未回读"

        def sent(changes):
            self.node._params.update(changes)
            self.window._pdh_write_receipts[id(self.node)] = True

        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.window, "_refresh_node_params_from_device", return_value=True), \
             patch.object(self.node, "set_params", side_effect=sent):
            card._param_widget._apply_callback({"pc_cmd": 1})
        self.assertIn("01 · 手动锁定模式启动请求", designer.command_label.text())
        self.assertEqual(designer.baseline_parameters()["pc_cmd"], 1)
        self.assertEqual(designer.staged_parameters(), {})

    def test_editing_rule_is_preview_only_until_explicit_apply(self):
        designer = self._open_designer()
        original = self.node.get_params()["threshold_signal_scan"]
        with patch.object(self.window.port_ctrl, "send_param") as send:
            designer._threshold_signal_scan_editor.setValue(original + 123)
            self.app.processEvents()
            self.assertEqual(designer.staged_parameters()["threshold_signal_scan"], original + 123)
            self.assertEqual(self.node.get_params()["threshold_signal_scan"], original)
            send.assert_not_called()

    def test_offline_apply_retains_preview_without_claiming_hardware_write(self):
        designer = self._open_designer()
        original = self.node.get_params()["threshold_signal_scan"]
        designer._threshold_signal_scan_editor.setValue(original + 123)
        with patch.object(self.window.port_ctrl, "send_param") as send:
            designer.apply_button.click()
            self.app.processEvents()
            send.assert_not_called()
        self.assertEqual(self.node.get_params()["threshold_signal_scan"], original)
        self.assertEqual(designer.staged_parameters()["threshold_signal_scan"], original + 123)
        self.assertIn("离线", designer.feedback.text())

    def test_offline_command_button_is_a_request_not_a_device_state(self):
        designer = self._open_designer()
        button = designer.findChild(QPushButton, "pdh_command_manual_button")
        self.assertIsNotNone(button)
        with patch.object(self.window.port_ctrl, "send_param") as send:
            button.click()
            self.app.processEvents()
            send.assert_not_called()
        self.assertEqual(self.node.get_params()["pc_cmd"], 0)
        self.assertIn("离线", designer.command_request_feedback.text())

    def test_removed_pdh_node_closes_its_designer_workspace(self):
        designer = self._open_designer()
        workspace_key = self.window.workspace_tabs.workspace_key(designer)
        self.assertIsNotNone(workspace_key)
        self.window._handle_node_removed(self.node)
        self.app.processEvents()
        self.assertIsNone(self.window.workspace_tabs.workspace_key(designer))

    def test_apply_uses_existing_node_writer_and_requires_register_readback(self):
        designer = self._open_designer()
        designer.set_parameters(self.node.get_params(), source_label="设备参数已读取 · 内部状态未回读")
        designer._threshold_signal_scan_editor.setValue(123)

        def update_cache(changes):
            self.node._params.update(changes)
            self.window._pdh_write_receipts[id(self.node)] = True

        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.node, "set_params", side_effect=update_cache) as apply, \
             patch.object(self.window, "_refresh_node_params_from_device", return_value=True) as read:
            designer.apply_button.click()
            self.app.processEvents()
        apply.assert_called_once_with({"threshold_signal_scan": 123})
        read.assert_called()
        self.assertEqual(designer.staged_parameters(), {})
        self.assertIn("设备参数已读取", designer.source_badge.text())

    def test_failed_readback_keeps_changes_unconfirmed(self):
        designer = self._open_designer()
        designer.set_parameters(self.node.get_params(), source_label="设备参数已读取 · 内部状态未回读")
        designer._threshold_signal_scan_editor.setValue(123)

        def sent_without_readback(_changes):
            self.window._pdh_write_receipts[id(self.node)] = True

        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.node, "set_params", side_effect=sent_without_readback) as apply, \
             patch.object(self.window, "_refresh_node_params_from_device", side_effect=[True, False]):
            designer.apply_button.click()
            self.app.processEvents()
        apply.assert_called_once()
        self.assertIn("回读失败", designer.feedback.text())
        self.assertEqual(designer.staged_parameters()["threshold_signal_scan"], 123)

    def test_unsafe_legacy_time_range_is_rejected_before_writing(self):
        designer = self._open_designer()
        designer._time_scan_editor.setText(str(2**31))
        self.app.processEvents()
        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.node, "set_params") as apply:
            designer.apply_button.click()
            self.app.processEvents()
        apply.assert_not_called()
        self.assertIn("兼容安全上限", designer.feedback.text())

    def test_closed_designer_tab_reopens_same_node_without_duplicate(self):
        first = self._open_designer()
        key = self.window.workspace_tabs.workspace_key(first)
        self.assertTrue(self.window.workspace_tabs.close_workspace(key))
        second = self._open_designer()
        self.assertIs(second, first)
        self.assertEqual(self.window.workspace_tabs.workspace_key(second), key)

    def test_clear_canvas_closes_old_designer_and_rejects_stale_node(self):
        designer = self._open_designer()
        key = self.window.workspace_tabs.workspace_key(designer)
        self.window._clear_canvas(False)
        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.node, "set_params") as apply:
            self.assertFalse(self.window._apply_pdh_designer_changes(
                self.node, designer, {"threshold_signal_scan": 123}
            ))
            apply.assert_not_called()
        self.assertNotIn(key, self.window.workspace_tabs._entries)

    def test_configuration_load_closes_old_pdh_workspace(self):
        designer = self._open_designer()
        key = self.window.workspace_tabs.workspace_key(designer)
        config_path = Path(self.temp_dir.name) / "empty.json"
        config_path.write_text(json.dumps({"version": 1, "nodes": [], "edges": []}), encoding="utf-8")
        with patch("qt_ui_mainwindow.QFileDialog.getOpenFileName", return_value=(str(config_path), "JSON (*.json)")):
            self.window.load_configuration()
        self.assertNotIn(key, self.window.workspace_tabs._entries)

    def test_offline_pdh_config_round_trip_restores_local_draft_without_serial_write(self):
        card = next(iter(self.window._param_panels.values()))
        card._param_widget._apply_callback({"threshold_signal_scan": 123})
        config_path = Path(self.temp_dir.name) / "pdh-draft.json"
        config_path.write_text(json.dumps(self.window._build_config_dict()), encoding="utf-8")
        with patch("qt_ui_mainwindow.QFileDialog.getOpenFileName",
                   return_value=(str(config_path), "JSON (*.json)")), \
             patch.object(self.window.port_ctrl, "send_param") as send:
            self.window.load_configuration()
        loaded = [item for item in self.window.scene.items() if isinstance(item, ModulePDHFSM)]
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].get_params()["threshold_signal_scan"], 123)
        send.assert_not_called()

    def test_offline_legacy_pdh_alias_config_restores_canonical_values(self):
        config = self.window._build_config_dict()
        pdh_cfg = next(item for item in config["nodes"] if item["name"] == self.node.name)
        pdh_cfg["direct_params"] = {
            "pc_cmd": 0, "thre_sig_lock": 111, "thre_sig_scan": -222,
            "time_scan": 10, "time_lock": 20,
            "coef_scan": 16384, "coef_lock": 24576,
        }
        config_path = Path(self.temp_dir.name) / "pdh-legacy.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        with patch("qt_ui_mainwindow.QFileDialog.getOpenFileName",
                   return_value=(str(config_path), "JSON (*.json)")), \
             patch.object(self.window.port_ctrl, "send_param") as send:
            self.window.load_configuration()
        loaded = next(item for item in self.window.scene.items() if isinstance(item, ModulePDHFSM))
        self.assertEqual(loaded.get_params()["threshold_signal_lock"], 111)
        self.assertEqual(loaded.get_params()["threshold_signal_scan"], -222)
        self.assertEqual(loaded._params["thre_sig_lock"], 111)
        self.assertEqual(loaded._params["thre_sig_scan"], -222)
        send.assert_not_called()

    def test_reopen_syncs_unedited_designer_with_new_node_values(self):
        designer = self._open_designer()
        self.node._params["threshold_signal_scan"] = 222
        self.window.workspace_tabs.show_home()
        with patch.object(self.window, "_refresh_node_params_from_device", return_value=False):
            second = self._open_designer()
        self.assertIs(second, designer)
        self.assertEqual(designer.preview_parameters()["threshold_signal_scan"], 222)

    def test_reopen_marks_pending_preview_conflict_instead_of_overwriting_it(self):
        designer = self._open_designer()
        designer._threshold_signal_scan_editor.setValue(123)
        self.node._params["threshold_signal_scan"] = 222
        self.window.workspace_tabs.show_home()
        with patch.object(self.window, "_refresh_node_params_from_device", return_value=False):
            self._open_designer()
        self.assertEqual(designer.preview_parameters()["threshold_signal_scan"], 123)
        self.assertIn("待核对", designer.source_badge.text())
        self.assertFalse(designer.apply_button.isEnabled())

    def test_failed_transport_is_not_hidden_by_matching_preexisting_readback(self):
        designer = self._open_designer()
        designer.set_parameters(self.node.get_params(), source_label="设备参数已读取 · 内部状态未回读")
        designer._threshold_signal_scan_editor.setValue(123)
        self.node._params["threshold_signal_scan"] = 123

        def failed_send(_changes):
            self.window._pdh_write_receipts[id(self.node)] = False

        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.node, "set_params", side_effect=failed_send) as apply, \
             patch.object(self.window, "_refresh_node_params_from_device", return_value=True):
            designer.apply_button.click()
        apply.assert_not_called()
        self.assertIn("基线不一致", designer.feedback.text())
        self.assertEqual(designer.staged_parameters()["threshold_signal_scan"], 123)

    def test_failed_send_after_verified_baseline_is_not_reported_successful(self):
        designer = self._open_designer()
        designer.set_parameters(self.node.get_params(), source_label="设备参数已读取 · 内部状态未回读")
        designer._threshold_signal_scan_editor.setValue(123)

        def failed_send(_changes):
            self.window._pdh_write_receipts[id(self.node)] = False

        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.node, "set_params", side_effect=failed_send) as apply, \
             patch.object(self.window, "_refresh_node_params_from_device", return_value=True):
            designer.apply_button.click()
        apply.assert_called_once()
        self.assertIn("发送失败", designer.feedback.text())
        self.assertEqual(designer.staged_parameters()["threshold_signal_scan"], 123)

    def test_failed_command_send_with_matching_existing_code_is_not_claimed(self):
        designer = self._open_designer()
        designer.set_parameters(self.node.get_params(), source_label="设备参数已读取 · 内部状态未回读")
        button = designer.findChild(QPushButton, "pdh_command_idle_button")

        def failed_send(_changes):
            self.window._pdh_write_receipts[id(self.node)] = False

        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.node, "set_params", side_effect=failed_send) as apply, \
             patch.object(self.window, "_refresh_node_params_from_device", return_value=True):
            button.click()
        apply.assert_called_once_with({"pc_cmd": 0})
        self.assertIn("发送失败", designer.command_request_feedback.text())

    def test_confirmed_workbench_command_refreshes_label_and_keeps_rule_preview(self):
        designer = self._open_designer()
        designer.set_parameters(self.node.get_params(), source_label="设备参数已读取 · 内部状态未回读")
        designer._threshold_signal_scan_editor.setValue(123)

        def sent(changes):
            self.node._params.update(changes)
            self.window._pdh_write_receipts[id(self.node)] = True

        button = designer.findChild(QPushButton, "pdh_command_manual_button")
        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.window, "_refresh_node_params_from_device", return_value=True), \
             patch.object(self.node, "set_params", side_effect=sent):
            button.click()
        self.assertIn("01 · 手动锁定模式启动请求", designer.command_label.text())
        self.assertEqual(designer.staged_parameters()["threshold_signal_scan"], 123)

    def test_device_connection_requires_fresh_parameter_baseline_before_apply(self):
        designer = self._open_designer()
        designer._threshold_signal_scan_editor.setValue(123)
        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.node, "set_params") as apply, \
             patch.object(self.window, "_refresh_node_params_from_device", return_value=True):
            designer.apply_button.click()
        apply.assert_not_called()
        self.assertIn("待核对", designer.source_badge.text())

    def test_changed_device_parameter_blocks_old_preview_at_apply_time(self):
        designer = self._open_designer()
        designer.set_parameters(self.node.get_params(), source_label="设备参数已读取 · 内部状态未回读")
        designer._threshold_signal_scan_editor.setValue(123)

        def read_new_hardware(_node):
            self.node._params["threshold_signal_scan"] = 222
            return True

        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.node, "set_params") as apply, \
             patch.object(self.window, "_refresh_node_params_from_device", side_effect=read_new_hardware):
            designer.apply_button.click()
        apply.assert_not_called()
        self.assertIn("待核对", designer.source_badge.text())
        self.assertEqual(designer.preview_parameters()["threshold_signal_scan"], 123)

    def test_start_request_does_not_claim_edge_when_command_is_already_set(self):
        designer = self._open_designer()
        designer.set_parameters(self.node.get_params(), source_label="设备参数已读取 · 内部状态未回读")
        self.node._params["pc_cmd"] = 1
        button = designer.findChild(QPushButton, "pdh_command_manual_button")
        with patch.object(self.window, "_pdh_device_connected", return_value=True), \
             patch.object(self.node, "set_params") as apply, \
             patch.object(self.window, "_refresh_node_params_from_device", return_value=True):
            button.click()
        apply.assert_not_called()
        self.assertIn("00→01", designer.command_request_feedback.text())


if __name__ == "__main__":
    unittest.main()
