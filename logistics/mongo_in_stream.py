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

            securities.insert_many(data)

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
