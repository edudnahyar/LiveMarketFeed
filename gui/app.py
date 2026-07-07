import sys

from PySide6.QtWidgets import QApplication

from gui.dashboard import Dashboard


def app():

    app = QApplication(sys.argv)

    window = Dashboard()

    window.show()

    sys.exit(QApplication.instance().exec())
