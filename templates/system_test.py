
import os
import sys
import time
import uuid
import subprocess
import urllib.request
import urllib.error
import json
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "IoTSensorMonitor")

EXPECTED_COLLECTIONS = [
    "locations",
    "sensors",
    "readings",
    "alerts",
    "maintenance_logs"
]

API_ENDPOINTS = [
    "/api/health",
    "/api/sensors",
    "/api/readings",
    "/api/alerts",
    "/api/analytics",
    "/api/counts"
]

results = []
server_process = None


def report(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, passed))
    print(f"[{status}] {name}")
    if detail:
        print(f"       {detail}")


def api_request(path):
    request = urllib.request.Request(
        BASE_URL + path,
        headers={"Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        body = response.read().decode("utf-8")
        return response.status, json.loads(body)


def start_server_if_needed():
    global server_process

    try:
        api_request("/api/health")
        report("Flask server", True, "Already running")
        return
    except Exception:
        pass

    print("\nStarting Flask server automatically...")

    if not os.path.exists("app.py"):
        report("Flask server", False, "app.py not found")
        return

    server_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    for _ in range(25):
        time.sleep(1)
        try:
            api_request("/api/health")
            report("Flask server", True, "Started successfully")
            return
        except Exception:
            if server_process.poll() is not None:
                break

    report("Flask server", False, "Could not start. Check app.py output.")


def test_apis():
    print("\n========== API TESTS ==========")

    for endpoint in API_ENDPOINTS:
        try:
            status, data = api_request(endpoint)
            valid = status == 200 and isinstance(data, (dict, list))
            report(endpoint, valid, f"HTTP {status}")
        except Exception as e:
            report(endpoint, False, str(e)[:180])


def test_database():
    print("\n========== MONGODB TESTS ==========")

    if not MONGO_URI:
        report("MongoDB URI", False, "MONGO_URI missing in .env")
        return

    client = None

    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=8000
        )
        client.admin.command("ping")
        report("MongoDB Atlas connection", True, "Ping successful")

        db = client[DB_NAME]
        report("Database selection", True, DB_NAME)

        existing = db.list_collection_names()

        for name in EXPECTED_COLLECTIONS:
            passed = name in existing
            count = db[name].count_documents({}) if passed else 0
            report(
                f"Collection: {name}",
                passed,
                f"{count:,} documents" if passed else "Collection missing"
            )

        print("\n========== TEMPORARY CRUD TEST ==========")

        test_name = "_sensorsense_test_" + uuid.uuid4().hex[:10]
        collection = db[test_name]

        try:
            # CREATE
            collection.insert_one({
                "test_id": "system-test",
                "value": 100,
                "created_at": datetime.now(timezone.utc)
            })
            report("CRUD - Create", True)

            # READ
            document = collection.find_one({"test_id": "system-test"})
            report("CRUD - Read", document is not None)

            # UPDATE
            update_result = collection.update_one(
                {"test_id": "system-test"},
                {"$set": {"value": 200}}
            )
            updated = collection.find_one({"test_id": "system-test"})
            report(
                "CRUD - Update",
                update_result.modified_count == 1
                and updated["value"] == 200
            )

            # DELETE
            delete_result = collection.delete_one(
                {"test_id": "system-test"}
            )
            report(
                "CRUD - Delete",
                delete_result.deleted_count == 1
            )

        finally:
            collection.drop()
            report("Temporary CRUD cleanup", True)

        print("\n========== TIME-SERIES TEST ==========")

        ts_name = "_sensorsense_ts_test_" + uuid.uuid4().hex[:10]

        try:
            db.create_collection(
                ts_name,
                timeseries={
                    "timeField": "timestamp",
                    "metaField": "sensor_id",
                    "granularity": "hours"
                }
            )

            ts = db[ts_name]
            ts.insert_one({
                "timestamp": datetime.now(timezone.utc),
                "sensor_id": "TEST-SENSOR",
                "temperature": 28.5
            })

            found = ts.find_one({"sensor_id": "TEST-SENSOR"})
            report(
                "Time-Series insert/read",
                found is not None,
                "Temporary MongoDB time-series collection"
            )

        except Exception as e:
            report("Time-Series insert/read", False, str(e)[:180])

        finally:
            if ts_name in db.list_collection_names():
                db.drop_collection(ts_name)
                report("Time-Series cleanup", True)

    except Exception as e:
        report("MongoDB connection", False, str(e)[:200])

    finally:
        if client:
            client.close()


def main():
    print("=" * 55)
    print("       SENSORSENSE COMPLETE SYSTEM TEST")
    print("=" * 55)

    start_server_if_needed()

    test_apis()
    test_database()

    print("\n========== FINAL REPORT ==========")

    passed = sum(1 for _, status in results if status)
    failed = len(results) - passed

    print(f"\nTotal tests : {len(results)}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {failed}")

    if failed == 0:
        print("\nALL TESTS PASSED!")
    else:
        print("\nSOME TESTS FAILED - CHECK DETAILS ABOVE.")

    print("=" * 55)

    if server_process and server_process.poll() is None:
        server_process.terminate()
        print("Automatically started Flask server stopped.")


if __name__ == "__main__":
    main()
