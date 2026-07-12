"""
timeframe_toggle.py — small HUD-styled button group (1M / 3M / 6M / 1Y)
used to control how much history the sparklines pull from Mongo.

Emits `changed(str)` whenever the selection changes.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup, QSizePolicy
from PySide6.QtCore import Qt, Signal

from gui import theme


class TimeframeToggle(QWidget):

    OPTIONS = ["1W", "1M", "3M"]

    changed = Signal(str)

    def __init__(self, default: str = "1M", parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons = {}

        for label in self.OPTIONS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(20)
            btn.setMinimumWidth(30)
            btn.setFont(theme.mono_font(8, bold=True))
            btn.setStyleSheet(self._qss())
            btn.clicked.connect(lambda _checked, l=label: self._on_click(l))
            self._group.addButton(btn)
            self._buttons[label] = btn
            layout.addWidget(btn)

        default = default if default in self._buttons else self.OPTIONS[0]
        self._buttons[default].setChecked(True)
        self._current = default

    def current(self) -> str:
        return self._current

    def _on_click(self, label: str):
        if label == self._current:
            return
        self._current = label
        self.changed.emit(label)

    @staticmethod
    def _qss():
        return f"""
            QPushButton {{
                background-color: {theme.BG_PANEL_ALT};
                color: {theme.TEXT_MUTED};
                border: 1px solid {theme.BORDER_DIM};
                border-radius: 2px;
                padding: 1px 2px;
            }}
            QPushButton:hover {{
                border: 1px solid {theme.ACCENT_CYAN_DIM};
                color: {theme.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {theme.ACCENT_CYAN_DIM};
                color: {theme.TEXT_PRIMARY};
                border: 1px solid {theme.ACCENT_CYAN};
            }}
        """
