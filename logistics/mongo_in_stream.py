import pymongo


class MongoInStream:
    @staticmethod
    def set_historical(data, db_instance):

            markets = db_instance["markets"]
            securities = markets["securities"]

            securities.create_index(
                [
                    ("ticker", 1),
                    ("interval", 1),
                    ("timestamp", 1)
                ],
                unique=True
            )

            # The same 3-month range gets re-fetched every loop tick, so
            # most documents on any run after the first are duplicates of
            # what's already stored. ordered=False lets Mongo skip past
            # the duplicate-key errors and still insert whatever's new
            # (e.g. today's freshly-closed bar) instead of raising and
            # killing the whole ingest loop.
            try:
                securities.insert_many(data, ordered=False)
            except pymongo.errors.BulkWriteError as e:
                write_errors = e.details.get("writeErrors", [])
                non_duplicate_errors = [we for we in write_errors if we.get("code") != 11000]
                if non_duplicate_errors:
                    raise

    @staticmethod
    def set_news(data, db_instance):

        markets = db_instance["markets"]
        news = markets["news"]

        news.create_index(
            [
                ("ticker", 1),
            ],
            unique=True
        )
        news.insert_many(data)
