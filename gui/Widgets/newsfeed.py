"""
newsfeed.py — scrolling global news feed panel. UI-only: call
add_news(headline, source, timestamp) whenever your news source
(RSS/API/websocket) produces an item. No news data source exists yet
in the repo's data/ layer — this just gives you the drop-in widget.
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt

from gui import theme


class NewsFeed(QWidget):

    MAX_ITEMS = 40

    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 4, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch(1)

        self._scroll.setWidget(self._list_widget)
        outer.addWidget(self._scroll)

        self._count = 0

    def add_news(self, headline: str, source: str = "", timestamp: datetime = None):
        timestamp = timestamp or datetime.now()

        row = QWidget()
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(1)

        meta = QLabel(f'{timestamp.strftime("%H:%M")}  ·  {source.upper()}' if source
                      else timestamp.strftime("%H:%M"))
        meta.setFont(theme.mono_font(7))
        meta.setStyleSheet(f"color: {theme.ACCENT_AMBER};")

        headline_lbl = QLabel(headline)
        headline_lbl.setWordWrap(True)
        headline_lbl.setFont(theme.display_font(9, bold=False))
        headline_lbl.setStyleSheet(f"color: {theme.TEXT_PRIMARY};")

        rule = QLabel()
        rule.setFixedHeight(1)
        rule.setStyleSheet(f"background-color: {theme.BORDER_DIM};")

        row_layout.addWidget(meta)
        row_layout.addWidget(headline_lbl)
        row_layout.addWidget(rule)

        # newest on top
        self._list_layout.insertWidget(0, row)
        self._count += 1

        if self._count > self.MAX_ITEMS:
            item = self._list_layout.takeAt(self.MAX_ITEMS)
            if item and item.widget():
                item.widget().deleteLater()
            self._count -= 1
