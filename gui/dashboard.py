"""
dashboard.py — main window.

Price + %change badges: live, from Redis, same 5s cadence as before.
Sparklines (every card + the Market Pulse overlay): daily closes pulled
from Mongo (see gui/mongo_history.py + Dashboard._load_historicals()),
refreshed on a slower timer since the underlying data is daily bars,
not tick data. The two are intentionally decoupled so the charts don't
jitter on every Redis poll.

A 1W / 1M / 3M toggle on the Market Pulse panel (gui.Widgets.
timeframe_toggle.TimeframeToggle) controls the range for ALL
sparklines app-wide, not just that panel.

    ┌─────────────────────────── top bar (title / clock / link status) ───────────────────────────┐
    │  GLOBAL INDICES        │      MARKET PULSE (overlay chart)      │      COMMODITIES           │
    │  FUTURES               │      GLOBAL ACTIVITY (radar)           │      CURRENCIES            │
    │                        │      WORLD EXCHANGES (clock strip)     │      GLOBAL NEWS           │
    ├────────────────────────────────── ticker tape ───────────────────────────────────────────────┤

Global News: pulled from Mongo (data/news/news.py + Dashboard._load_news()),
same slow-timer pattern as historicals — per-symbol yfinance company
news via OpenBB, merged into one feed. Falls back to placeholder
headlines (_seed_demo_news()) only if Mongo has nothing yet.
"""

import random
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QScrollArea
)
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import QTimer, Qt, QDateTime

import redis

from gui import theme
from gui import mongo_history
from gui.Widgets.frame import HudFrame
from gui.Widgets.marketcard import MarketCard
from gui.Widgets.sparkline import MultiSparkline
from gui.Widgets.ticker import TickerTape
from gui.Widgets.radar import RadarPulse, ExchangeStrip
from gui.Widgets.newsfeed import NewsFeed
from gui.Widgets.timeframe_toggle import TimeframeToggle

DEMO_MODE = True   # seeds News/live-price ticks so the dashboard looks
                    # alive even before those data sources exist.
                    # Indices/Commodities/Currencies/Futures prices
                    # always prefer real Redis data when available;
                    # sparklines always prefer real Mongo historicals.

HISTORY_REFRESH_MS = 5 * 60 * 1000   # Mongo history is daily bars —
                                      # no need to re-query every 5s.

# Approx. trading days per timeframe. Mongo only stores what
# data/historicals/*.py has actually fetched (a rolling 3-month window
# per HistoricalFetcher.period()), but the collection is append-only —
# unique-indexed on (ticker, interval, timestamp) — so history depth
# only grows the longer the ingest service runs. All three of these
# options fit comfortably inside that 3-month window from day one.
TIMEFRAME_TRADING_DAYS = {"1W": 5, "1M": 22, "3M": 66}


