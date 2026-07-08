import yfinance as yf

class Curency:
    def __init__(self):
        self.currencies = {
            'USD / EUR': 'EUR=X',
            'USD / JPY': 'JPY=X',
            'USD / GBP': 'GBP=X',
            'USD / CNY': 'CNY=X',
            'AUD / USD': 'AUDUSD=X',
        }
        self.data = None

    def fetch(self):
        data = yf.download(
            tickers=list(self.currencies.values()),
            period="1d"
        )

        latest = data.iloc[-1]

        output = {}

        for ticker in self.currencies.values():
            output[ticker] = {
                "price": latest["Close", ticker],
                "open": latest["Open", ticker]
            }

        return output