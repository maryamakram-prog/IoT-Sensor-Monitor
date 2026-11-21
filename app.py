
import os
from datetime import datetime, date, timezone, timedelta

from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

from crud_routes import crud


# ==================================================
# 1. FLASK APP AND MONGODB CONNECTION
# ==================================================

load_dotenv()

# Configure DNS resolver to avoid Windows SRV query SERVFAIL issues
try:
    import dns.resolver
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ["8.8.8.8", "1.1.1.1"]
except Exception:
    pass

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


# ==================================================
# 2. JSON CONVERSION
# ==================================================

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


# ==================================================
# 3. MEASUREMENT VALIDATION
# ==================================================

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

    if field == "aqi" and value < 0:
        return None

    return value


def average(values):

    valid_values = [
        value
        for value in values
        if value is not None
    ]

    if not valid_values:
        return None

    return round(
        sum(valid_values) / len(valid_values),
        2
    )


# ==================================================
# 4. AQI CATEGORY
# ==================================================

def aqi_category(aqi):

    if aqi is None:
        return {
            "category": "Unavailable",
            "risk": "Unknown",
            "message": "No valid AQI measurement is available yet."
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
            "message": "Air quality is acceptable. However, unusually sensitive people should consider limiting prolonged outdoor exertion."
        }

    if aqi <= 150:
        return {
            "category": "Unhealthy for Sensitive Groups",
            "risk": "Elevated",
            "message": "Sensitive groups may experience health effects."
        }

    if aqi <= 200:
        return {
            "category": "Unhealthy",
            "risk": "High",
            "message": "Health effects may occur. Reduce outdoor exposure."
        }

    if aqi <= 300:
        return {
            "category": "Very Unhealthy",
            "risk": "Very High",
            "message": "Avoid prolonged outdoor exposure."
        }

    return {
        "category": "Hazardous",
        "risk": "Severe",
        "message": "Air quality is hazardous. Avoid outdoor exposure."
    }


# ==================================================
# 5. DATABASE READING FUNCTIONS
# ==================================================

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


# ==================================================
# 6. FRONTEND NAVIGATION ROUTES
# ==================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        page="dashboard"
    )


@app.route("/analytics")
def analytics_page():

    return render_template(
        "index.html",
        page="analytics"
    )


@app.route("/weather")
def weather_page():

    return render_template(
        "index.html",
        page="weather"
    )


@app.route("/sensors")
def sensors_page():

    return render_template(
        "index.html",
        page="sensors"
    )


@app.route("/latest-readings")
def latest_readings_page():

    return render_template(
        "index.html",
        page="latest"
    )


@app.route("/history")
def history_page():

    return render_template(
        "index.html",
        page="history"
    )


@app.route("/alerts")
def alerts_page():

    return render_template(
        "index.html",
        page="alerts"
    )


# ==================================================
# 7. DATABASE HEALTH API
# ==================================================

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
            "message": "MongoDB connection failed."
        }), 500


# ==================================================
# 8. DASHBOARD COUNTS API
# ==================================================

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


# ==================================================
# 9. SENSORS API
# ==================================================

@app.route("/api/sensors")
def get_sensors():

    try:

        sensors = list(
            db.sensors.find(
                {},
                {"_id": 0}
            ).sort("sensor_id", 1)
        )

        return jsonify(
            convert_bson(sensors)
        )

    except Exception:

        app.logger.exception(
            "Could not load sensors"
        )

        return jsonify({
            "error": "Could not load sensors."
        }), 500


# ==================================================
# 10. READINGS API
# ==================================================

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


# ==================================================
# 11. ALERTS API
# ==================================================

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


# ==================================================
# 12. ANALYTICS API (MongoDB Aggregation Pipelines)
# ==================================================

