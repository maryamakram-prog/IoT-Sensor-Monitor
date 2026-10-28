
import os
import json
from urllib.request import urlopen
from urllib.parse import urlencode
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Hyderabad, Sindh, Pakistan
LATITUDE = 25.3960
LONGITUDE = 68.3578
CITY = "Hyderabad"
COUNTRY = "Pakistan"

SENSOR_ID = "SENSOR-WEATHER-HYD-001"
LOCATION_ID = "LOC-HYD-001"

mongo_uri = os.getenv("MONGO_URI")
database_name = os.getenv("MONGO_DB", "IoTSensorMonitor")

if not mongo_uri:
    raise RuntimeError(
        "MONGO_URI missing hai. .env file check karo."
    )

client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=15000
)

db = client[database_name]


def fetch_api(url, params):
    full_url = url + "?" + urlencode(params)

    with urlopen(full_url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_hourly_map(data, fields):
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])

    result = {}

    for index, timestamp in enumerate(times):
        row = {}

        for field in fields:
            values = hourly.get(field, [])

            row[field] = (
                values[index]
                if index < len(values)
                else None
            )

        result[timestamp] = row

    return result


def main():
    print("Fetching Hyderabad weather data...")

    weather = fetch_api(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "hourly": (
                "temperature_2m,"
                "relative_humidity_2m"
            ),
            "past_hours": 24,
            "forecast_hours": 24,
            "timezone": "Asia/Karachi"
        }
    )

    print("Fetching Hyderabad air-quality data...")

    air_quality = fetch_api(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "hourly": "pm2_5,pm10,us_aqi",
            "past_hours": 24,
            "forecast_hours": 24,
            "timezone": "Asia/Karachi"
        }
    )

    weather_map = get_hourly_map(
        weather,
        [
            "temperature_2m",
            "relative_humidity_2m"
        ]
    )

    air_map = get_hourly_map(
        air_quality,
        [
            "pm2_5",
            "pm10",
            "us_aqi"
        ]
    )

    # Find or create Hyderabad location.
    location = db.locations.find_one({
        "city": {
            "$regex": "^Hyderabad$",
            "$options": "i"
        },
        "country": {
            "$regex": "^Pakistan$",
            "$options": "i"
        }
    })

    if location:
        location_id = str(
            location.get("location_id")
            or location["_id"]
        )
    else:
        location_doc = {
            "location_id": LOCATION_ID,
            "location_name": "Hyderabad, Sindh",
            "city": CITY,
            "country": COUNTRY,
            "latitude": LATITUDE,
            "longitude": LONGITUDE
        }

        db.locations.insert_one(location_doc)
        location_id = LOCATION_ID

    # Find or create the weather sensor.
    db.sensors.update_one(
        {"sensor_id": SENSOR_ID},
        {
            "$set": {
                "sensor_id": SENSOR_ID,
                "sensor_name": (
                    "Hyderabad Weather and Air Quality API"
                ),
                "sensor_type": "weather",
                "location_id": location_id,
                "status": "active",
                "data_source": "Open-Meteo API"
            },
            "$setOnInsert": {
                "installed_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }
        },
        upsert=True
    )

    inserted_or_updated = 0

    # Combine weather and air quality by timestamp.
    for timestamp, weather_values in weather_map.items():
        air_values = air_map.get(timestamp, {})

        temperature = weather_values.get(
            "temperature_2m"
        )

        humidity = weather_values.get(
            "relative_humidity_2m"
        )

        pm25 = air_values.get("pm2_5")
        pm10 = air_values.get("pm10")
        aqi = air_values.get("us_aqi")

        # Skip rows with no measurements.
        if all(
            value is None
            for value in [
                temperature,
                humidity,
                pm25,
                pm10,
                aqi
            ]
        ):
            continue

        reading = {
            "sensor_id": SENSOR_ID,
            "location_id": location_id,
            "temperature_c": temperature,
            "humidity_percent": humidity,
            "pm25": pm25,
            "pm10": pm10,
            "aqi": aqi,
            "recorded_at": timestamp,
            "data_source": "open-meteo-api",
            "location_name": "Hyderabad, Sindh, Pakistan"
        }

        # Update the same timestamp instead of creating duplicates.
        db.readings.update_one(
            {
                "sensor_id": SENSOR_ID,
                "recorded_at": timestamp
            },
            {"$set": reading},
            upsert=True
        )

        inserted_or_updated += 1

    print("\nImport completed successfully!")
    print("Location: Hyderabad, Sindh, Pakistan")
    print("Data source: Open-Meteo API")
    print("Records inserted/updated:", inserted_or_updated)
    print("Total readings in MongoDB:", db.readings.count_documents({}))
    print("Total sensors:", db.sensors.count_documents({}))

    print(
        "\nNote: Recent observations/model estimates and "
        "forecast data are not physical sensor readings."
    )

    client.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\nImport failed:", error)
        print(
            "Internet connection, MongoDB Atlas access, "
            "and API response check karo."
        )
    finally:
        client.close()
