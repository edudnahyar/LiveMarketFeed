"""
mongo_history.py — read-only helper the GUI uses to pull 3-month daily
closes out of the `markets.securities` collection that
services/market_services.py populates via data/historicals/*.py and
logistics/mongo_in_stream.py.

Deliberately independent of database/pymongo.py, which is the
service-side connectivity check/writer (it has test-insert side
effects that have no place in a read path). This just opens its own
short-timeout read client.
"""

import pymongo

MONGO_HOST = "localhost"
MONGO_PORT = 27017
DB_NAME = "markets"
COLLECTION_NAME = "securities"
NEWS_COLLECTION_NAME = "news"


def get_client(timeout_ms: int = 1500):
    """Returns a MongoClient, or None if Mongo isn't reachable. Doesn't
    raise — callers can treat None as 'no historicals available yet'."""
    try:
        client = pymongo.MongoClient(
            host=MONGO_HOST, port=MONGO_PORT,
            serverSelectionTimeoutMS=timeout_ms,
        )
        client.admin.command("ping")
        return client
    except Exception:
        return None


def fetch_close_history(client, ticker: str, interval: str = "1d", limit: int = 90):
    """Ascending list of closing prices for the most recent `limit` bars
    stored for `ticker`. Empty list if Mongo is unreachable or nothing
    has been ingested yet for that ticker — callers should treat that as
    'no chart yet', not an error."""
    if client is None:
        return []
    try:
        collection = client[DB_NAME][COLLECTION_NAME]
        cursor = (
            collection.find(
                {"ticker": ticker, "interval": interval},
                {"_id": 0, "close": 1, "timestamp": 1},
            )
            .sort("timestamp", -1)
            .limit(limit)
        )
        docs = list(cursor)
        docs.reverse()  # ascending chronological order for charting
        return [d["close"] for d in docs if "close" in d]
    except Exception:
        return []


def fetch_latest_news(client, limit: int = 20):
    """Most recent news documents (see data/news/news.py +
    logistics/mongo_in_stream.py's set_news), newest first. Empty list
    if Mongo is unreachable or nothing's been ingested yet."""
    if client is None:
        return []
    try:
        collection = client[DB_NAME][NEWS_COLLECTION_NAME]
        cursor = (
            collection.find({}, {"_id": 0})
            .sort("published", -1)
            .limit(limit)
        )
        return list(cursor)
    except Exception:
        return []
