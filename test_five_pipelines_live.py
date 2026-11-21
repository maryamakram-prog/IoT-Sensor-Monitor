import os
from datetime import datetime, timedelta
import dns.resolver
from dotenv import load_dotenv
from pymongo import MongoClient

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

load_dotenv()
db = MongoClient(os.getenv("MONGO_URI"))[os.getenv("MONGO_DB", "IoTSensorMonitor")]

print("=== TOTAL DOCUMENT COUNTS IN MONGODB ATLAS ===")
total_docs = db.readings.count_documents({})
print(f"Total documents in 'readings': {total_docs}")
print(f"Total documents in 'sensors': {db.sensors.count_documents({})}")
print(f"Total documents in 'locations': {db.locations.count_documents({})}")
print(f"Total documents in 'alerts': {db.alerts.count_documents({})}")
print(f"Total documents in 'maintenance_logs': {db.maintenance_logs.count_documents({})}")
print(f"Total documents in 'sensor_readings_ts': {db.sensor_readings_ts.count_documents({})}")

print("\n--- PIPELINE 1: Avg Temp & Humidity by Sensor (Excluding Demo Records) ---")
p1 = list(db.readings.aggregate([
    {
        "$match": {
            "temperature_c": {"$ne": None},
            "data_source": {"$ne": "demo"}
        }
    },
    {
        "$group": {
            "_id": "$sensor_id",
            "avg_temperature": {"$avg": "$temperature_c"},
            "avg_humidity": {"$avg": "$humidity_percent"},
            "total_records": {"$sum": 1}
        }
    }
]))
for doc in p1:
    print(" ", doc)

print("\n--- PIPELINE 2: Hourly Record Counts Distribution ($hour) ---")
p2 = list(db.readings.aggregate([
    {"$match": {"recorded_at": {"$ne": None}}},
    {
        "$group": {
            "_id": {"$hour": "$recorded_at"},
            "record_count": {"$sum": 1}
        }
    },
    {"$sort": {"_id": 1}}
]))
for doc in p2[:5]:
    print(" ", doc)
print(f"  ... Total hourly buckets: {len(p2)}")

print("\n--- PIPELINE 3: Daily Temperature Summary (Actual Last 7 Calendar Days) ---")
now = datetime.now()
seven_days_ago = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
print(f"  Date Filter Range: {seven_days_ago} to {now}")

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
            "min_temperature": {"$min": "$temperature_c"},
            "max_temperature": {"$max": "$temperature_c"},
            "avg_temperature": {"$avg": "$temperature_c"},
            "records": {"$sum": 1}
        }
    },
    {"$sort": {"_id": -1}},
    {"$limit": 7}
]))
for doc in p3:
    print(" ", doc)

print("\n--- PIPELINE 4: Temperature Bucketing ($bucket) ---")
p4 = list(db.readings.aggregate([
    {"$match": {"temperature_c": {"$ne": None}}},
    {
        "$bucket": {
            "groupBy": "$temperature_c",
            "boundaries": [0, 20, 30, 40, 60],
            "default": "other",
            "output": {"records": {"$sum": 1}}
        }
    }
]))
for doc in p4:
    print(" ", doc)

print("\n--- PIPELINE 5: Humidity Distribution Bucketing ($bucket with $avg) ---")
p5 = list(db.readings.aggregate([
    {"$match": {"humidity_percent": {"$ne": None}}},
    {
        "$bucket": {
            "groupBy": "$humidity_percent",
            "boundaries": [0, 25, 50, 75, 101],
            "default": "other",
            "output": {
                "records": {"$sum": 1},
                "avg_humidity": {"$avg": "$humidity_percent"}
            }
        }
    }
]))
for doc in p5:
    print(" ", doc)
