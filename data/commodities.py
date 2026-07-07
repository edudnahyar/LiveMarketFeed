import yfinance as yf

class Commodities:
    def __init__(self):
        self.commodities = {
            'Oil': 'CL=F',
            'Natural Gas': 'NG=F',
            'Gold': 'GC=F',
        }
        self.data = None

    def fetch(self):
        data = yf.download(tickers=list(self.commodities.values()), period='1d')
        data = data["Close"].iloc[-1]
        return data