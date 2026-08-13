import sys

from PySide6.QtWidgets import QApplication

from qt_ui_mainwindow import MainWindow


def create_window(settings=None):
    return MainWindow(settings=settings)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = create_window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
