"""
sparkline.py — lightweight rolling line/area chart, no QtCharts dependency.

Sparkline: single-series mini chart used inside each MarketCard.
MultiSparkline: overlays several named series in one bigger panel
                (used for the "MARKET PULSE" overview chart).
"""

from collections import deque

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QPen, QColor, QLinearGradient, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF

from gui import theme


class Sparkline(QWidget):

    def __init__(self, color: str = theme.ACCENT_CYAN, max_points: int = 60, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._data = deque(maxlen=max_points)
        self.setMinimumHeight(34)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)



    def push(self, value: float):
        try:
            self._data.append(float(value))
        except (TypeError, ValueError):
            return
        self.update()

    def set_data(self, values):
        """Replace the whole series at once (e.g. a 3-month historical
        pull), rather than appending one live tick at a time."""
        maxlen = self._data.maxlen
        if values and len(values) > maxlen:
            maxlen = len(values)
        self._data = deque(values, maxlen=maxlen)
        self.update()

    def set_color(self, color: str):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())

        if len(self._data) < 2:
            p.setPen(QColor(theme.TEXT_DIM))
            p.drawText(rect, Qt.AlignCenter, "· · ·")
            p.end()
            return

        lo, hi = min(self._data), max(self._data)
        span = (hi - lo) or 1.0
        n = len(self._data)
        step = rect.width() / (n - 1)

        pts = [
            QPointF(i * step, rect.height() - 4 - ((v - lo) / span) * (rect.height() - 8))
            for i, v in enumerate(self._data)
        ]

        # gradient fill under the line
        area = QPainterPath()
        area.moveTo(pts[0].x(), rect.height())
        for pt in pts:
            area.lineTo(pt)
        area.lineTo(pts[-1].x(), rect.height())
        area.closeSubpath()

        grad = QLinearGradient(0, 0, 0, rect.height())
        fill = QColor(self._color)
        fill.setAlpha(90)
        grad.setColorAt(0.0, fill)
        transparent = QColor(self._color)
        transparent.setAlpha(0)
        grad.setColorAt(1.0, transparent)
        p.fillPath(area, grad)

        # line
        line = QPainterPath()
        line.moveTo(pts[0])
        for pt in pts[1:]:
            line.lineTo(pt)
        pen = QPen(self._color)
        pen.setWidthF(1.6)
        p.setPen(pen)
        p.drawPath(line)

        # glow dot on last point
        last = pts[-1]
        p.setPen(Qt.NoPen)
        glow = QColor(self._color)
        glow.setAlpha(70)
        p.setBrush(glow)
        p.drawEllipse(last, 5, 5)
        p.setBrush(self._color)
        p.drawEllipse(last, 2, 2)

        p.end()


class MultiSparkline(QWidget):
    """Overlay of several named series sharing one scale, with a small
    legend. Used for the central 'MARKET PULSE' overview panel."""

    def __init__(self, max_points: int = 90, parent=None):
        super().__init__(parent)
        self._series = {}   # name -> {"color": QColor, "data": deque}
        self._max_points = max_points
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def add_series(self, name: str, color: str):
        self._series[name] = {
            "color": QColor(color),
            "data": deque(maxlen=self._max_points),
        }

    def push(self, name: str, value: float):
        if name not in self._series:
            self.add_series(name, theme.ACCENT_CYAN)
        try:
            self._series[name]["data"].append(float(value))
        except (TypeError, ValueError):
            return
        self.update()

    def set_series_data(self, name: str, values, color: str = None):
        """Replace one series' whole history at once (3-month pull),
        rather than appending one live tick at a time."""
        if name not in self._series:
            self.add_series(name, color or theme.ACCENT_CYAN)
        elif color:
            self._series[name]["color"] = QColor(color)
        self._series[name]["data"] = deque(values, maxlen=self._max_points)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())

        chart_rect = QRectF(rect.left(), rect.top(), rect.width(), rect.height() - 18)

        # background grid (horizontal reference lines)
        grid_pen = QPen(QColor(theme.GRID_LINE))
        grid_pen.setWidthF(1)
        p.setPen(grid_pen)
        for i in range(1, 4):
            y = chart_rect.top() + chart_rect.height() * i / 4
            p.drawLine(QPointF(chart_rect.left(), y), QPointF(chart_rect.right(), y))

        any_series = False
        for name, series in self._series.items():
            data = series["data"]
            if len(data) < 2:
                continue
            any_series = True
            lo, hi = min(data), max(data)
            span = (hi - lo) or 1.0
            n = len(data)
            step = chart_rect.width() / (n - 1)
            pts = [
                QPointF(
                    chart_rect.left() + i * step,
                    chart_rect.bottom() - ((v - lo) / span) * (chart_rect.height() - 6) - 3,
                )
                for i, v in enumerate(data)
            ]
            # -------------------------------
            # Gradient fill under the line
            # -------------------------------
            area = QPainterPath()
            area.moveTo(pts[0].x(), chart_rect.bottom())

            for pt in pts:
                area.lineTo(pt)

            area.lineTo(pts[-1].x(), chart_rect.bottom())
            area.closeSubpath()

            grad = QLinearGradient(
                0,
                chart_rect.top(),
                0,
                chart_rect.bottom()
            )

            fill = QColor(series["color"])
            fill.setAlpha(90)
            grad.setColorAt(0.0, fill)

            transparent = QColor(series["color"])
            transparent.setAlpha(0)
            grad.setColorAt(1.0, transparent)

            p.fillPath(area, grad)

            path = QPainterPath()
            path.moveTo(pts[0])

            for pt in pts[1:]:
                path.lineTo(pt)

            # endpoint
            last = pts[-1]
            p.setBrush(series["color"])
            p.setPen(Qt.NoPen)
            p.drawEllipse(last, 2.2, 2.2)

        # legend row along the bottom
        lx = rect.left()
        ly = rect.bottom() - 8
        f = theme.mono_font(7)
        p.setFont(f)
        for name, series in self._series.items():
            color = series["color"]
            p.setBrush(color)
            p.setPen(Qt.NoPen)
            p.drawRect(QRectF(lx, ly - 6, 7, 7))
            p.setPen(QColor(theme.TEXT_MUTED))
            p.drawText(QPointF(lx + 11, ly), name)
            lx += 11 + p.fontMetrics().horizontalAdvance(name) + 14

        p.end()
