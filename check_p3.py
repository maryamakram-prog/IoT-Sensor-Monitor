import os
import dns.resolver
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

load_dotenv()
db = MongoClient(os.getenv("MONGO_URI"))[os.getenv("MONGO_DB", "IoTSensorMonitor")]

now = datetime.now()
seven_days_ago = now - timedelta(days=7)
print("Now:", now)
print("7 days ago:", seven_days_ago)

p3 = list(db.readings.aggregate([
    {
        "$match": {
            "recorded_at": {
                "$gte": seven_days_ago,
                "$lte": now
            },
            "temperature_c": {"$ne": None}
        }
    },
    {
        "$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$recorded_at"}},
            "min_temp": {"$min": "$temperature_c"},
            "max_temp": {"$max": "$temperature_c"},
            "avg_temp": {"$avg": "$temperature_c"},
            "records": {"$sum": 1}
        }
    },
    {"$sort": {"_id": -1}},
    {"$limit": 7}
]))

print(f"Pipeline 3 (Actual last 7 calendar days) returned {len(p3)} date groups:")
for d in p3:
    print(d)
