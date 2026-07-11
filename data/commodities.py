
import yfinance as yf

class Commodities:
    def __init__(self):
        self.commodities = {
            'Oil': 'CL=F',
            'Natural Gas': 'NG=F',
            'Gold': 'GC=F',
            'Copper': 'HG=F',
        }
        self.data = None

    def fetch(self):
        data = yf.download(
            tickers=list(self.commodities.values()),
            period="1d"
        )

        latest = data.iloc[-1]

        output = {}

        for ticker in self.commodities.values():
            output[ticker] = {
                "price": latest["Close", ticker],
                "open": latest["Open", ticker]
            }

        return output