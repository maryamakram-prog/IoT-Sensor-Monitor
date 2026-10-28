
import os
from datetime import datetime, date, timezone

from flask import Flask, jsonify, render_template
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

from crud_routes import crud

# --------------------------------------------------
# 1. FLASK APP AND MONGODB CONNECTION
# --------------------------------------------------

load_dotenv()

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI")
database_name = os.getenv("MONGO_DB", "IoTSensorMonitor")

if not mongo_uri:
    raise RuntimeError(
        "MONGO_URI missing hai. Apni .env file check karo."
    )

client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=10000
)

db = client[database_name]

app.config["mongo_db"] = db
app.register_blueprint(crud)


# --------------------------------------------------
# 2. CONVERT MONGODB VALUES TO JSON-SAFE VALUES
# --------------------------------------------------

def convert_bson(value):
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: convert_bson(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            convert_bson(item)
            for item in value
        ]

    return value


# --------------------------------------------------
# 3. VALIDATE SENSOR MEASUREMENTS
# --------------------------------------------------

def numeric(reading, field):
    value = reading.get(field)

    if isinstance(value, bool):
        return None

    if not isinstance(value, (int, float)):
        return None

    return float(value)


def valid_measurement(reading, field):
    value = numeric(reading, field)

    if value is None:
        return None

    source = str(
        reading.get(
            "data_source",
            reading.get("source", "")
        )
    ).lower()

    sensor_id = str(
        reading.get("sensor_id", "")
    ).upper()

    # Ignore known demo placeholder values.
    # Database documents are not modified.
    if source == "demo":

        if (
            field == "temperature_c"
            and sensor_id == "SENSOR-002"
            and value == 0
        ):
            return None

        if (
            field in ("pm25", "pm10", "aqi")
            and sensor_id == "SENSOR-001"
            and value == 0
        ):
            return None

    # Negative AQI is invalid.
    if field == "aqi" and value < 0:
        return None

    return value


def average(values):
    valid_values = [
        value for value in values
        if value is not None
    ]

    if not valid_values:
        return None

    return round(
        sum(valid_values) / len(valid_values),
        2
    )


# --------------------------------------------------
# 4. AIR QUALITY INDEX CATEGORY
# --------------------------------------------------

def aqi_category(aqi):
    if aqi is None:
        return {
            "category": "Unavailable",
            "risk": "Unknown",
            "message": (
                "No valid AQI measurement is available yet."
            )
        }

    if aqi <= 50:
        return {
            "category": "Good",
            "risk": "Low",
            "message": "Air quality is satisfactory."
        }

    if aqi <= 100:
        return {
            "category": "Moderate",
            "risk": "Moderate",
            "message": (
                "Sensitive people should monitor air quality."
            )
        }

    if aqi <= 150:
        return {
            "category": "Unhealthy for Sensitive Groups",
            "risk": "Elevated",
            "message": (
                "Sensitive groups may experience health effects."
            )
        }

    if aqi <= 200:
        return {
            "category": "Unhealthy",
            "risk": "High",
            "message": (
                "Health effects may occur. "
                "Reduce outdoor exposure."
            )
        }

    if aqi <= 300:
        return {
            "category": "Very Unhealthy",
            "risk": "Very High",
            "message": (
                "Avoid prolonged outdoor exposure."
            )
        }

    return {
        "category": "Hazardous",
        "risk": "Severe",
        "message": (
            "Air quality is hazardous. "
            "Avoid outdoor exposure."
        )
    }


# --------------------------------------------------
# 5. FETCH READINGS
# --------------------------------------------------

def recent_readings(limit=100):
    return list(
        db.readings.find(
            {},
            {"_id": 0}
        ).sort(
            "recorded_at", -1
        ).limit(limit)
    )


def all_readings():
    return list(
        db.readings.find(
            {},
            {"_id": 0}
        ).sort(
            "recorded_at", -1
        )
    )


def clean_readings(readings):
    cleaned = []

    fields = (
        "temperature_c",
        "humidity_percent",
        "pm25",
        "pm10",
        "aqi"
    )

    for item in readings:
        row = dict(item)

        for field in fields:
            value = valid_measurement(row, field)

            if value is not None:
                row[field] = value
            elif field in row:
                row[field] = None

        cleaned.append(row)

    return cleaned


# --------------------------------------------------
# 6. DASHBOARD HOME
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# 7. MONGODB CONNECTION STATUS
# --------------------------------------------------

