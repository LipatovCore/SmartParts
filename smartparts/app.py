import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from smartparts.ui.login_window import LoginWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("SmartParts")
    app.setFont(QFont("Arial"))

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())
