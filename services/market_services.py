from data.index import Index
from data.commodities import Commodities

from database.redis import Redis
from logistics.redis_in_stream import RedisInStream

import time
import sys


def run():

    indices = Index()
    commodities = Commodities()

    redis = Redis()
    redis_client = redis.connect()

    stream = RedisInStream()


    while True:

        index_data = indices.fetch()
        commodity_data = commodities.fetch()

        data = {
            "index": index_data,
            "commodity": commodity_data
        }

        stream.set(
            data,
            redis_client
        )

        time.sleep(60)
        sys.exit(
            run().exec()
        )