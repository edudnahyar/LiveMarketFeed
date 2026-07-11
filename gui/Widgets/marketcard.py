"""
marketcard.py — compact HUD-style row: symbol name, live price, %change
badge and a mini sparkline.

Price + %change: live, from update_market(data) (Redis).
Sparkline: static-ish, from set_history(values) (Mongo 3-month daily
closes) — see gui/mongo_history.py and Dashboard._load_historicals().
These two are intentionally decoupled: the chart won't jitter on every
5s Redis poll, it only moves when a fresh historical pull comes in.
"""

from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
from collections import deque

from gui import theme
from gui.Widgets.sparkline import Sparkline


class MarketCard(QFrame):

    def __init__(self, title: str, history_len: int = 40, parent=None):
        super().__init__(parent)

        self._last_price = None
        self._history = deque(maxlen=history_len)

        self.setObjectName("MarketCard")
        self.setStyleSheet(f"""
            QFrame#MarketCard {{
                background-color: {theme.BG_PANEL_ALT};
                border: 1px solid {theme.BORDER_DIM};
                border-radius: 2px;
            }}
            QFrame#MarketCard:hover {{
                border: 1px solid {theme.ACCENT_CYAN_DIM};
            }}
        """)

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 6, 10, 6)
        row.setSpacing(10)

        # left: symbol name + big price stacked
        left = QVBoxLayout()
        left.setSpacing(1)

        self.title_label = QLabel(title.upper())
        self.title_label.setFont(theme.mono_font(8))
        self.title_label.setStyleSheet(f"color: {theme.TEXT_MUTED}; letter-spacing: 1px;")

        self.price_label = QLabel("—")
        self.price_label.setFont(theme.mono_font(13, bold=True))
        self.price_label.setStyleSheet(f"color: {theme.TEXT_PRIMARY};")

        left.addWidget(self.title_label)
        left.addWidget(self.price_label)

        # middle: sparkline, stretches
        self.spark = Sparkline(color=theme.ACCENT_CYAN)
        self.spark.setMinimumWidth(70)

        # right: change badge
        self.change_label = QLabel("--")
        self.change_label.setFont(theme.mono_font(10, bold=True))
        self.change_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.change_label.setMinimumWidth(58)
        self.change_label.setStyleSheet(f"color: {theme.TEXT_MUTED};")

        row.addLayout(left, 0)
        row.addWidget(self.spark, 1)
        row.addWidget(self.change_label, 0)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(48)

    # ------------------------------------------------------------------
    def update_market(self, data: dict):
        """Price + %change come from the live Redis feed, same as
        before. The sparkline itself is NOT driven from here anymore —
        see set_history() below, which is fed from the Mongo 3-month
        historicals instead."""

        raw_price = data.get("price")
        try:
            price = float(raw_price)
        except (TypeError, ValueError):
            self.price_label.setText("—")
            return

        open_price = self._safe_float(data.get("open"))

        if open_price is not None and open_price != 0:
            change_pct = ((price - open_price) / open_price) * 100.0
        else:
            change_pct = None

        self._last_price = price
        self._history.append(price)

        self.price_label.setText(f"{price:,.2f}")

        if change_pct is None:
            self.change_label.setText("--")
            self.change_label.setStyleSheet(f"color: {theme.TEXT_MUTED};")
        else:
            sign = "+" if change_pct >= 0 else ""
            self.change_label.setText(f"{sign}{change_pct:.2f}%")
            color = theme.ACCENT_GREEN if change_pct >= 0 else theme.ACCENT_RED
            self.change_label.setStyleSheet(f"color: {color}; font-weight: 600;")
            self.spark.set_color(color)

    def set_history(self, values):
        """Feed the sparkline a 3-month daily-close series pulled from
        Mongo (see gui/mongo_history.py). Independent of update_market()
        so the chart doesn't get overwritten by every 5s Redis tick."""
        self.spark.set_data(values)

    @property
    def history(self):
        return list(self._history)

    @property
    def last_price(self):
        return self._last_price

    @staticmethod
    def _safe_float(v):
        try:
            if v in (None, "--", ""):
                return None
            return float(v)
        except (TypeError, ValueError):
            return None
