
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "IoTSensorMonitor")

LATITUDE = 25.3960
LONGITUDE = 68.3578
TIMEZONE = "Asia/Karachi"

START_DATE = "2026-07-01"
END_DATE = "2026-08-31"

SOURCE = "open-meteo-historical"
SENSOR_ID = "SENSOR-WEATHER-HYD-001"


def main():
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI missing. Check .env.")

    print("1. Fetching historical weather data...")

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": "temperature_2m,relative_humidity_2m",
        "timezone": TIMEZONE,
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    hourly = response.json().get("hourly", {})

    times = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    humidities = hourly.get("relative_humidity_2m", [])

    if not times:
        raise RuntimeError("No historical weather records returned.")

    print("2. Records received:", len(times))
    print("3. Connecting to MongoDB Atlas...")

    with MongoClient(MONGO_URI, serverSelectionTimeoutMS=20000) as client:
        client.admin.command("ping")
        db = client[DB_NAME]

        db.sensors.update_one(
            {"sensor_id": SENSOR_ID},
            {"$setOnInsert": {
                "sensor_id": SENSOR_ID,
                "sensor_name": "Hyderabad Historical Weather",
                "sensor_type": "weather",
                "status": "active",
                "data_source": SOURCE,
                "latitude": LATITUDE,
                "longitude": LONGITUDE,
            }},
            upsert=True,
        )

        operations = []

        for i, time_text in enumerate(times):
            temp = temperatures[i]
            humidity = humidities[i]

            if temp is None and humidity is None:
                continue

            recorded_at = datetime.fromisoformat(time_text).replace(
                tzinfo=ZoneInfo(TIMEZONE)
            )
            record_id = f"{SOURCE}:{SENSOR_ID}:{time_text}"

            document = {
                "_id": record_id,
                "sensor_id": SENSOR_ID,
                "location_id": None,
                "temperature_c": temp,
                "humidity_percent": humidity,
                "pm25": None,
                "pm10": None,
                "aqi": None,
                "recorded_at": recorded_at,
                "data_source": SOURCE,
                "data_type": "historical_reanalysis",
                "source_url": "https://open-meteo.com/",
                "latitude": LATITUDE,
                "longitude": LONGITUDE,
            }

            operations.append(
                UpdateOne(
                    {"_id": record_id},
                    {"$set": document},
                    upsert=True,
                )
            )

        if operations:
            result = db.readings.bulk_write(operations, ordered=False)
            print("4. New records inserted:", result.upserted_count)
            print("5. Existing imported records updated:", result.modified_count)

        print("Total readings:", db.readings.count_documents({}))
        print(
            "Historical weather records:",
            db.readings.count_documents({"data_source": SOURCE})
        )
        print("Import completed.")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("IMPORT FAILED:", type(error).__name__, str(error))