class Dashboard(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Live Market Feed")
        self.resize(1440, 860)
        self.setStyleSheet(theme.GLOBAL_QSS)

        self._current_timeframe = "1M"

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
        columns.addWidget(self._build_left_column(), 3)
        columns.addWidget(self._build_center_column(), 4)
        columns.addWidget(self._build_right_column(), 3)
        root.addLayout(columns, 1)

        self.ticker = TickerTape()
        root.addWidget(self.ticker)

        # ---- Mongo connection (read-only, for sparklines + news) ----
        self.mongo_client = mongo_history.get_client()
        self._ticker_for_card = self._build_ticker_map()
        self._seen_news_urls = set()

        # ---- refresh cadence (unchanged: 5s for live price/change) ----
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

        self.history_timer = QTimer(self)
        self.history_timer.timeout.connect(self._load_historicals)
        self.history_timer.start(HISTORY_REFRESH_MS)

        self.news_timer = QTimer(self)
        self.news_timer.timeout.connect(self._load_news)
        self.news_timer.start(HISTORY_REFRESH_MS)

        self._load_historicals()
        if not self._load_news() and DEMO_MODE:
            self._seed_demo_news()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_ticker_map(self):
        """card object -> yfinance ticker, spanning indices/commodities
        (keyed by short name) and currencies/futures (already keyed by
        ticker), so _load_historicals() can loop over one flat dict."""
        ticker_map = {
            self.cards["SP500"]: "^GSPC",
            self.cards["ASX200"]: "^AXJO",
            self.cards["FTSE100"]: "^FTSE",
            self.cards["HSI"]: "^HSI",
            self.cards["EUROSTOXX"]: "^STOXX50E",
            self.cards["Crude Oil"]: "CL=F",
            self.cards["Natural Gas"]: "NG=F",
            self.cards["Gold"]: "GC=F",
            self.cards["Copper"]: "HG=F",
        }
        for ticker, card in self.fx_cards.items():
            ticker_map[card] = ticker
        for ticker, card in self.futures_cards.items():
            ticker_map[card] = ticker
        return ticker_map

    def _load_historicals(self):
        """Pull daily closes from Mongo, at the currently-selected
        timeframe, for every card plus the three Market Pulse series.
        No-op (leaves whatever's already showing) for any ticker Mongo
        has nothing for yet."""
        if self.mongo_client is None:
            self.mongo_client = mongo_history.get_client()
        if self.mongo_client is None:
            return

        limit = TIMEFRAME_TRADING_DAYS.get(self._current_timeframe, 66)

        for card, ticker in self._ticker_for_card.items():
            closes = mongo_history.fetch_close_history(self.mongo_client, ticker, limit=limit)
            if closes:
                card.set_history(closes)

        pulse_tickers = {"SP500": "^GSPC", "ASX200": "^AXJO", "HSI": "^HSI"}
        for name, ticker in pulse_tickers.items():
            closes = mongo_history.fetch_close_history(self.mongo_client, ticker, limit=limit)
            if closes:
                self.pulse.set_series_data(name, closes)

    def _load_news(self) -> bool:
        """Pull the latest news from Mongo (data/news/news.py +
        logistics/mongo_in_stream.py's set_news) and add anything new
        to the Global News panel, oldest-first so the newest article
        ends up on top. Returns True if Mongo had any news at all (even
        if none of it was new since the last check) — used at startup
        to decide whether to fall back to demo headlines."""
        if self.mongo_client is None:
            self.mongo_client = mongo_history.get_client()
        if self.mongo_client is None:
            return False

        docs = mongo_history.fetch_latest_news(self.mongo_client, limit=20)
        if not docs:
            return False

        new_docs = [d for d in docs if d.get("url") and d["url"] not in self._seen_news_urls]
        new_docs.sort(key=lambda d: d.get("published") or datetime.min)

        for doc in new_docs:
            self._seen_news_urls.add(doc["url"])
            self.news.add_news(
                doc.get("title") or "(untitled)",
                doc.get("source") or "",
                doc.get("published"),
            )

        if new_docs:
            self._news_panel.subtitle_label.setText("yfinance company news, via OpenBB")
        return True

    def _seed_demo_news(self):
        """Placeholder headlines shown only until real news arrives from
        Mongo (or indefinitely if Mongo/the news pipeline isn't up)."""
        self._news_panel.subtitle_label.setText("demo feed — waiting on real news source")
        headlines = [
            ("Central bank holds rates steady amid inflation watch", "Reuters"),
            ("Tech shares rally on strong earnings outlook", "Bloomberg"),
            ("Oil slips as demand forecasts are trimmed", "AP"),
            ("Regional manufacturing index beats expectations", "WSJ"),
        ]
        for headline, source in headlines:
            self.news.add_news(headline, source)

    def _on_timeframe_changed(self, label: str):
        self._current_timeframe = label
        points = TIMEFRAME_TRADING_DAYS.get(label, 66)
        self._pulse_panel.subtitle_label.setText(
            f"{label} daily close — applies to all sparklines"
        )
        # Instant feedback from synthetic data (or whatever's cached),
        # then overwritten by real Mongo data a moment later if present.
        self._refresh_demo_history(points)
        self._load_historicals()

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
    def _build_left_column(self):
        wrap = QWidget()
        col = QVBoxLayout(wrap)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(10)

        indices_panel = HudFrame("Global Indices", accent=theme.ACCENT_CYAN,
                                  subtitle="S&P500 · ASX200 · FTSE100 · HSI · STOXX50")
        self.cards = {
            "SP500": MarketCard("S&P 500"),
            "ASX200": MarketCard("ASX 200"),
            "FTSE100": MarketCard("FTSE 100"),
            "HSI": MarketCard("Hang Seng"),
            "EUROSTOXX": MarketCard("EuroStoxx 50"),
        }
        for card in self.cards.values():
            indices_panel.body.addWidget(card)
        indices_panel.body.addStretch(1)

        futures_panel = self._build_futures_panel()

        col.addWidget(indices_panel, 0)
        col.addWidget(futures_panel, 1)
        return wrap

    def _build_futures_panel(self):
        panel = HudFrame("Futures", accent=theme.ACCENT_BLUE,
                          subtitle="rates & FX futures")

        # 10 instruments — scroll rather than stretch the whole dashboard.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 4, 0)
        inner_layout.setSpacing(6)

        # ticker -> short display label (see data/futures.py for the full names)
        futures_labels = {
            "ZN=F": "10Y T-Note Fut",
            "ZF=F": "5Y T-Note Fut",
            "ZT=F": "2Y T-Note Fut",
            "ZB=F": "T-Bond Fut",
            "ZQ=F": "Fed Fund Fut",
            "6E=F": "Euro FX Fut",
            "6B=F": "British FX Fut",
            "6J=F": "Japanese FX Fut",
            "6A=F": "Australian FX Fut",
            "RTY=F": "Russell 2000 Fut",
        }
        self.futures_cards = {}
        for ticker, label in futures_labels.items():
            card = MarketCard(label)
            self.futures_cards[ticker] = card
            inner_layout.addWidget(card)
        inner_layout.addStretch(1)

        scroll.setWidget(inner)
        panel.body.addWidget(scroll)
        return panel

    def _build_right_column(self):
        wrap = QWidget()
        col = QVBoxLayout(wrap)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(10)

        commodities_panel = HudFrame("Commodities", accent=theme.ACCENT_AMBER,
                                      subtitle="Oil · Natural Gas · Gold · Copper")
        self.cards.update({
            "Crude Oil": MarketCard("Crude Oil"),
            "Natural Gas": MarketCard("Natural Gas"),
            "Gold": MarketCard("Gold"),
            "Copper": MarketCard("Copper"),
        })
        for key in ("Crude Oil", "Natural Gas", "Gold", "Copper"):
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
                               subtitle="connecting to news feed…")
        self._news_panel = news_panel
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
                                subtitle="1M daily close — applies to all sparklines")
        self._pulse_panel = pulse_panel

        self.timeframe_toggle = TimeframeToggle(default=self._current_timeframe)
        self.timeframe_toggle.changed.connect(self._on_timeframe_changed)
        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(0, 0, 0, 0)
        toggle_row.addStretch(1)
        toggle_row.addWidget(self.timeframe_toggle)
        pulse_panel.body.addLayout(toggle_row)

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
            "Copper": "market:HG=F",
        }
        fx_redis_keys = {
            "EUR=X": "market:EUR=X",
            "JPY=X": "market:JPY=X",
            "GBP=X": "market:GBP=X",
            "CNY=X": "market:CNY=X",
            "AUDUSD=X": "market:AUDUSD=X",
        }
        futures_redis_keys = {ticker: f"market:{ticker}" for ticker in self.futures_cards}

        try:
            for name, key in redis_keys.items():
                data = self.redis.hgetall(key)
                if data:
                    self.cards[name].update_market(data)
            for name, key in fx_redis_keys.items():
                data = self.redis.hgetall(key)
                if data:
                    self.fx_cards[name].update_market(data)
            for name, key in futures_redis_keys.items():
                data = self.redis.hgetall(key)
                if data:
                    self.futures_cards[name].update_market(data)
            self._set_link_status(True)
        except Exception:
            self._set_link_status(False)
            return

        self._refresh_ticker()

    def _refresh_ticker(self):
        items = []
        all_cards = {**self.cards, **getattr(self, "fx_cards", {}), **getattr(self, "futures_cards", {})}
        for name, card in all_cards.items():
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
        self._commodity_base = {"Crude Oil": 68.4, "Natural Gas": 2.91, "Gold": 2382.0, "Copper": 4.55}

        self._futures_base = {
            "ZN=F": 111.5, "ZF=F": 106.8, "ZT=F": 103.2, "ZB=F": 118.4, "ZQ=F": 95.6,
            "6E=F": 1.0855, "6B=F": 1.2655, "6J=F": 0.00641, "6A=F": 0.6525, "RTY=F": 2145.0,
        }

        # Synthetic daily-close random walk so every chart has something
        # to show before Mongo has real historicals (or when it's
        # unreachable). _load_historicals(), called right after this in
        # __init__, overwrites these with real data if present.
        self._refresh_demo_history(TIMEFRAME_TRADING_DAYS[self._current_timeframe])

    def _refresh_demo_history(self, points: int):
        """(Re)generate synthetic history at the given length. Used at
        startup and whenever the timeframe toggle changes — instant
        visual feedback even before/without a real Mongo pull."""
        bases = {**self._index_base, **self._commodity_base, **self._fx_base, **self._futures_base}
        all_cards = {**self.cards, **self.fx_cards, **self.futures_cards}
        for sym, base in bases.items():
            card = all_cards.get(sym)
            if card is None:
                continue
            card.set_history(self._synthetic_walk(base, points=points))

        for name in ("SP500", "ASX200", "HSI"):
            self.pulse.set_series_data(name, self._synthetic_walk(self._index_base[name], points=points))

    @staticmethod
    def _synthetic_walk(base: float, points: int = 64, step_pct: float = 0.006):
        values = [base]
        for _ in range(points - 1):
            values.append(values[-1] + values[-1] * random.uniform(-step_pct, step_pct))
        return values

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

            for sym, base in self._commodity_base.items():
                new_val = base + base * random.uniform(-0.002, 0.002)
                self._commodity_base[sym] = new_val
                change = (new_val - base) / base * 100
                self.cards[sym].update_market({"price": new_val, "change": change})

            for sym, base in self._futures_base.items():
                new_val = base + base * random.uniform(-0.0015, 0.0015)
                self._futures_base[sym] = new_val
                change = (new_val - base) / base * 100
                self.futures_cards[sym].update_market({"price": new_val, "change": change})

        self._refresh_ticker()
