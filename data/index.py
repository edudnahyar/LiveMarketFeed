import yfinance as yf

class Index:
    def __init__(self):
        self.indices = {
            "S&P500": "^GSPC",
            "ASX200": "^AXJO",
            "EuroStoxx": "^STOXX50E",
            "FTSE100": "^FTSE",
            "Hang Seng": "^HSI"
        }

        self.data = None

    def fetch(self):
        data = yf.download(
            tickers=list(self.indices.values()),
            period="1d"
        )

        latest = data.iloc[-1]

        output = {}

        for ticker in self.indices.values():
            output[ticker] = {
                "price": latest["Close", ticker],
                "open": latest["Open", ticker]
            }

        return output