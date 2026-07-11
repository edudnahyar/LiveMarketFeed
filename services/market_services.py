from data.historicals.futures_history import FuturesHistory
from data.index import Index
from data.commodities import Commodities
from data.currency import Curency
from data.futures import Futures

from data.historicals.index_history import IndexHistory
from data.historicals.commodity_history import CommodityHistory
from data.historicals.currency_history import CurrencyHistory
from data.historicals.futures_history import FuturesHistory

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

        data = {
            "index": index_data,
            "commodity": commodity_data,
            "currency": currency_data,
            "future": future_data
        }

        data_hist = {
            "index": index_documents,
            "commodity": commodity_documents,
            "currency": currency_documents,
            "future": future_documents
        }


        stream.set(
            data,
            redis_client
        )

        hist_stream.set_historical(
            data_hist,
            mongo_client
        )

        time.sleep(60)
        sys.exit(
            run().exec()
        )