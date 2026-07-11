"""
frame.py — HudFrame: the corner-bracketed panel chrome used everywhere in
the dashboard (index list, commodities, news, radar, ticker...).

QSS can't draw sci-fi corner brackets or a title strip with a tick mark,
so this is hand-painted in paintEvent(). Child widgets are placed in
`self.body` (a plain QVBoxLayout) below the title strip.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QRectF

from gui import theme


class HudFrame(QWidget):

    CORNER = 12          # length of each corner bracket in px
    PAD = 12             # inner content padding
    TITLE_H = 26          # height reserved for the title strip

    def __init__(self, title: str, accent: str = theme.ACCENT_CYAN, subtitle: str = "", parent=None):
        super().__init__(parent)
        self._accent = QColor(accent)
        self._title = title

        outer = QVBoxLayout(self)
        outer.setContentsMargins(self.PAD, self.TITLE_H + 6, self.PAD, self.PAD)
        outer.setSpacing(6)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(f"color: {theme.TEXT_MUTED};")
        self.subtitle_label.setFont(theme.mono_font(7))
        self.subtitle_label.setWordWrap(True)

        self.body = QVBoxLayout()
        self.body.setSpacing(6)

        if subtitle:
            outer.addWidget(self.subtitle_label)
        else:
            self.subtitle_label.setVisible(False)
        outer.addLayout(self.body)
        outer.addStretch(1)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_accent(self, color: str):
        self._accent = QColor(color)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)

        # panel fill
        p.fillRect(rect, QColor(theme.BG_PANEL))

        # faint full border
        pen = QPen(QColor(theme.BORDER_DIM))
        pen.setWidthF(1)
        p.setPen(pen)
        p.drawRect(rect)

        # corner brackets in accent color
        c = self.CORNER
        pen = QPen(self._accent)
        pen.setWidthF(1.6)
        p.setPen(pen)
        w, h = rect.width(), rect.height()
        x0, y0 = rect.left(), rect.top()
        x1, y1 = rect.right(), rect.bottom()

        # top-left
        p.drawLine(x0, y0, x0 + c, y0)
        p.drawLine(x0, y0, x0, y0 + c)
        # top-right
        p.drawLine(x1, y0, x1 - c, y0)
        p.drawLine(x1, y0, x1, y0 + c)
        # bottom-left
        p.drawLine(x0, y1, x0 + c, y1)
        p.drawLine(x0, y1, x0, y1 - c)
        # bottom-right
        p.drawLine(x1, y1, x1 - c, y1)
        p.drawLine(x1, y1, x1, y1 - c)

        # title strip: small tick + letter-spaced label
        tick_x = self.PAD
        tick_y = 14
        p.setPen(QPen(self._accent, 3))
        p.drawLine(tick_x, tick_y, tick_x + 10, tick_y)

        p.setPen(QPen(QColor(theme.TEXT_PRIMARY)))
        f = theme.display_font(10, bold=True)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 1.6)
        p.setFont(f)
        p.drawText(tick_x + 16, tick_y + 4, theme.spaced(self._title))

        p.end()
