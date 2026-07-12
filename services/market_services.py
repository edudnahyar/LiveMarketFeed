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


    while True:

        index_data = indices.fetch()
        commodity_data = commodities.fetch()
        currency_data = currencies.fetch()
        future_data = futures.fetch()

        index_documents = index_history.fetch()
        commodity_documents = commodity_history.fetch()
        currency_documents = currency_history.fetch()
        future_documents = future_history.fetch()

        news_data = news.fetch()

        data = {
            "index": index_data,
            "commodity": commodity_data,
            "currency": currency_data,
            "future": future_data,
        }

        # MongoInStream.set_historical() -> insert_many() needs a flat
        # list of documents, not a dict keyed by asset class.
        historical_documents = (
            index_documents + commodity_documents + currency_documents + future_documents + news_data
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

        time.sleep(60)