from data.historicals.historical_fetcher import HistoricalFetcher

class CurrencyHistory(HistoricalFetcher):

    def __init__(self):

        currencies = {
            'USD / EUR': 'EUR=X',
            'USD / JPY': 'JPY=X',
            'USD / GBP': 'GBP=X',
            'USD / CNY': 'CNY=X',
            'AUD / USD': 'AUDUSD=X',
        }

        super().__init__(
            tickers = currencies,
            asset_class="currency"
        )

    def period(self):
        return "3mo"

    def interval(self):
        return "1d"