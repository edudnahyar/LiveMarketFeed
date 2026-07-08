import sys

from PySide6.QtWidgets import QApplication

from gui.dashboard import Dashboard
from gui import theme


def app():

    application = QApplication.instance() or QApplication(sys.argv)

    theme.load_bundled_fonts()   # no-op unless you drop TTFs in gui/assets/fonts/
    application.setStyleSheet(theme.GLOBAL_QSS)

    window = Dashboard()
    window.show()

    sys.exit(application.exec())
