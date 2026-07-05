import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .gui.main_window import MainWindow
from .gui.style import APP_STYLESHEET


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(__import__(__package__).__app_name__)
    app.setOrganizationName("WoodwindDesignAutomation")
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