@app.route("/api/analytics")
def get_analytics():
    """
    Computes environmental statistics using MongoDB Aggregation Pipelines
    with $facet, $group, $avg, $min, $max, and $bucket stages.
    """
    try:
        pipeline = [
            {
                "$facet": {
                    "overall": [
                        {
                            "$match": {
                                "data_source": {"$ne": "demo"}
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "total_records": {"$sum": 1},
                                "avg_temperature": {"$avg": "$temperature_c"},
                                "min_temperature": {"$min": "$temperature_c"},
                                "max_temperature": {"$max": "$temperature_c"},
                                "avg_humidity": {"$avg": "$humidity_percent"},
                                "min_humidity": {"$min": "$humidity_percent"},
                                "max_humidity": {"$max": "$humidity_percent"},
                                "avg_aqi": {"$avg": "$aqi"}
                            }
                        }
                    ],
                    "temperature_buckets": [
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
                    "latest_reading": [
                        {"$sort": {"recorded_at": -1}},
                        {"$limit": 1}
                    ]
                }
            }
        ]

        agg_result = list(db.readings.aggregate(pipeline))
        facet_data = agg_result[0] if agg_result else {}

        overall = facet_data.get("overall", [{}])[0] if facet_data.get("overall") else {}
        latest_doc = facet_data.get("latest_reading", [{}])[0] if facet_data.get("latest_reading") else {}
        buckets = facet_data.get("temperature_buckets", [])

        latest_aqi = latest_doc.get("aqi")
        status = aqi_category(latest_aqi)

        avg_temp = round(overall.get("avg_temperature", 0.0), 2) if overall.get("avg_temperature") is not None else None
        avg_hum = round(overall.get("avg_humidity", 0.0), 2) if overall.get("avg_humidity") is not None else None
        avg_aqi = round(overall.get("avg_aqi", 0.0), 2) if overall.get("avg_aqi") is not None else None

        return jsonify({
            "engine": "MongoDB Aggregation Pipeline ($facet, $group, $bucket)",
            "total_readings": overall.get("total_records", db.readings.count_documents({})),
            "average_temperature_c": avg_temp,
            "min_temperature_c": overall.get("min_temperature"),
            "max_temperature_c": overall.get("max_temperature"),
            "average_humidity_percent": avg_hum,
            "min_humidity_percent": overall.get("min_humidity"),
            "max_humidity_percent": overall.get("max_humidity"),
            "average_aqi": avg_aqi,
            "latest_available_aqi": latest_aqi,
            "temperature_buckets": buckets,
            "aqi_status": status,
            "aqi_category": status["category"],
            "aqi_risk": status["risk"],
            "aqi_message": status["message"],
            "latest_reading": convert_bson(latest_doc),
            "readings_analyzed": overall.get("total_records", 0)
        })

    except Exception:
        app.logger.exception("Could not calculate aggregation analytics")
        return jsonify({"error": "Could not calculate sensor analytics."}), 500


# ==================================================
# 13. GEOSPATIAL SEARCH API ($near on 2dsphere)
# ==================================================

@app.route("/api/locations/nearby")
def nearby_locations():
    """
    Demonstrates MongoDB Geospatial 2dsphere indexing and the $near operator.
    Default coordinates: Hyderabad, Pakistan [68.3578, 25.3960]
    """
    try:
        lon = float(request.args.get("lon", 68.3578))
        lat = float(request.args.get("lat", 25.3960))
        max_dist = int(request.args.get("max_distance", 50000)) # 50 km default

        query = {
            "coordinates": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "$maxDistance": max_dist
                }
            }
        }

        results = list(db.locations.find(query))
        return jsonify({
            "feature": "MongoDB 2dsphere Geospatial Index",
            "query_center": [lon, lat],
            "max_distance_meters": max_dist,
            "locations_found": len(results),
            "results": convert_bson(results)
        })

    except Exception:
        app.logger.exception("Geospatial query failed")
        return jsonify({"error": "Geospatial query failed."}), 500


# ==================================================
# 14. AGGREGATION PIPELINES DEMO API
# ==================================================

@app.route("/api/aggregations/run")
def run_aggregations():
    """
    Executes and returns the 5 MongoDB aggregation pipelines
    required by the project rubric.
    """
    try:
        # Pipeline 1: Avg Temp & Humidity by Sensor (Excluding Demo Records)
        p1 = list(db.readings.aggregate([
            {
                "$match": {
                    "temperature_c": {"$ne": None},
                    "data_source": {"$ne": "demo"}
                }
            },
            {"$group": {
                "_id": "$sensor_id",
                "avg_temperature": {"$avg": "$temperature_c"},
                "avg_humidity": {"$avg": "$humidity_percent"},
                "total_records": {"$sum": 1}
            }}
        ]))

        # Pipeline 2: Hourly distribution using $hour
        p2 = list(db.readings.aggregate([
            {"$match": {"recorded_at": {"$ne": None}}},
            {"$group": {
                "_id": {"$hour": "$recorded_at"},
                "record_count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]))

        # Pipeline 3: Daily Summary for Actual Last 7 Calendar Days
        now = datetime.now()
        seven_days_ago = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)

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
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$recorded_at"}},
                "min_temperature": {"$min": "$temperature_c"},
                "max_temperature": {"$max": "$temperature_c"},
                "avg_temperature": {"$avg": "$temperature_c"},
                "records": {"$sum": 1}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 7}
        ]))

        # Pipeline 4: Temperature Bucketing
        p4 = list(db.readings.aggregate([
            {"$match": {"temperature_c": {"$ne": None}}},
            {"$bucket": {
                "groupBy": "$temperature_c",
                "boundaries": [0, 20, 30, 40, 60],
                "default": "other",
                "output": {"records": {"$sum": 1}}
            }}
        ]))

        # Pipeline 5: Humidity Distribution Bucketing
        p5 = list(db.readings.aggregate([
            {"$match": {"humidity_percent": {"$ne": None}}},
            {"$bucket": {
                "groupBy": "$humidity_percent",
                "boundaries": [0, 25, 50, 75, 101],
                "default": "other",
                "output": {
                    "records": {"$sum": 1},
                    "avg_humidity": {"$avg": "$humidity_percent"}
                }
            }}
        ]))

        return jsonify({
            "status": "success",
            "pipelines_executed": 5,
            "pipeline_1_sensor_averages": convert_bson(p1),
            "pipeline_2_hourly_distribution": convert_bson(p2),
            "pipeline_3_daily_summary_last_7_days": convert_bson(p3),
            "pipeline_4_temperature_buckets": convert_bson(p4),
            "pipeline_5_humidity_buckets": convert_bson(p5)
        })

    except Exception:
        app.logger.exception("Aggregation pipelines execution failed")
        return jsonify({"error": "Failed to run aggregation pipelines."}), 500


# ==================================================
# 13. START APPLICATION
# ==================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )