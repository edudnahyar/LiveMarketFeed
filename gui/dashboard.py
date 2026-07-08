"""
dashboard.py — main window. Same Redis-backed refresh loop as before
(same keys, same 5s cadence) rebuilt into a cyberdeck-style layout:

    ┌─────────────────────────── top bar (title / clock / link status) ───────────────────────────┐
    │  GLOBAL INDICES        │      MARKET PULSE (overlay chart)      │      COMMODITIES           │
    │  (compact rows)        │      GLOBAL ACTIVITY (radar)           │      CURRENCIES (TODO feed) │
    │                        │      WORLD EXCHANGES (clock strip)     │      GLOBAL NEWS (TODO feed)│
    ├────────────────────────────────── ticker tape ───────────────────────────────────────────────┤

Everything besides Indices/Commodities (which already have a data
pipeline in data/index.py + data/commodities.py) is wired with demo
data behind a DEMO_MODE flag — Currencies and News have no backing
service yet, so their panels are ready to receive real data via
add_news()/update_market() but ship with placeholder ticks until you
add those data sources.
"""

import random

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import QTimer, Qt, QDateTime

import redis

from gui import theme
from gui.Widgets.frame import HudFrame
from gui.Widgets.marketcard import MarketCard
from gui.Widgets.sparkline import MultiSparkline
from gui.Widgets.ticker import TickerTape
from gui.Widgets.radar import RadarPulse, ExchangeStrip
from gui.Widgets.newsfeed import NewsFeed

DEMO_MODE = True   # seeds Currencies/News/Pulse with fake ticks so the
                    # dashboard looks alive even before those data
                    # sources exist. Indices/Commodities always prefer
                    # real Redis data when available.


