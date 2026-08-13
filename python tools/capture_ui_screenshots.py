#!/usr/bin/env python3
"""Capture deterministic ordinary/integrated DClocking workstation previews."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "python control"
AGENT = ROOT / "FPGA_Agent"
for path in (str(CONTROL), str(AGENT), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from PySide6.QtCore import QPointF, QSettings
from PySide6.QtWidgets import QApplication

from FPGA_Agent.main import create_window as create_integrated_window
from qt_UI1 import create_window as create_ordinary_window
from qt_module import ModulePID, ModuleScaler


def add_demo_graph(window):
    pid = ModulePID("PID控制器", 0, QPointF(-190, -20))
    scaler = ModuleScaler("线性缩放器", 0, QPointF(190, 90))
    window.view._used_indices["PID控制器"].add(0)
    window.view._used_indices["线性缩放器"].add(0)
    window.scene.addItem(pid)
    window.scene.addItem(scaler)
    window.scene.create_connection(pid.out_ports[0], scaler.in_ports[0])
    window.view.center_on_nodes()
    window._refresh_ui_status()


def capture(factory, variant, width, height, output_dir, settings_path):
    settings = QSettings(str(settings_path), QSettings.IniFormat)
    settings.clear()
    window = factory(settings=settings)
    window.resize(width, height)
    window.show()
    app = QApplication.instance()
    app.processEvents()
    add_demo_graph(window)
    window.set_log_expanded(False)

    if variant == "integrated" and width >= 1600:
        window._agent_action.setChecked(True)
    if width >= 1920:
        window.set_log_expanded(True)
        window._append_log_text("[preview] PIDC → SCLR route ready\n")
    app.processEvents()

    output = output_dir / f"{variant}-{width}x{height}.png"
    if not window.grab().save(str(output), "PNG"):
        raise RuntimeError(f"Failed to save {output}")
    window.close()
    app.processEvents()
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_root = Path(temp_dir)
        for width, height in ((1280, 720), (1600, 900), (1920, 1080)):
            for variant, factory in (
                ("ordinary", create_ordinary_window),
                ("integrated", create_integrated_window),
            ):
                output = capture(
                    factory,
                    variant,
                    width,
                    height,
                    args.output,
                    settings_root / f"{variant}-{width}.ini",
                )
                print(output)


if __name__ == "__main__":
    main()
