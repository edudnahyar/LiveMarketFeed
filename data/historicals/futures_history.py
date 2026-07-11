from historical_fetcher import HistoricalFetcher

class FuturesHistory(HistoricalFetcher):
    def __init__(self):

        futures = {
            "10-Year T-Note Futures": "ZN=F",
            "5-Year T-Note Futures": "ZF=F",
            "2-Year T-Note Futures": "ZT=F",
            "T-Bond Futures": "ZB=F",
            "30-day Fed Fund Futures": "ZQ=F",
            "Euro FX Futures": "6E=F",
            "British FX Futures": "6B=F",
            "Japanese FX Futures": "6J=F",
            "Australian FX Futures": "6A=F",
            "E-mini Russell 2000 Futures": "RTY=F",
        }

        super().__init__(
            tickers=futures,
            asset_class="commodity"
        )

    def period(self):
        return "3mo"

    def interval(self):
        return "1d"