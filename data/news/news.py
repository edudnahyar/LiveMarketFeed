from openbb import obb

# obb.news.world() only offers benzinga/fmp/intrinio/tiingo as providers —
# all four require a paid API key registered with OpenBB, so "world" news
# isn't usable here without that setup (see https://docs.openbb.co for how
# to add credentials if you get one later, e.g. provider="fmp").
#
# obb.news.company(), on the other hand, DOES support the free "yfinance"
# provider — same one used everywhere else in this app, no signup needed.
# So instead of one "world news" call, this fetches per-symbol company news
# for the instruments already tracked elsewhere (data/index.py,
# data/commodities.py) and merges them into one feed. Currencies/futures
# tickers (e.g. "EUR=X", "ZN=F") are skipped — yfinance's news endpoint
# essentially never has articles attached to those symbols.

DEFAULT_SYMBOLS = [
    "^GSPC", "^AXJO", "^STOXX50E", "^FTSE", "^HSI",   # data/index.py
    "CL=F", "NG=F", "GC=F", "HG=F",                    # data/commodities.py
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
                result = obb.news.company(
                    symbol=symbol,
                    provider="yfinance",
                    limit=self.limit,
                )
                df = result.to_df()
            except Exception as e:
                # One symbol having no news (or yfinance hiccuping) for a
                # a moment shouldn't take down the whole ingest loop.
                print(f"[News] failed to fetch news for {symbol}: {e}")
                continue

            for _, row in df.iterrows():
                url = row.get("url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                excerpt = row.get("excerpt")
                if excerpt is None or excerpt != excerpt:   # NaN != NaN
                    excerpt = ""
                documents.append({
                    "symbol": symbol,
                    "title": row.get("title"),
                    "source": row.get("source"),
                    "published": row.get("date"),
                    "url": url,
                    "description": excerpt,
                })

        return documents