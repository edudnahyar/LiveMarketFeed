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
        data = yf.download(tickers=list(self.currencies.keys()), period='1d', interval='3s')
        data = data["Close"].iloc[-1]
        return data