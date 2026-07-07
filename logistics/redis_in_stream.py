
class RedisInStream:
    def set(self, data, db_instance):

        for list_name, tickers in data.items():
            for price in tickers:
                db_instance.hset(f"market:{tickers}",
                                 mapping={
                                     "price": float(price)
                                 })

