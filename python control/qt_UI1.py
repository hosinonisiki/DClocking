import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


def create_window(settings=None):
    """Create the workstation with the integrated AI Agent panel."""
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from FPGA_Agent.main import create_window as create_agent_window

    return create_agent_window(settings=settings)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = create_window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
