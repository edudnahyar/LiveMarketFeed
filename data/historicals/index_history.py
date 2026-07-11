from historical_fetcher import HistoricalFetcher


class IndexHistory(HistoricalFetcher):

    def __init__(self):

        indices = {
            "S&P500": "^GSPC",
            "ASX200": "^AXJO",
            "FTSE100": "^FTSE"
        }

        super().__init__(
            tickers=indices,
            asset_class="index"
        )

    def period(self):
        return "3mo"

    def interval(self):
        return "1d"