class Dashboard(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("MARKET CYBERDECK // LIVE FEED")
        self.resize(1440, 860)
        self.setStyleSheet(theme.GLOBAL_QSS)

        # ---- Redis connection (unchanged behaviour from original) ----
        self.redis = None
        self._redis_connected = False
        try:
            self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
            self._redis_connected = bool(self.redis.ping())
        except Exception:
            self._redis_connected = False

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        root.addLayout(self._build_topbar())

        columns = QHBoxLayout()
        columns.setSpacing(10)
        columns.addWidget(self._build_indices_panel(), 3)
        columns.addWidget(self._build_center_column(), 4)
        columns.addWidget(self._build_right_column(), 3)
        root.addLayout(columns, 1)

        self.ticker = TickerTape()
        root.addWidget(self.ticker)

        # ---- refresh cadence (unchanged: 5s for market data) ----
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._tick_clock)
        self.clock_timer.start(1000)
        self._tick_clock()

        if DEMO_MODE:
            self.demo_timer = QTimer(self)
            self.demo_timer.timeout.connect(self._demo_tick)
            self.demo_timer.start(2000)
            self._seed_demo()

        self.refresh()

    # ------------------------------------------------------------------
    # background grid, matches the reference image's faint graph-paper backdrop
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(theme.BG_APP))
        pen = QPen(QColor(theme.GRID_LINE))
        pen.setWidthF(1)
        p.setPen(pen)
        step = 28
        for x in range(0, self.width(), step):
            p.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            p.drawLine(0, y, self.width(), y)
        p.end()

    # ------------------------------------------------------------------
    def _build_topbar(self):
        bar = QHBoxLayout()
        bar.setSpacing(14)

        title = QLabel(theme.spaced("Global Markets"))
        title.setFont(theme.display_font(18, bold=True))
        title.setStyleSheet(f"color: {theme.ACCENT_CYAN};")

        subtitle = QLabel(theme.spaced("Live Cyberdeck Feed", gap=" "))
        subtitle.setFont(theme.mono_font(8))
        subtitle.setStyleSheet(f"color: {theme.TEXT_MUTED};")

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        bar.addLayout(title_col)
        bar.addStretch(1)

        self.status_dot = QLabel("●")
        self.status_label = QLabel("LINK")
        self.status_label.setFont(theme.mono_font(9, bold=True))
        self._set_link_status(self._redis_connected)

        self.clock_label = QLabel("--:--:--")
        self.clock_label.setFont(theme.mono_font(13, bold=True))
        self.clock_label.setStyleSheet(f"color: {theme.TEXT_PRIMARY};")

        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status_label)

        right_col = QVBoxLayout()
        right_col.setSpacing(2)
        right_col.addLayout(status_row)
        right_col.addWidget(self.clock_label, 0, Qt.AlignRight)

        bar.addLayout(right_col)
        return bar

    def _set_link_status(self, connected: bool):
        color = theme.ACCENT_GREEN if connected else theme.ACCENT_RED
        text = "REDIS LINK OK" if connected else "REDIS OFFLINE"
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 10px;")
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    def _tick_clock(self):
        now = QDateTime.currentDateTime()
        self.clock_label.setText(now.toString("HH:mm:ss") + "  UTC" + now.toString("zzz")[:0])

    # ------------------------------------------------------------------
    def _build_indices_panel(self):
        panel = HudFrame("Global Indices", accent=theme.ACCENT_CYAN,
                          subtitle="S&P500 · ASX200 · FTSE100 · HSI · STOXX50")

        self.cards = {
            "SP500": MarketCard("S&P 500"),
            "ASX200": MarketCard("ASX 200"),
            "FTSE100": MarketCard("FTSE 100"),
            "HSI": MarketCard("Hang Seng"),
            "EUROSTOXX": MarketCard("EuroStoxx 50"),
        }
        for card in self.cards.values():
            panel.body.addWidget(card)
        panel.body.addStretch(1)
        return panel

    def _build_right_column(self):
        wrap = QWidget()
        col = QVBoxLayout(wrap)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(10)

        commodities_panel = HudFrame("Commodities", accent=theme.ACCENT_AMBER,
                                      subtitle="Oil · Natural Gas · Gold")
        self.cards.update({
            "Crude Oil": MarketCard("Crude Oil"),
            "Natural Gas": MarketCard("Natural Gas"),
            "Gold": MarketCard("Gold"),
        })
        for key in ("Crude Oil", "Natural Gas", "Gold"):
            commodities_panel.body.addWidget(self.cards[key])
        commodities_panel.body.addStretch(1)

        currencies_panel = HudFrame("Currencies", accent=theme.ACCENT_AMBER,
                                     subtitle="USD/EUR · USD/JPY · USD/GBP · USD/CNY · AUD/USD")
        self.fx_cards = {
            "EUR=X": MarketCard("USD / EUR"),
            "JPY=X": MarketCard("USD / JPY"),
            "GBP=X": MarketCard("USD / GBP"),
            "CNY=X": MarketCard("USD / CNY"),
            "AUDUSD=X": MarketCard("AUD / USD"),
        }
        for card in self.fx_cards.values():
            currencies_panel.body.addWidget(card)
        currencies_panel.body.addStretch(1)

        news_panel = HudFrame("Global News", accent=theme.ACCENT_RED,
                               subtitle="demo feed — hook up your news source")
        self.news = NewsFeed()
        news_panel.body.addWidget(self.news)

        col.addWidget(commodities_panel, 2)
        col.addWidget(currencies_panel, 2)
        col.addWidget(news_panel, 3)
        return wrap

    def _build_center_column(self):
        wrap = QWidget()
        col = QVBoxLayout(wrap)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(10)

        pulse_panel = HudFrame("Market Pulse", accent=theme.ACCENT_CYAN,
                                subtitle="normalized overlay — all tracked instruments")
        self.pulse = MultiSparkline()
        for name, color in (
            ("SP500", theme.ACCENT_CYAN),
            ("ASX200", theme.ACCENT_AMBER),
            ("HSI", theme.ACCENT_BLUE),
        ):
            self.pulse.add_series(name, color)
        pulse_panel.body.addWidget(self.pulse)

        radar_panel = HudFrame("Global Activity", accent=theme.ACCENT_CYAN,
                                subtitle="live order-flow pulses by venue")
        self.radar = RadarPulse()
        radar_panel.body.addWidget(self.radar)

        exchanges_panel = HudFrame("World Exchanges", accent=theme.ACCENT_CYAN)
        self.exchange_strip = ExchangeStrip()
        exchanges_panel.body.addWidget(self.exchange_strip)

        col.addWidget(pulse_panel, 3)
        col.addWidget(radar_panel, 3)
        col.addWidget(exchanges_panel, 1)
        return wrap

    # ------------------------------------------------------------------
    # Real data path — same Redis keys / cadence as the original dashboard.
    def refresh(self):
        if self.redis is None:
            self._set_link_status(False)
            return

        redis_keys = {
            "SP500": "market:^GSPC",
            "ASX200": "market:^AXJO",
            "FTSE100": "market:^FTSE",
            "HSI": "market:^HSI",
            "EUROSTOXX": "market:^STOXX50E",
            "Crude Oil": "market:CL=F",
            "Natural Gas": "market:NG=F",
            "Gold": "market:GC=F",
        }
        fx_redis_keys = {
            "EUR=X": "market:EUR=X",
            "JPY=X": "market:JPY=X",
            "GBP=X": "market:GBP=X",
            "CNY=X": "market:CNY=X",
            "AUDUSD=X": "market:AUDUSD=X",
        }

        try:
            for name, key in redis_keys.items():
                data = self.redis.hgetall(key)
                if data:
                    self.cards[name].update_market(data)
            for name, key in fx_redis_keys.items():
                data = self.redis.hgetall(key)
                if data:
                    self.fx_cards[name].update_market(data)
            self._set_link_status(True)
        except Exception:
            self._set_link_status(False)
            return

        # feed the overview chart + ticker from whatever cards have data
        for name in ("SP500", "ASX200", "HSI"):
            if self.cards[name].last_price is not None:
                self.pulse.push(name, self.cards[name].last_price)

        self._refresh_ticker()

    def _refresh_ticker(self):
        items = []
        for name, card in {**self.cards, **getattr(self, "fx_cards", {})}.items():
            if card.last_price is None:
                continue
            label = card.title_label.text()
            change_txt = card.change_label.text()
            color = theme.ACCENT_GREEN if change_txt.startswith("+") else (
                theme.ACCENT_RED if change_txt.startswith("-") else theme.TEXT_MUTED)
            items.append((label, f"{card.last_price:,.2f} ({change_txt})", color))
        self.ticker.set_items(items)

    # ------------------------------------------------------------------
    # Demo data for panels with no backing service yet (Currencies, News).
    # Safe to delete once you wire real feeds in.
    def _seed_demo(self):
        # Only used as a stand-in when Redis/the market_services pipeline
        # isn't running, so the layout is still fully testable on its own.
        self._fx_base = {
            "EUR=X": 0.9215, "JPY=X": 156.20, "GBP=X": 0.7905,
            "CNY=X": 7.185, "AUDUSD=X": 0.6520,
        }
        self._index_base = {
            "SP500": 5460.0, "ASX200": 7920.0, "FTSE100": 8210.0,
            "HSI": 18340.0, "EUROSTOXX": 4950.0,
        }
        self._commodity_base = {"Crude Oil": 68.4, "Natural Gas": 2.91, "Gold": 2382.0}

        headlines = [
            ("Central bank holds rates steady amid inflation watch", "Reuters"),
            ("Tech shares rally on strong earnings outlook", "Bloomberg"),
            ("Oil slips as demand forecasts are trimmed", "AP"),
            ("Regional manufacturing index beats expectations", "WSJ"),
        ]
        for headline, source in headlines:
            self.news.add_news(headline, source)

    def _demo_tick(self):
        # Indices/commodities/currencies only get demo ticks while the real
        # Redis feed is unavailable, so this steps aside the moment your
        # pipeline is up and pushing real hashes.
        if not self._redis_connected:
            for sym, base in self._fx_base.items():
                new_val = base + base * random.uniform(-0.0015, 0.0015)
                self._fx_base[sym] = new_val
                change = (new_val - base) / base * 100
                self.fx_cards[sym].update_market({"price": new_val, "change": change})

            for sym, base in self._index_base.items():
                new_val = base + base * random.uniform(-0.001, 0.001)
                self._index_base[sym] = new_val
                change = (new_val - base) / base * 100
                self.cards[sym].update_market({"price": new_val, "change": change})
                if sym in ("SP500", "ASX200", "HSI"):
                    self.pulse.push(sym, new_val)

            for sym, base in self._commodity_base.items():
                new_val = base + base * random.uniform(-0.002, 0.002)
                self._commodity_base[sym] = new_val
                change = (new_val - base) / base * 100
                self.cards[sym].update_market({"price": new_val, "change": change})

        self._refresh_ticker()
