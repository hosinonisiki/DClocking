#!/usr/bin/env python3
"""Exercise the real Qt operator workspace without devices, credentials or LLMs.

Run with a desktop Qt platform for visual inspection; use --keep-open to leave
the sample workspace visible. Every persisted artifact stays under --artifacts.
"""
import argparse
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "python control"), str(ROOT / "FPGA_Agent")]

from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from FPGA_Agent.pdh_experiment import ExperimentProfile, demo_trace
from qt_ui_mainwindow import MainWindow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", required=True, type=Path)
    parser.add_argument("--keep-open", action="store_true")
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    window = MainWindow(settings=QSettings(str(args.artifacts / "ui.ini"), QSettings.IniFormat),
                        custom_composite_path=args.artifacts / "composites.json",
                        experiment_repository_path=args.artifacts / "records")
    window.resize(1480, 950)
    window.show()
    app.processEvents()
    widget = window.open_pdh_workbench()
    widget.set_profile(ExperimentProfile(
        name="共振谷练习 · 离线演示", detector_source="示例探测器（非本机接线）", polarity="dip",
        signal_path="示例：探测器 → FIR → 判锁输入",
        error_path="示例：探测器 → 解调 → FIR → PID",
        scan_path="示例：扫描累加器 → 扫描同步；锁定时暂停保持",
        actuator_path="离线演示，无执行器输出；实机需填写通道和安全范围",
        clock_hz=250_000_000, notes="250 MHz 仅为本次演示换算值，不声明当前板卡时钟。"))
    app.processEvents()
    window.grab().save(str(args.artifacts / "01-setup.png"))
    with patch.object(window.port_ctrl, "send_param") as write:
        QTest.mouseClick(widget.next_button, Qt.LeftButton)
        widget.set_trace(demo_trace())
        QTest.mouseClick(widget.next_button, Qt.LeftButton)
        widget.waveform.set_selection(.006, .014)
        QTest.mouseClick(widget.suggest_button, Qt.LeftButton)
        before = widget.preview_parameters()["threshold_signal_scan"]
        marker = widget.waveform.marker_position("threshold_signal_scan").toPoint()
        QTest.mousePress(widget.waveform, Qt.LeftButton, pos=marker)
        QTest.mouseMove(widget.waveform, pos=marker + QPoint(0, -12))
        QTest.mouseRelease(widget.waveform, Qt.LeftButton, pos=marker + QPoint(0, -12))
        app.processEvents()
        assert widget.preview_parameters()["threshold_signal_scan"] != before
        assert widget.staged_parameters()
        window.grab().save(str(args.artifacts / "02-waveform-draft.png"))
        saved = args.artifacts / "pdh-demo.json"
        widget.save_bundle(saved)
        draft = widget.preview_parameters()
        widget.undo_draft()
        widget.load_bundle(saved)
        assert widget.preview_parameters() == draft
        widget.mode_combo.setCurrentIndex(1)
        app.processEvents()
        assert not widget.waveform.isEnabled()
        window.grab().save(str(args.artifacts / "03-automatic-mode.png"))
        widget.mode_combo.setCurrentIndex(0)
        widget.controls_scroll.ensureWidgetVisible(widget.local_button)
        app.processEvents()
        QTest.mouseClick(widget.local_button, Qt.LeftButton)
        assert not widget.staged_parameters()
        widget.set_step(3)
        QTest.mouseClick(widget.start_button, Qt.LeftButton)
        assert "未发送" in widget.operation_feedback.text()
        assert window.open_pdh_workbench() is widget
        widget.set_step(2)
        widget.controls_scroll.verticalScrollBar().setValue(0)
        app.processEvents()
        write.assert_not_called()
        window.grab().save(str(args.artifacts / "04-workbench.png"))
    print(json.dumps({"passed": True, "hardware_writes": 0,
                      "artifacts": str(args.artifacts), "platform": app.platformName()}, ensure_ascii=False), flush=True)
    if args.keep_open:
        return app.exec()
    window.close()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
