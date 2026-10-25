
from datetime import datetime, date

from flask import Blueprint, jsonify, request, current_app
from bson import ObjectId
from pymongo.errors import PyMongoError

crud = Blueprint("crud", __name__)


def get_db():
    return current_app.config["mongo_db"]


def convert_value(value):
    """Convert MongoDB values into JSON-safe values."""
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: convert_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [convert_value(item) for item in value]

    return value


def serialize_sensor(sensor):
    if sensor is None:
        return None

    return {
        key: convert_value(value)
        for key, value in sensor.items()
    }


# CREATE: Add a sensor
@crud.route("/api/sensors", methods=["POST"])
def create_sensor():
    data = request.get_json(silent=True) or {}

    sensor_id = data.get("sensor_id")
    sensor_name = data.get("sensor_name", data.get("name"))
    sensor_type = data.get("sensor_type", data.get("type", "weather"))
    status = data.get("status", "active")

    if not isinstance(sensor_id, str) or not sensor_id.strip():
        return jsonify({"error": "A valid sensor_id is required."}), 400

    if not isinstance(sensor_name, str) or not sensor_name.strip():
        return jsonify({"error": "A valid sensor_name is required."}), 400

    if not isinstance(sensor_type, str) or not sensor_type.strip():
        return jsonify({"error": "A valid sensor_type is required."}), 400

    if status not in ("active", "inactive"):
        return jsonify({
            "error": "Status must be active or inactive."
        }), 400

    sensor_id = sensor_id.strip()

    sensor = {
        "sensor_id": sensor_id,
        "sensor_name": sensor_name.strip(),
        "sensor_type": sensor_type.strip(),
        "status": status,
        "installed_at": datetime.utcnow()
    }

    try:
        db = get_db()

        if db.sensors.find_one({"sensor_id": sensor_id}):
            return jsonify({
                "error": "This sensor_id already exists."
            }), 409

        result = db.sensors.insert_one(sensor)
        sensor["_id"] = result.inserted_id

        return jsonify({
            "message": "Sensor created successfully.",
            "sensor": serialize_sensor(sensor)
        }), 201

    except PyMongoError:
        current_app.logger.exception("Sensor creation failed")
        return jsonify({"error": "Database operation failed."}), 500


# READ: Get one sensor
@crud.route("/api/sensors/<sensor_id>", methods=["GET"])
def read_sensor(sensor_id):
    try:
        sensor = get_db().sensors.find_one({"sensor_id": sensor_id})

        if sensor is None:
            return jsonify({"error": "Sensor not found."}), 404

        return jsonify(serialize_sensor(sensor)), 200

    except PyMongoError:
        current_app.logger.exception("Reading sensor failed")
        return jsonify({"error": "Database operation failed."}), 500


# UPDATE: Update a sensor
@crud.route("/api/sensors/<sensor_id>", methods=["PUT"])
def update_sensor(sensor_id):
    data = request.get_json(silent=True) or {}

    updates = {}

    if "sensor_name" in data or "name" in data:
        value = data.get("sensor_name", data.get("name"))

        if not isinstance(value, str) or not value.strip():
            return jsonify({"error": "Invalid sensor_name."}), 400

        updates["sensor_name"] = value.strip()

    if "sensor_type" in data or "type" in data:
        value = data.get("sensor_type", data.get("type"))

        if not isinstance(value, str) or not value.strip():
            return jsonify({"error": "Invalid sensor_type."}), 400

        updates["sensor_type"] = value.strip()

    if "status" in data:
        if data["status"] not in ("active", "inactive"):
            return jsonify({
                "error": "Status must be active or inactive."
            }), 400

        updates["status"] = data["status"]

    if not updates:
        return jsonify({
            "error": "Provide sensor_name, sensor_type, or status to update."
        }), 400

    try:
        db = get_db()

        result = db.sensors.update_one(
            {"sensor_id": sensor_id},
            {"$set": updates}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Sensor not found."}), 404

        sensor = db.sensors.find_one({"sensor_id": sensor_id})

        return jsonify({
            "message": "Sensor updated successfully.",
            "sensor": serialize_sensor(sensor)
        }), 200

    except PyMongoError:
        current_app.logger.exception("Sensor update failed")
        return jsonify({"error": "Database operation failed."}), 500


# DELETE: Delete a sensor
@crud.route("/api/sensors/<sensor_id>", methods=["DELETE"])
def delete_sensor(sensor_id):
    try:
        result = get_db().sensors.delete_one({"sensor_id": sensor_id})

        if result.deleted_count == 0:
            return jsonify({"error": "Sensor not found."}), 404

        return jsonify({
            "message": "Sensor deleted successfully.",
            "sensor_id": sensor_id
        }), 200

    except PyMongoError:
        current_app.logger.exception("Sensor deletion failed")
        return jsonify({"error": "Database operation failed."}), 500
