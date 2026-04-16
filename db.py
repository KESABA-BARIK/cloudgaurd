from pymongo import MongoClient

# Connection
client = MongoClient("mongodb://localhost:27017/")

# Database
db = client["opmonitor"]

# Collections
logs_collection = db["logs"]
rules_collection = db["rules"]
configs_collection = db["configs"]

# Indexes (IMPORTANT for performance)
logs_collection.create_index("userId")
logs_collection.create_index("action")
logs_collection.create_index("resource")

rules_collection.create_index("userId")
rules_collection.create_index("action")

# Config collection indexes
configs_collection.create_index("name")
configs_collection.create_index("config_type")
configs_collection.create_index("environment")
configs_collection.create_index("risk_level")
configs_collection.create_index("analyzed")
configs_collection.create_index("uploaded_at")