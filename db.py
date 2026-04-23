"""
MongoDB connection and collection setup for CloudGuard.

Set MONGODB_URI in your environment to override the default localhost URL.
Indexes are created lazily on first use so the app can still start when
MongoDB is unreachable (useful for tests / offline development).
"""

import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError

MONGO_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("MONGODB_DB", "opmonitor")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
db = client[DB_NAME]

logs_collection = db["logs"]
rules_collection = db["rules"]
configs_collection = db["configs"]

_indexes_created = False


def ensure_indexes():
    """Create indexes once. Called lazily so import doesn't fail offline."""
    global _indexes_created
    if _indexes_created:
        return
    try:
        logs_collection.create_index("userId")
        logs_collection.create_index("action")
        logs_collection.create_index("resource")

        rules_collection.create_index("userId")
        rules_collection.create_index("action")

        configs_collection.create_index("name")
        configs_collection.create_index("config_type")
        configs_collection.create_index("environment")
        configs_collection.create_index("risk_level")
        configs_collection.create_index("analyzed")
        configs_collection.create_index("uploaded_at")
        _indexes_created = True
    except PyMongoError as e:
        # Don't crash on import if Mongo is unavailable.
        print(f"[db] Warning: could not create indexes ({e}). Will retry later.")


# Try once at import — but don't fail if Mongo is down.
try:
    ensure_indexes()
except Exception as e:
    print(f"[db] Warning: index setup deferred ({e})")