@app.route("/api/health")
def health():
    try:
        client.admin.command("ping")

        return jsonify({
            "status": "connected",
            "project": "IoT Sensor Monitor",
            "database": database_name,
            "checked_at": datetime.now(
                timezone.utc
            ).isoformat()
        })

    except Exception:
        app.logger.exception(
            "MongoDB connection failed"
        )

        return jsonify({
            "status": "error",
            "message": (
                "MongoDB connection failed. "
                "Check Atlas Network Access, "
                "database user and MONGO_URI."
            )
        }), 500


# --------------------------------------------------
# 8. DASHBOARD COUNTS
# --------------------------------------------------

@app.route("/api/counts")
def counts():
    try:
        total_sensors = db.sensors.count_documents({})
        total_readings = db.readings.count_documents({})
        total_alerts = db.alerts.count_documents({})

        active_sensors = db.sensors.count_documents({
            "status": {
                "$regex": "^active$",
                "$options": "i"
            }
        })

        return jsonify({
            "total_sensors": total_sensors,
            "total_readings": total_readings,
            "total_alerts": total_alerts,
            "active_sensors": active_sensors,
            "inactive_sensors": (
                total_sensors - active_sensors
            )
        })

    except Exception:
        app.logger.exception(
            "Could not load database counts"
        )

        return jsonify({
            "error": "Could not load database counts."
        }), 500


# --------------------------------------------------
# 9. GET ALL SENSORS
# --------------------------------------------------

@app.route("/api/sensors")
def get_sensors():
    try:
        sensors = list(
            db.sensors.find(
                {},
                {"_id": 0}
            ).sort("sensor_id", 1)
        )

        return jsonify(convert_bson(sensors))

    except Exception:
        app.logger.exception(
            "Could not load sensors"
        )

        return jsonify({
            "error": "Could not load sensors."
        }), 500


# --------------------------------------------------
# 10. GET RECENT READINGS
# --------------------------------------------------

@app.route("/api/readings")
def get_readings():
    try:
        readings = recent_readings(100)
        cleaned = clean_readings(readings)

        return jsonify(
            convert_bson(cleaned)
        )

    except Exception:
        app.logger.exception(
            "Could not load readings"
        )

        return jsonify({
            "error": "Could not load readings."
        }), 500


# --------------------------------------------------
# 11. GET ALERTS
# --------------------------------------------------

@app.route("/api/alerts")
def get_alerts():
    try:
        alerts = list(
            db.alerts.find(
                {},
                {"_id": 0}
            ).sort(
                "created_at", -1
            ).limit(100)
        )

        return jsonify(
            convert_bson(alerts)
        )

    except Exception:
        app.logger.exception(
            "Could not load alerts"
        )

        return jsonify({
            "error": "Could not load alerts."
        }), 500


# --------------------------------------------------
# 12. ANALYTICS USING ALL STORED READINGS
# --------------------------------------------------

@app.route("/api/analytics")
def get_analytics():
    try:
        readings = all_readings()

        temperatures = [
            valid_measurement(
                reading, "temperature_c"
            )
            for reading in readings
        ]

        humidities = [
            valid_measurement(
                reading, "humidity_percent"
            )
            for reading in readings
        ]

        aqis = [
            valid_measurement(
                reading, "aqi"
            )
            for reading in readings
        ]

        # Ignore unavailable and zero AQI values.
        valid_aqis = [
            value
            for value in aqis
            if value is not None and value > 0
        ]

        # Readings are sorted newest first.
        latest_aqi = (
            valid_aqis[0]
            if valid_aqis
            else None
        )

        status = aqi_category(latest_aqi)

        return jsonify({
            "total_readings": (
                db.readings.count_documents({})
            ),

            "average_temperature_c": average(
                temperatures
            ),

            "average_humidity_percent": average(
                humidities
            ),

            "average_aqi": average(
                valid_aqis
            ),

            "latest_available_aqi": latest_aqi,

            "aqi_status": status,

            # Frontend compatibility fields
            "aqi_category": status["category"],
            "aqi_risk": status["risk"],
            "aqi_message": status["message"],

            "readings_analyzed": len(readings),

            "note": (
                "Analytics use stored database records. "
                "Historical or demo records are not "
                "necessarily live sensor measurements."
            )
        })

    except Exception:
        app.logger.exception(
            "Could not calculate analytics"
        )

        return jsonify({
            "error": "Could not calculate sensor analytics."
        }), 500


# --------------------------------------------------
# 13. START APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
