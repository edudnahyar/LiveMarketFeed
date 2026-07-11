from abc import ABC, abstractmethod

import pandas as pd
import yfinance as yf


class HistoricalFetcher(ABC):

    def __init__(self, tickers: dict, asset_class: str):
        self.tickers = tickers
        self.asset_class = asset_class

    @abstractmethod
    def interval(self):
        """Return yfinance interval."""
        pass

    @abstractmethod
    def period(self):
        """Return yfinance period."""
        pass

    def fetch(self) -> list[dict]:

        data = yf.download(
            tickers=list(self.tickers.values()),
            period=self.period(),
            interval=self.interval(),
            auto_adjust=False,
            progress=False
        )

        documents = []

        for ticker in self.tickers.values():

            ticker_df = data.xs(
                ticker,
                axis=1,
                level=1
            )

            ticker_df = ticker_df.dropna(
                subset=["Close"]
            )

            for timestamp, row in ticker_df.iterrows():

                documents.append({

                    "ticker": ticker,

                    "asset_class": self.asset_class,

                    "interval": self.interval(),

                    "timestamp": timestamp,

                    "open": float(row["Open"]),

                    "high": float(row["High"]),

                    "low": float(row["Low"]),

                    "close": float(row["Close"]),

                    "volume": (
                        None
                        if pd.isna(row["Volume"])
                        else float(row["Volume"])
                    )
                })

        return documents