import os
import dns.resolver
from dotenv import load_dotenv
from pymongo import MongoClient

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

load_dotenv()
db = MongoClient(os.getenv("MONGO_URI"))[os.getenv("MONGO_DB", "IoTSensorMonitor")]

pipeline = [
    {
        "$facet": {
            "overall": [
                {
                    "$group": {
                        "_id": None,
                        "total_records": {"$sum": 1},
                        "avg_temp": {"$avg": "$temperature_c"},
                        "min_temp": {"$min": "$temperature_c"},
                        "max_temp": {"$max": "$temperature_c"},
                        "avg_humidity": {"$avg": "$humidity_percent"},
                        "avg_aqi": {"$avg": "$aqi"}
                    }
                }
            ],
            "temp_buckets": [
                {"$match": {"temperature_c": {"$ne": None}}},
                {
                    "$bucket": {
                        "groupBy": "$temperature_c",
                        "boundaries": [0, 20, 30, 40, 60],
                        "default": "other",
                        "output": {"count": {"$sum": 1}}
                    }
                }
            ],
            "latest": [
                {"$sort": {"recorded_at": -1}},
                {"$limit": 1}
            ]
        }
    }
]

res = list(db.readings.aggregate(pipeline))
print("Aggregation completed successfully!")
print("Overall summary:", res[0]["overall"])
print("Temperature buckets:", res[0]["temp_buckets"])
print("Latest document:", res[0]["latest"])
