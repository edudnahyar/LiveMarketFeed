"""
ticker.py — bottom marquee ticker tape, continuously scrolling
right-to-left, like an exchange tape / news crawl.
"""

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt, QTimer

from gui import theme


class TickerTape(QWidget):

    SPEED_PX = 1.4          # px per tick
    TICK_MS = 30
    GAP = 60                # px gap between repeated loop of items

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []     # list of (label, value_str, color)
        self._offset = 0.0
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(self.TICK_MS)

    def set_items(self, items):
        """items: list of (label, value_str, color_hex)"""
        self._items = list(items)
        self.update()

    def _advance(self):
        if not self._items:
            return
        self._offset -= self.SPEED_PX
        total_w = self._content_width()
        if total_w > 0 and -self._offset > total_w:
            self._offset += total_w
        self.update()

    def _content_width(self):
        fm = self.fontMetrics()
        w = 0
        for label, value, _ in self._items:
            w += fm.horizontalAdvance(f"{label}  {value}") + self.GAP
        return w

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        p.fillRect(rect, QColor(theme.BG_PANEL_ALT))
        p.setPen(QColor(theme.BORDER_DIM))
        p.drawLine(0, 0, self.width(), 0)

        if not self._items:
            p.end()
            return

        f = theme.mono_font(9, bold=True)
        p.setFont(f)
        fm = p.fontMetrics()

        total_w = self._content_width()
        x = self._offset
        y = rect.height() // 2 + fm.ascent() // 2 - 1

        # draw enough repeats to fill the width twice over (seamless loop)
        while x < self.width():
            for label, value, color in self._items:
                seg = f"{label}"
                p.setPen(QColor(theme.TEXT_MUTED))
                p.drawText(int(x), y, seg)
                x += fm.horizontalAdvance(seg) + 6

                p.setPen(QColor(color))
                p.drawText(int(x), y, value)
                x += fm.horizontalAdvance(value)

                p.setPen(QColor(theme.BORDER_DIM))
                p.drawText(int(x) + self.GAP // 2, y, "//")
                x += self.GAP
                if x > self.width() + 200:
                    break
            if total_w <= 0:
                break

        p.end()
