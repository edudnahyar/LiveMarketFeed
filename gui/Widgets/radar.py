"""
radar.py — two small "global ops" widgets that stand in for the giant
rotating globe in the reference image without needing real geodata:

  RadarPulse    — animated sweep + randomly-fading blips per exchange,
                  reads like a live "global activity" scope.
  ExchangeStrip — row of world exchanges with an open/closed dot and
                  each city's current local time.
"""

import random
from datetime import datetime, timedelta

from PySide6.QtWidgets import QWidget, QSizePolicy, QHBoxLayout, QLabel, QVBoxLayout
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF

from gui import theme


class RadarPulse(QWidget):

    EXCHANGES = ["NYSE", "LSE", "HKEX", "ASX", "JPX", "EURONEXT"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sweep_angle = 0.0
        self._blips = []   # list of dicts: angle, radius(0-1), age, label
        self.setMinimumHeight(350)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._sweep_timer = QTimer(self)
        self._sweep_timer.timeout.connect(self._tick_sweep)
        self._sweep_timer.start(30)

        self._blip_timer = QTimer(self)
        self._blip_timer.timeout.connect(self._spawn_blip)
        self._blip_timer.start(900)

    def _tick_sweep(self):
        self._sweep_angle = (self._sweep_angle + 2.4) % 360
        # age out blips
        for b in self._blips:
            b["age"] += 1
        self._blips = [b for b in self._blips if b["age"] < 140]
        self.update()

    def _spawn_blip(self):
        self._blips.append({
            "angle": random.uniform(0, 360),
            "radius": random.uniform(0.3, 0.95),
            "age": 0,
            "label": random.choice(self.EXCHANGES),
        })

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        cx, cy = rect.width() / 2, rect.height() / 2
        radius = min(rect.width(), rect.height()) / 2 - 10
        if radius <= 0:
            p.end()
            return

        center = QPointF(cx, cy)

        # concentric rings
        for i in range(1, 4):
            pen = QPen(QColor(theme.BORDER_DIM))
            pen.setWidthF(1)
            p.setPen(pen)
            r = radius * i / 3
            p.drawEllipse(center, r, r)

        # crosshair
        p.setPen(QPen(QColor(theme.BORDER_DIM), 1))
        p.drawLine(QPointF(cx - radius, cy), QPointF(cx + radius, cy))
        p.drawLine(QPointF(cx, cy - radius), QPointF(cx, cy + radius))

        # sweep (a soft wedge, drawn as several fading lines)
        import math
        for i in range(14):
            a = math.radians(self._sweep_angle - i * 2.2)
            alpha = max(0, 90 - i * 7)
            pen = QPen(QColor(theme.ACCENT_CYAN))
            c = QColor(theme.ACCENT_CYAN)
            c.setAlpha(alpha)
            pen.setColor(c)
            pen.setWidthF(1.4)
            p.setPen(pen)
            p.drawLine(center, QPointF(cx + radius * math.cos(a), cy + radius * math.sin(a)))

        # blips
        f = theme.mono_font(7)
        p.setFont(f)
        for b in self._blips:
            a = math.radians(b["angle"])
            r = radius * b["radius"]
            pt = QPointF(cx + r * math.cos(a), cy + r * math.sin(a))
            fade = max(0, 1 - b["age"] / 140)
            color = QColor(theme.ACCENT_AMBER)
            color.setAlpha(int(220 * fade))
            p.setPen(Qt.NoPen)
            p.setBrush(color)
            size = 3 + 2 * (1 - fade)
            p.drawEllipse(pt, size, size)
            if b["age"] < 40:
                label_color = QColor(theme.TEXT_MUTED)
                label_color.setAlpha(int(255 * fade))
                p.setPen(label_color)
                p.drawText(pt + QPointF(6, -4), b["label"])

        p.end()


class ExchangeStrip(QWidget):
    """Row of world exchanges: name, open/closed dot, local time.
    Local time is approximated with fixed UTC offsets so this needs no
    extra dependency (swap in zoneinfo if you want DST accuracy)."""

    _EXCHANGES = [
        ("NYSE", -4, 9, 16),
        ("LSE", 1, 8, 16),
        ("HKEX", 8, 9, 16),
        ("ASX", 10, 10, 16),
        ("JPX", 9, 9, 15),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        self._dots = {}
        self._time_labels = {}

        for name, offset, open_h, close_h in self._EXCHANGES:
            col = QVBoxLayout()
            col.setSpacing(2)

            top = QHBoxLayout()
            top.setSpacing(5)
            dot = QLabel("●")
            dot.setStyleSheet(f"color:{theme.TEXT_DIM}; font-size: 9px;")
            name_lbl = QLabel(name)
            name_lbl.setFont(theme.mono_font(8, bold=True))
            name_lbl.setStyleSheet(f"color:{theme.TEXT_PRIMARY};")
            top.addWidget(dot)
            top.addWidget(name_lbl)
            top.addStretch(1)

            time_lbl = QLabel("--:--")
            time_lbl.setFont(theme.mono_font(9))
            time_lbl.setStyleSheet(f"color:{theme.TEXT_MUTED};")

            col.addLayout(top)
            col.addWidget(time_lbl)
            layout.addLayout(col)

            self._dots[name] = (dot, offset, open_h, close_h)
            self._time_labels[name] = time_lbl

        layout.addStretch(1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(1000)
        self._refresh()

    def _refresh(self):
        utc = datetime.utcnow()
        for name, (dot, offset, open_h, close_h) in self._dots.items():
            local = utc + timedelta(hours=offset)
            self._time_labels[name].setText(local.strftime("%H:%M"))
            is_open = open_h <= local.hour < close_h
            color = theme.ACCENT_GREEN if is_open else theme.TEXT_DIM
            dot.setStyleSheet(f"color:{color}; font-size: 9px;")
