import math

class RedisInStream:
    def set(self, data, db_instance):

        for category, series in data.items():
            for ticker, values in list(series.items()):

                price = values["price"]
                open_price = values["open"]

                if math.isnan(price):
                    continue

                db_instance.hset(
                    f"market:{ticker}",
                    mapping={
                        "category": category,
                        "price": f"{price:.2f}",
                        "open": f"{open_price:.2f}"
                    }
                )

