
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "IoTSensorMonitor")


def main():
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is missing from .env")

    with MongoClient(MONGO_URI, serverSelectionTimeoutMS=20000) as client:
        client.admin.command("ping")
        db = client[DB_NAME]
        readings = db.readings

        pipelines = [
            (
                "1. Average temperature and humidity",
                [
                    {"$match": {"data_source": "open-meteo-historical"}},
                    {"$group": {
                        "_id": "$sensor_id",
                        "avg_temperature": {"$avg": "$temperature_c"},
                        "avg_humidity": {"$avg": "$humidity_percent"},
                        "records": {"$sum": 1}
                    }}
                ]
            ),
            (
                "2. Hourly record counts",
                [
                    {"$match": {"data_source": "open-meteo-historical"}},
                    {"$group": {
                        "_id": {"$hour": "$recorded_at"},
                        "records": {"$sum": 1}
                    }},
                    {"$sort": {"_id": 1}}
                ]
            ),
            (
                "3. Daily temperature summary",
                [
                    {"$match": {"data_source": "open-meteo-historical"}},
                    {"$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$recorded_at"
                            }
                        },
                        "min_temperature": {"$min": "$temperature_c"},
                        "max_temperature": {"$max": "$temperature_c"},
                        "avg_temperature": {"$avg": "$temperature_c"},
                        "records": {"$sum": 1}
                    }},
                    {"$sort": {"_id": 1}},
                    {"$limit": 10}
                ]
            ),
            (
                "4. Temperature category counts",
                [
                    {"$match": {
                        "data_source": "open-meteo-historical",
                        "temperature_c": {"$ne": None}
                    }},
                    {"$bucket": {
                        "groupBy": "$temperature_c",
                        "boundaries": [0, 20, 30, 40, 60],
                        "default": "outside_ranges",
                        "output": {"records": {"$sum": 1}}
                    }}
                ]
            ),
            (
                "5. Humidity distribution",
                [
                    {"$match": {
                        "data_source": "open-meteo-historical",
                        "humidity_percent": {"$ne": None}
                    }},
                    {"$bucket": {
                        "groupBy": "$humidity_percent",
                        "boundaries": [0, 25, 50, 75, 101],
                        "default": "outside_ranges",
                        "output": {
                            "records": {"$sum": 1},
                            "avg_humidity": {"$avg": "$humidity_percent"}
                        }
                    }}
                ]
            )
        ]

        for title, pipeline in pipelines:
            print("\n" + "=" * 60)
            print(title)
            print("=" * 60)

            results = list(readings.aggregate(pipeline))
            if not results:
                print("No matching records.")
            else:
                for row in results[:10]:
                    print(row)

        print("\nAll five aggregation pipelines executed.")
        print("No documents were inserted, updated, or deleted.")


if __name__ == "__main__":
    main()
