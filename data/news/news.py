from openbb import obb


class News:

    def __init__(self, limit=20):
        self.limit = limit

    def fetch(self, symbol=None):

        if symbol:
            result = obb.news.company(
                symbol=symbol,
                limit=self.limit
            )
        else:
            result = obb.news.world(
                limit=self.limit
            )

        df = result.to_df()

        return [
            {
                "symbol": symbol,
                "title": row["title"],
                "source": row["source"],
                "published": row["published"],
                "url": row["url"],
                "description": row.get("description", "")
            }
            for _, row in df.iterrows()
        ]