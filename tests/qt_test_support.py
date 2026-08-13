import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "python control"
AGENT = ROOT / "FPGA_Agent"
for path in (str(CONTROL), str(AGENT), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from PySide6.QtWidgets import QApplication


def ensure_app():
    return QApplication.instance() or QApplication([])
