from pandas.core.interchange.from_dataframe import primitive_column_to_ndarray

from data.index import Index
from data.commodities import Commodities
from data.currency import Curency
from data.futures import Futures

from database.redis import Redis
from database.pymongo import PyMongo
from logistics.redis_in_stream import RedisInStream

import time
import sys


def run():

    indices = Index()
    commodities = Commodities()
    currencies = Curency()
    futures = Futures()

    redis = Redis()
    redis_client = redis.connect()

    mongo = PyMongo()
    mongo_client = mongo.connect()

    stream = RedisInStream()


    while True:

        index_data = indices.fetch()
        commodity_data = commodities.fetch()
        currency_data = currencies.fetch()
        future_data = futures.fetch()

        data = {
            "index": index_data,
            "commodity": commodity_data,
            "currency": currency_data,
            "future": future_data
        }


        stream.set(
            data,
            redis_client
        )

        time.sleep(60)
        sys.exit(
            run().exec()
        )