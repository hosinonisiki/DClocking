"""PDH rule designer must stage native register values without inventing telemetry."""

import unittest

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication, QLabel, QLineEdit, QPushButton, QSlider, QSpinBox, QToolButton,
)

from tests.qt_test_support import ensure_app
from qt_pdh_designer import PDHDesignerWidget, PDHRuleCanvas


PARAMETERS = {
    "pc_cmd": 2,
    "threshold_signal_lock": 1300,
    "threshold_signal_scan": -1200,
    "time_scan": 0x20000000,
    "time_lock": 0x20000000,
    "coef_scan": 16384,
    "coef_lock": 30000,
}


class PDHDesignerWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ensure_app()

    def setUp(self):
        self.widget = PDHDesignerWidget()
        self.widget.set_parameters(PARAMETERS, source_label="本地配置")
        self.widget.show()
        self.app.processEvents()

    def tearDown(self):
        self.widget.close()
        self.app.processEvents()

    def test_original_registers_are_preserved_and_source_is_not_live_hardware(self):
        self.assertEqual(self.widget.staged_parameters(), {})
        self.assertEqual(self.widget.preview_parameters(), PARAMETERS)
        self.assertIn("规则示意", self.widget.findChild(PDHRuleCanvas, "pdh_manual_rule_canvas").accessibleName())
        self.assertEqual(self.widget.findChild(QLineEdit, "pdh_time_scan_cycles").text(), "536870912")

    def test_command_readback_updates_only_request_label_not_pending_rule_edits(self):
        self.widget._threshold_signal_scan_editor.setValue(-1000)
        self.widget.update_command_value(1)
        self.assertIn("01 · 手动锁定模式启动请求", self.widget.command_label.text())
        self.assertEqual(self.widget.baseline_parameters()["pc_cmd"], 1)
        self.assertEqual(self.widget.staged_parameters()["threshold_signal_scan"], -1000)
        self.assertIn("本地配置", self.widget.findChild(QPushButton, "pdh_apply_button").toolTip())

    def test_manual_value_change_is_staged_and_apply_is_explicit(self):
        previews, applies = [], []
        self.widget.parameter_preview_changed.connect(lambda key, value: previews.append((key, value)))
        self.widget.apply_requested.connect(applies.append)
        editor = self.widget.findChild(QSpinBox, "pdh_threshold_signal_scan")
        editor.setValue(-1100)
        self.app.processEvents()

        self.assertEqual(previews[-1], ("threshold_signal_scan", -1100))
        self.assertEqual(self.widget.staged_parameters(), {"threshold_signal_scan": -1100})
        self.assertEqual(applies, [])

        self.widget.findChild(QPushButton, "pdh_apply_button").click()
        self.assertEqual(applies, [{"threshold_signal_scan": -1100}])
        self.assertNotIn("pc_cmd", applies[0])

    def test_unsigned_32_bit_duration_is_preserved_but_not_reapplied_above_ui_limit(self):
        observed = []
        applied = []
        self.widget.parameter_preview_changed.connect(lambda key, value: observed.append((key, value)))
        self.widget.apply_requested.connect(applied.append)
        editor = self.widget.findChild(QLineEdit, "pdh_time_scan_cycles")
        editor.setText("4294967295")
        QTest.keyClick(editor, Qt.Key_Tab)
        self.app.processEvents()
        self.assertEqual(self.widget.staged_parameters(), {"time_scan": 4294967295})
        self.assertEqual(observed[-1], ("time_scan", 4294967295))
        apply_button = self.widget.findChild(QPushButton, "pdh_apply_button")
        self.assertFalse(apply_button.isEnabled())
        self.assertIn("当前界面兼容安全上限", self.widget.findChild(QLabel, "pdh_designer_feedback").text())
        apply_button.click()
        self.assertEqual(applied, [])

        editor.setText("2147483647")
        self.app.processEvents()
        self.assertEqual(self.widget.staged_parameters(), {"time_scan": 2147483647})
        self.assertTrue(apply_button.isEnabled())

    def test_q15_out_of_interval_is_not_clamped_when_loaded(self):
        original = dict(PARAMETERS, coef_scan=-32768, coef_lock=-3)
        self.widget.set_parameters(original, source_label="设备已读")
        self.assertEqual(self.widget.preview_parameters(), original)
        self.assertEqual(self.widget.staged_parameters(), {})
        self.assertIn(
            "原始 Q1.15 值已保留",
            self.widget.findChild(QLabel, "pdh_auto_warning").text(),
        )

        events = []
        self.widget.apply_requested.connect(events.append)
        slider = self.widget.findChild(QSlider, "pdh_coef_scan_slider")
        slider.setValue(16384)
        self.app.processEvents()
        self.assertEqual(events, [])
        self.assertEqual(self.widget.staged_parameters(), {"coef_scan": 16384})

    def test_manual_threshold_marker_can_be_dragged_for_preview_only(self):
        canvas = self.widget.findChild(PDHRuleCanvas, "pdh_manual_rule_canvas")
        events = []
        self.widget.parameter_preview_changed.connect(lambda key, value: events.append((key, value)))
        start = canvas.marker_position("threshold_signal_scan")
        self.assertIsNotNone(start)
        QTest.mousePress(canvas, Qt.LeftButton, pos=start)
        QTest.mouseMove(canvas, pos=start + canvas.marker_drag_delta(20))
        QTest.mouseRelease(canvas, Qt.LeftButton, pos=start + canvas.marker_drag_delta(20))
        self.app.processEvents()

        self.assertTrue(any(key == "threshold_signal_scan" for key, _ in events))
        self.assertIn("threshold_signal_scan", self.widget.staged_parameters())

    def test_auto_threshold_marker_can_be_dragged_without_write_request(self):
        self.widget.tabs.setCurrentIndex(1)
        self.app.processEvents()
        canvas = self.widget.findChild(PDHRuleCanvas, "pdh_auto_rule_canvas")
        pending_writes = []
        self.widget.apply_requested.connect(pending_writes.append)
        start = canvas.marker_position("coef_scan")
        QTest.mousePress(canvas, Qt.LeftButton, pos=start)
        QTest.mouseMove(canvas, pos=start + canvas.marker_drag_delta(-18))
        QTest.mouseRelease(canvas, Qt.LeftButton, pos=start + canvas.marker_drag_delta(-18))
        self.app.processEvents()
        self.assertIn("coef_scan", self.widget.staged_parameters())
        self.assertEqual(pending_writes, [])

    def test_refresh_replaces_pending_preview_after_successful_readback(self):
        self.widget.findChild(QSpinBox, "pdh_threshold_signal_scan").setValue(-1100)
        self.assertTrue(self.widget.staged_parameters())
        self.widget.set_parameters(dict(PARAMETERS, threshold_signal_scan=-1000), source_label="设备已读")
        self.assertEqual(self.widget.staged_parameters(), {})
        self.assertEqual(self.widget.preview_parameters()["threshold_signal_scan"], -1000)

    def test_invalid_duration_disables_apply_and_preserves_last_valid_preview(self):
        editor = self.widget.findChild(QLineEdit, "pdh_time_lock_cycles")
        editor.setText("4294967296")
        self.app.processEvents()
        self.assertFalse(self.widget.findChild(QPushButton, "pdh_apply_button").isEnabled())
        self.assertEqual(self.widget.preview_parameters()["time_lock"], PARAMETERS["time_lock"])
        editor.setText("987")
        self.app.processEvents()
        self.assertEqual(self.widget.staged_parameters(), {"time_lock": 987})
        self.assertTrue(self.widget.findChild(QPushButton, "pdh_apply_button").isEnabled())

    def test_unicode_superscript_digit_is_rejected_without_overwriting_preview(self):
        editor = self.widget.findChild(QLineEdit, "pdh_time_lock_cycles")
        editor.setText("987")
        self.app.processEvents()
        self.assertEqual(self.widget.staged_parameters(), {"time_lock": 987})
        editor.setText("²")
        self.app.processEvents()
        self.assertEqual(self.widget.staged_parameters(), {"time_lock": 987})
        self.assertFalse(self.widget.findChild(QPushButton, "pdh_apply_button").isEnabled())
        self.assertIn("ASCII", self.widget.findChild(QLabel, "pdh_designer_feedback").text())
        editor.setText(" 123 ")
        self.app.processEvents()
        self.assertEqual(self.widget.staged_parameters(), {"time_lock": 987})
        self.assertFalse(self.widget.findChild(QPushButton, "pdh_apply_button").isEnabled())

    def test_loaded_legacy_uint32_time_is_visible_without_blocking_unrelated_edits(self):
        legacy = dict(PARAMETERS, time_scan=4294967295)
        self.widget.set_parameters(legacy, source_label="设备已读")
        self.assertEqual(self.widget.preview_parameters(), legacy)
        self.assertEqual(self.widget.staged_parameters(), {})
        self.assertEqual(
            self.widget.findChild(QLineEdit, "pdh_time_scan_cycles").text(),
            "4294967295",
        )
        self.assertIn(
            "仅保留历史值",
            self.widget.findChild(QLabel, "pdh_duration_hint").text(),
        )
        self.widget.findChild(QSpinBox, "pdh_threshold_signal_scan").setValue(-1100)
        self.app.processEvents()
        self.assertEqual(self.widget.staged_parameters(), {"threshold_signal_scan": -1100})
        self.assertTrue(self.widget.findChild(QPushButton, "pdh_apply_button").isEnabled())
        editor = self.widget.findChild(QLineEdit, "pdh_time_scan_cycles")
        editor.setText("429496729")
        editor.setText("4294967295")
        self.app.processEvents()
        self.assertEqual(self.widget.staged_parameters(), {"threshold_signal_scan": -1100})
        self.assertTrue(self.widget.findChild(QPushButton, "pdh_apply_button").isEnabled())

    def test_period_to_milliseconds_requires_explicit_board_clock(self):
        no_clock = self.widget.findChild(QLabel, "pdh_duration_hint").text()
        self.assertIn("未确认板卡时钟", no_clock)
        self.widget.set_parameters(PARAMETERS, source_label="本地配置", clock_hz=250_000_000)
        converted = self.widget.findChild(QLabel, "pdh_duration_hint").text()
        self.assertIn("MHz", converted)
        self.assertIn("ms", converted)

    def test_write_feedback_never_impersonates_hardware_readback(self):
        self.widget.findChild(QSpinBox, "pdh_threshold_signal_scan").setValue(-1100)
        self.widget.set_apply_result(True, "命令已发送。")
        self.assertEqual(self.widget.staged_parameters(), {"threshold_signal_scan": -1100})
        self.assertIn("请回读设备", self.widget.findChild(QLabel, "pdh_designer_feedback").text())
        self.widget.set_apply_result(False, "设备离线")
        self.assertIn("设备离线", self.widget.findChild(QLabel, "pdh_designer_feedback").text())

    def test_control_buttons_emit_request_only_without_changing_config_preview(self):
        requested, applied = [], []
        self.widget.command_requested.connect(requested.append)
        self.widget.apply_requested.connect(applied.append)
        for name, expected in (
            ("pdh_command_idle_button", 0),
            ("pdh_command_manual_button", 1),
            ("pdh_command_auto_button", 2),
        ):
            button = self.widget.findChild(QPushButton, name)
            self.assertIsNotNone(button)
            button.click()
            self.assertEqual(requested[-1], expected)
        self.assertEqual(requested, [0, 1, 2])
        self.assertEqual(applied, [])
        self.assertEqual(self.widget.preview_parameters()["pc_cmd"], PARAMETERS["pc_cmd"])
        self.assertEqual(self.widget.staged_parameters(), {})

    def test_lock_mode_names_still_describe_requests_not_confirmed_hardware_state(self):
        manual = self.widget.findChild(QPushButton, "pdh_command_manual_button")
        auto = self.widget.findChild(QPushButton, "pdh_command_auto_button")
        self.assertEqual(manual.text(), "手动锁定模式 (01)")
        self.assertEqual(auto.text(), "自动锁定模式 (10)")
        self.assertIn("扫描阶段", manual.toolTip())
        self.assertIn("自动校准流程", auto.toolTip())
        self.assertIn("请求发送", manual.toolTip())
        self.assertIn("请求发送", auto.toolTip())
        self.assertIn("不表示已锁定", manual.toolTip())
        self.assertIn("不表示已锁定", auto.toolTip())
        self.assertIn("请求码不是当前硬件状态", self.widget.command_label.text())

    def test_advanced_command_help_is_collapsed_and_does_not_promise_urgent_stop(self):
        toggle = self.widget.findChild(QToolButton, "pdh_command_advanced_toggle")
        detail = self.widget.findChild(QLabel, "pdh_command_advanced_detail")
        self.assertIsNotNone(toggle)
        self.assertIsNotNone(detail)
        self.assertFalse(detail.isVisible())
        toggle.click()
        self.assertTrue(detail.isVisible())
        self.assertIn("AUTO_LOCKING", detail.text())
        self.assertIn("不是第四种启动模式", detail.text())
        warning = self.widget.findChild(QLabel, "pdh_command_warning").text()
        self.assertIn("00→01／10", warning)
        self.assertIn("不保证任何状态立即停止", warning)

    def test_conflict_keeps_preview_but_blocks_apply_until_source_is_verified(self):
        self.widget.findChild(QSpinBox, "pdh_threshold_signal_scan").setValue(-1100)
        pending = self.widget.staged_parameters()
        self.assertEqual(pending, {"threshold_signal_scan": -1100})
        applied = []
        commands = []
        self.widget.apply_requested.connect(applied.append)
        self.widget.command_requested.connect(commands.append)

        self.widget.mark_conflict("当前标签可能关联旧设备或节点")
        self.assertEqual(self.widget.staged_parameters(), pending)
        self.assertIn("待核对", self.widget.findChild(QLabel, "pdh_source_badge").text())
        self.assertIn("旧设备", self.widget.findChild(QLabel, "pdh_designer_feedback").text())
        button = self.widget.findChild(QPushButton, "pdh_apply_button")
        self.assertFalse(button.isEnabled())
        command_button = self.widget.findChild(QPushButton, "pdh_command_manual_button")
        self.assertFalse(command_button.isEnabled())
        button.click()
        command_button.click()
        self.assertEqual(applied, [])
        self.assertEqual(commands, [])

        refreshed = dict(PARAMETERS, threshold_signal_scan=-900)
        self.widget.set_parameters(refreshed, source_label="设备已读")
        self.assertEqual(self.widget.staged_parameters(), {})
        self.assertEqual(self.widget.preview_parameters(), refreshed)
        self.assertNotIn("待核对", self.widget.findChild(QLabel, "pdh_source_badge").text())
        self.widget.findChild(QSpinBox, "pdh_threshold_signal_scan").setValue(-800)
        self.app.processEvents()
        self.assertTrue(button.isEnabled())
        self.assertTrue(self.widget.findChild(QPushButton, "pdh_command_manual_button").isEnabled())

    def test_refresh_button_requests_controller_read_and_does_not_discard_preview(self):
        self.widget.findChild(QSpinBox, "pdh_threshold_signal_scan").setValue(-1100)
        self.widget.mark_conflict("与当前节点未核对")
        before = self.widget.preview_parameters()
        requested = []
        self.widget.refresh_requested.connect(lambda: requested.append(True))
        button = self.widget.findChild(QPushButton, "pdh_refresh_button")
        self.assertIsNotNone(button)
        self.assertIn("丢弃未应用更改", button.toolTip())
        self.assertIn("读取失败时预览保留", button.toolTip())
        button.click()
        self.app.processEvents()

        self.assertEqual(requested, [True])
        self.assertEqual(self.widget.preview_parameters(), before)
        self.assertIn("待核对", self.widget.findChild(QLabel, "pdh_source_badge").text())

    def test_public_baseline_is_a_defensive_copy(self):
        baseline = self.widget.baseline_parameters()
        self.assertEqual(baseline, PARAMETERS)
        baseline["threshold_signal_scan"] = 999
        self.assertEqual(
            self.widget.baseline_parameters()["threshold_signal_scan"],
            PARAMETERS["threshold_signal_scan"],
        )


if __name__ == "__main__":
    unittest.main()
