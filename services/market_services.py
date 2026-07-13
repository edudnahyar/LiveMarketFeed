from data.historicals.futures_history import FuturesHistory
from data.index import Index
from data.commodities import Commodities
from data.currency import Curency
from data.futures import Futures

from data.historicals.index_history import IndexHistory
from data.historicals.commodity_history import CommodityHistory
from data.historicals.currency_history import CurrencyHistory
from data.historicals.futures_history import FuturesHistory

from data.news.news import News

from database.redis import Redis
from database.pymongo import PyMongo
from logistics.redis_in_stream import RedisInStream
from logistics.mongo_in_stream import MongoInStream

import time
import sys


def run():

    indices = Index()
    commodities = Commodities()
    currencies = Curency()
    futures = Futures()

    index_history = IndexHistory()
    commodity_history = CommodityHistory()
    currency_history = CurrencyHistory()
    future_history = FuturesHistory()

    news = News()

    redis = Redis()
    redis_client = redis.connect()

    mongo = PyMongo()
    mongo_client = mongo.connect()

    stream = RedisInStream()
    hist_stream = MongoInStream()

    # News changes far slower than prices, and each tick fans out to 9
    # separate yfinance calls (one per tracked symbol) — polling that
    # every 60s like the price loop is both wasteful and a good way to
    # get rate-limited. Only fetch news every NEWS_EVERY_N_TICKS loops.
    NEWS_EVERY_N_TICKS = 10   # ~10 minutes at a 60s loop
    tick = 0

    while True:

        index_data = indices.fetch()
        commodity_data = commodities.fetch()
        currency_data = currencies.fetch()
        future_data = futures.fetch()

        index_documents = index_history.fetch()
        commodity_documents = commodity_history.fetch()
        currency_documents = currency_history.fetch()
        future_documents = future_history.fetch()

        data = {
            "index": index_data,
            "commodity": commodity_data,
            "currency": currency_data,
            "future": future_data,
        }

        # MongoInStream.set_historical() -> insert_many() needs a flat
        # list of documents, not a dict keyed by asset class.
        historical_documents = (
            index_documents + commodity_documents + currency_documents + future_documents
        )

        stream.set(
            data,
            redis_client
        )

        if mongo_client is not None and historical_documents:
            hist_stream.set_historical(
                historical_documents,
                mongo_client
            )

        if tick % NEWS_EVERY_N_TICKS == 0:
            news_data = news.fetch()
            if mongo_client is not None and news_data:
                hist_stream.set_news(
                    news_data,
                    mongo_client
                )

        tick += 1
        time.sleep(60)