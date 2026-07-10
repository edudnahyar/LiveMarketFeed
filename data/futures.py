import yfinance as yf

class Futures:
    def __init__(self):
        self.futures = {
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

        self.data = None

    def fetch(self):
        data = yf.download(tickers = list(self.futures.values()),period = "1d")

        latest = data.iloc[-1]
        output = {}

        for ticker in self.futures.values():
            output[ticker] = {
                "price": latest["Close", ticker],
                "open": latest["Open", ticker]
            }
        return output