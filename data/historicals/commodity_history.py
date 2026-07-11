from data.historicals.historical_fetcher import HistoricalFetcher


class CommodityHistory(HistoricalFetcher):

    def __init__(self):

        commodities = {
            "Oil": "CL=F",
            "Natural Gas": "NG=F",
            "Gold": "GC=F",
            "Copper": "HG=F"
        }

        super().__init__(
            tickers=commodities,
            asset_class="commodity"
        )

    def period(self):
        return "3mo"

    def interval(self):
        return "1d"