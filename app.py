
import os
from datetime import datetime, date

from flask import Flask, jsonify, render_template
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

from crud_routes import crud

load_dotenv()

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI")
database_name = os.getenv("MONGO_DB", "IoTSensorMonitor")

if not mongo_uri:
    raise RuntimeError(
        "MONGO_URI is missing. Please check your .env file."
    )

client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=10000
)

db = client[database_name]

# Make the existing MongoDB database available to CRUD routes.
app.config["mongo_db"] = db
app.register_blueprint(crud)


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
        return [convert_bson(item) for item in value]

    return value


def get_number(reading, field):
    value = reading.get(field)

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value

    return None


def average(values):
    valid_values = [
        value for value in values
        if value is not None and value != 0
    ]

    if not valid_values:
        return None

    return round(sum(valid_values) / len(valid_values), 2)


def get_aqi_category(aqi):
    if aqi is None:
        return {
            "category": "No Data",
            "risk": "Unknown",
            "message": "No non-zero AQI reading is available."
        }

    if aqi <= 50:
        category = "Good"
        risk = "Low"
        message = "Air quality is satisfactory."
    elif aqi <= 100:
        category = "Moderate"
        risk = "Moderate"
        message = "Sensitive people should monitor air quality."
    elif aqi <= 150:
        category = "Unhealthy for Sensitive Groups"
        risk = "Elevated"
        message = "Sensitive groups may experience health effects."
    elif aqi <= 200:
        category = "Unhealthy"
        risk = "High"
        message = "Health effects may occur; reduce outdoor exposure."
    elif aqi <= 300:
        category = "Very Unhealthy"
        risk = "Very High"
        message = "Avoid prolonged outdoor exposure."
    else:
        category = "Hazardous"
        risk = "Severe"
        message = "Health alert: avoid outdoor exposure."

    return {
        "category": category,
        "risk": risk,
        "message": message
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health")
def health():
    try:
        client.admin.command("ping")

        return jsonify({
            "status": "connected",
            "project": "IoT Sensor Monitor",
            "database": database_name
        })

    except Exception:
        app.logger.exception("MongoDB connection failed")

        return jsonify({
            "status": "error",
            "message": (
                "MongoDB connection failed. "
                "Check Atlas settings and your .env file."
            )
        }), 500


@app.route("/api/sensors")
def get_sensors():
    try:
        sensors = list(db.sensors.find({}, {"_id": 0}))
        return jsonify(convert_bson(sensors))

    except Exception:
        app.logger.exception("Could not load sensors")
        return jsonify({"error": "Could not load sensors."}), 500


@app.route("/api/readings")
def get_readings():
    try:
        readings = list(
            db.readings.find({}, {"_id": 0})
            .sort("recorded_at", -1)
            .limit(100)
        )
        return jsonify(convert_bson(readings))

    except Exception:
        app.logger.exception("Could not load readings")
        return jsonify({"error": "Could not load readings."}), 500


@app.route("/api/alerts")
def get_alerts():
    try:
        alerts = list(
            db.alerts.find({}, {"_id": 0})
            .sort("created_at", -1)
            .limit(100)
        )
        return jsonify(convert_bson(alerts))

    except Exception:
        app.logger.exception("Could not load alerts")
        return jsonify({"error": "Could not load alerts."}), 500


@app.route("/api/analytics")
def get_analytics():
    try:
        readings = list(
            db.readings.find({}, {"_id": 0})
            .sort("recorded_at", -1)
            .limit(100)
        )

        temperatures = [
            get_number(reading, "temperature_c")
            for reading in readings
        ]
        humidities = [
            get_number(reading, "humidity_percent")
            for reading in readings
        ]
        aqis = [
            get_number(reading, "aqi")
            for reading in readings
        ]

        valid_aqis = [
            value for value in aqis
            if value is not None and value > 0
        ]
        latest_aqi = valid_aqis[0] if valid_aqis else None

        return jsonify({
            "average_temperature_c": average(temperatures),
            "average_humidity_percent": average(humidities),
            "average_aqi": average(aqis),
            "latest_available_aqi": latest_aqi,
            "aqi_status": get_aqi_category(latest_aqi),
            "readings_analyzed": len(readings),
            "note": (
                "Based on stored demo readings, not live sensor data. "
                "Zero values are excluded from averages."
            )
        })

    except Exception:
        app.logger.exception("Could not calculate analytics")
        return jsonify({
            "error": "Could not calculate sensor analytics."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
