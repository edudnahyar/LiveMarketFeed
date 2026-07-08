import math

class RedisInStream:
    def set(self, data, db_instance):

        for category, series in data.items():
            for ticker, price in series.items():
                if math.isnan(price):
                    continue
                db_instance.hset(f"market:{ticker}",
                                 mapping={
                                     "category": category,
                                     "price": f"{price:.1f}"
                                 })

