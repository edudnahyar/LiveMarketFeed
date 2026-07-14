"""
news.py — pulls per-symbol news directly from yfinance (no OpenBB
dependency). Merged into one feed and presented as a single "Global
News" panel in the GUI, rather than segmented by symbol.

yfinance's news endpoint is keyed to an actual Yahoo Finance ticker
page, so it essentially never has articles for raw index tickers
("^GSPC"), FX pairs ("EUR=X"), or futures contracts ("CL=F", "ZN=F") —
those aren't "securities" with their own news tab. Real, liquid,
heavily-covered ETFs/equities are used as proxies for each asset class
instead, so this reliably returns results.

The parsing below (content -> title/clickThroughUrl/pubDate/provider/
summary) mirrors OpenBB's own yfinance news normalization
(openbb_yfinance.models.company_news), since that's just a thin wrapper
around this same yf.Ticker(...).get_news() call — verified against
OpenBB's source rather than guessed.
"""

import yfinance as yf
from datetime import datetime, timezone

DEFAULT_SYMBOLS = [
    "SPY", "EFA", "EEM",            # US / developed intl / emerging market equities
    "USO", "UNG", "GLD", "CPER",    # oil, nat gas, gold, copper (ETF proxies)
    "AAPL", "MSFT",                 # bellwether mega-caps — reliably newsy
]


class News:

    def __init__(self, symbols=None, limit=5):
        self.symbols = symbols or DEFAULT_SYMBOLS
        self.limit = limit

    def fetch(self):
        documents = []
        seen_urls = set()

        for symbol in self.symbols:
            try:
                raw_items = yf.Search(symbol, news_count=self.limit) or []
            except Exception as e:
                # One symbol having no news (or yfinance hiccuping) for a
                # moment shouldn't take down the whole ingest loop.
                print(f"[News] failed to fetch news for {symbol}: {e}")
                continue

            for item in raw_items:
                doc = self._normalize(item, symbol)
                if doc is None or doc["url"] in seen_urls:
                    continue
                seen_urls.add(doc["url"])
                documents.append(doc)

        return documents

    @staticmethod
    def _normalize(item, symbol):
        """Flatten one raw yfinance news item into our document shape.
        Mirrors openbb_yfinance's own normalization logic."""
        if not isinstance(item, dict):
            return None

        content = item.get("content")
        if not isinstance(content, dict):
            return None

        title = content.get("title") or content.get("summary")

        url = None
        click_through = content.get("clickThroughUrl")
        if isinstance(click_through, dict):
            url = click_through.get("url")
        if not url:
            canonical = content.get("canonicalUrl")
            if isinstance(canonical, dict):
                url = canonical.get("url")
        if not url:
            url = content.get("previewUrl")

        published = News._parse_date(content.get("pubDate") or content.get("displayTime"))

        provider = content.get("provider")
        source = provider.get("displayName") if isinstance(provider, dict) else None

        excerpt = content.get("summary") or content.get("description") or ""

        if not (title and url and published):
            return None

        return {
            "symbol": symbol,
            "title": title,
            "source": source,
            "published": published,
            "url": url,
            "description": excerpt,
        }

    @staticmethod
    def _parse_date(raw_date):
        if not raw_date:
            return None
        if isinstance(raw_date, datetime):
            return raw_date
        if isinstance(raw_date, (int, float)):
            # Yahoo has used both second- and millisecond-epoch
            # timestamps across API versions.
            ts = raw_date / 1000 if raw_date > 1e12 else raw_date
            try:
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            except (ValueError, OSError, OverflowError):
                return None
        try:
            # ISO 8601, e.g. "2026-07-11T14:30:00Z"
            return datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
