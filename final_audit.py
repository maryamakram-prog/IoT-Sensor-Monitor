
import os
import sys
import json
import uuid
import urllib.request
import urllib.error
import subprocess
import py_compile
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

API = "http://127.0.0.1:5000"

PASS = 0
FAIL = 0


def report(name, ok, detail=""):
    global PASS, FAIL

    if ok:
        PASS += 1
        print(f"[PASS] {name} {detail}")
    else:
        FAIL += 1
        print(f"[FAIL] {name} {detail}")


def request_api(path, method="GET", data=None):
    body = None if data is None else json.dumps(data).encode()

    req = urllib.request.Request(
        API + path,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}

    except urllib.error.HTTPError as e:
        raw = e.read().decode()

        try:
            result = json.loads(raw)
        except Exception:
            result = {"response": raw}

        return e.code, result


print("\n========== SENSORSENSE FINAL PROJECT AUDIT ==========\n")


# =====================================================
# 1. DASHBOARD API TESTS
# =====================================================

print("\n--- 1. DASHBOARD API TESTS ---")

for endpoint in [
    "/api/health",
    "/api/sensors",
    "/api/readings",
    "/api/alerts",
    "/api/analytics",
    "/api/counts"
]:
    try:
        status, _ = request_api(endpoint)

        report(
            endpoint,
            status == 200,
            f"HTTP {status}"
        )

    except Exception as e:
        report(endpoint, False, str(e))


# =====================================================
# 2. CRUD TEST
# =====================================================

print("\n--- 2. CRUD TEST ---")

test_id = "SENSOR-CRUD-TEST-" + uuid.uuid4().hex[:8].upper()
created = False

try:
    status, result = request_api(
        "/api/sensors",
        "POST",
        {
            "sensor_id": test_id,
            "sensor_name": "Temporary CRUD Audit Sensor",
            "sensor_type": "test",
            "status": "active"
        }
    )

    created = status == 201

    report("CREATE sensor", created, f"HTTP {status}")

    if created:

        status, result = request_api(
            "/api/sensors/" + test_id
        )

        report("READ sensor", status == 200, f"HTTP {status}")

        status, result = request_api(
            "/api/sensors/" + test_id,
            "PUT",
            {
                "sensor_name": "Updated CRUD Audit Sensor",
                "status": "inactive"
            }
        )

        report("UPDATE sensor", status == 200, f"HTTP {status}")

        status, result = request_api(
            "/api/sensors/" + test_id,
            "DELETE"
        )

        deleted = status == 200

        report("DELETE sensor", deleted, f"HTTP {status}")

        status, result = request_api(
            "/api/sensors/" + test_id
        )

        report(
            "VERIFY deletion",
            status == 404,
            f"HTTP {status}"
        )

    else:
        print("[WARN] CRUD remaining steps skipped because CREATE failed.")

except Exception as e:

    report("CRUD workflow", False, str(e))

    if created:
        try:
            request_api(
                "/api/sensors/" + test_id,
                "DELETE"
            )
        except Exception:
            pass


# =====================================================
# 3. MONGODB ATLAS AND COLLECTIONS
# =====================================================

print("\n--- 3. MONGODB ATLAS & COLLECTIONS ---")

client = None
db = None

try:
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB", "IoTSensorMonitor")

    if not uri:
        raise ValueError("MONGO_URI missing from .env")

    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=12000
    )

    client.admin.command("ping")

    db = client[db_name]

    report(
        "MongoDB Atlas connection",
        True,
        f"Database={db_name}"
    )

    expected = [
        "locations",
        "sensors",
        "readings",
        "alerts",
        "maintenance_logs"
    ]

    existing = db.list_collection_names()

    for name in expected:

        if name in existing:

            count = db[name].count_documents({})

            indexes = list(
                db[name].index_information().keys()
            )

            report(
                f"Collection {name}",
                True,
                f"Documents={count}, Indexes={indexes}"
            )

        else:
            report(
                f"Collection {name}",
                False,
                "Missing"
            )

    ts_exists = "sensor_readings_ts" in existing

    report(
        "Time-Series collection exists",
        ts_exists
    )

    if ts_exists:

        ts_count = db.sensor_readings_ts.count_documents({})

        print(
            f"[INFO] Time-Series documents: {ts_count}"
        )

        if ts_count == 0:
            print(
                "[WARN] Time-Series collection is empty."
            )

except Exception as e:

    report("MongoDB audit", False, str(e))


# =====================================================
# 4. FIVE AGGREGATION PIPELINES
# =====================================================

print("\n--- 4. FIVE AGGREGATION PIPELINES ---")

try:

    result = subprocess.run(
        [
            sys.executable,
            str(BASE / "aggregation_tests.py")
        ],
        cwd=str(BASE),
        capture_output=True,
        text=True,
        timeout=120
    )

    print(result.stdout[-7000:])

    if result.stderr:
        print(
            "[AGGREGATION STDERR]",
            result.stderr[-2000:]
        )

    report(
        "Aggregation test script",
        result.returncode == 0,
        f"Exit code={result.returncode}"
    )

except Exception as e:

    report(
        "Aggregation test script",
        False,
        str(e)
    )


# =====================================================
# 5. INDEX PERFORMANCE EXPLAIN COMPARISON
# =====================================================

print("\n--- 5. INDEX PERFORMANCE ---")

if db is not None:

    try:

        query = {
            "sensor_id": "SENSOR-WEATHER-HYD-001"
        }

        # WITHOUT INDEX: Collection Scan
        before = db.command(
            "explain",
            {
                "find": "readings",
                "filter": query,
                "sort": {"recorded_at": -1},
                "limit": 10,
                "hint": {"$natural": 1}
            },
            verbosity="executionStats"
        )

        # WITH INDEX: Compound Index
        after = db.command(
            "explain",
            {
                "find": "readings",
                "filter": query,
                "sort": {"recorded_at": -1},
                "limit": 10,
                "hint": {
                    "sensor_id": 1,
                    "recorded_at": -1
                }
            },
            verbosity="executionStats"
        )

        def stats(plan):

            execution = plan.get(
                "executionStats", {}
            )

            return {
                "executionTimeMillis":
                    execution.get("executionTimeMillis"),

                "totalDocsExamined":
                    execution.get("totalDocsExamined"),

                "totalKeysExamined":
                    execution.get("totalKeysExamined"),

                "nReturned":
                    execution.get("nReturned")
            }

        before_stats = stats(before)
        after_stats = stats(after)

        print(
            "\nCOLLECTION SCAN:",
            before_stats
        )

        print(
            "INDEXED QUERY:",
            after_stats
        )

        before_stage = (
            before.get("queryPlanner", {})
            .get("winningPlan", {})
        )

        after_stage = (
            after.get("queryPlanner", {})
            .get("winningPlan", {})
        )

        def find_stages(plan):
            stages = []

            def walk(node):
                if isinstance(node, dict):
                    if "stage" in node:
                        stages.append(node["stage"])

                    for value in node.values():
                        walk(value)

                elif isinstance(node, list):
                    for value in node:
                        walk(value)

            walk(plan)
            return stages

        before_stages = find_stages(before_stage)
        after_stages = find_stages(after_stage)

        print("COLLECTION SCAN STAGES:", before_stages)
        print("INDEXED QUERY STAGES:", after_stages)

        before_success = (
            before.get("executionStats", {})
            .get("executionSuccess", False)
        )

        after_success = (
            after.get("executionStats", {})
            .get("executionSuccess", False)
        )

        index_used = (
            "IXSCAN" in after_stages
        )

        execution_success = (
            before_success
            and after_success
            and index_used
        )

        report(
            "Index explain comparison",
            execution_success,
            "Collection scan and compound index explain completed"
        )

    except Exception as e:

        report(
            "Index explain comparison",
            False,
            str(e)
        )


# =====================================================
# 6. PYTHON FILE COMPILATION
# =====================================================

print("\n--- 6. PYTHON FILE COMPILATION ---")

for filename in [
    "app.py",
    "crud_routes.py",
    "aggregation_tests.py"
]:

    path = BASE / filename

    if path.exists():

        try:

            py_compile.compile(
                str(path),
                doraise=True
            )

            report(
                filename + " compilation",
                True
            )

        except Exception as e:

            report(
                filename + " compilation",
                False,
                str(e)
            )

    else:

        report(
            filename + " exists",
            False
        )


# =====================================================
# 7. SUBMISSION FILES
# =====================================================

print("\n--- 7. SUBMISSION FILES ---")

for filename in [
    "README.md",
    ".env.example",
    "requirements.txt",
    ".gitignore",
    "INDEX_PERFORMANCE.md"
]:

    report(
        filename,
        (BASE / filename).is_file()
    )


docs = BASE / "docs"

report(
    "docs folder",
    docs.is_dir()
)

if docs.is_dir():

    print(
        "[INFO] docs contents:",
        [p.name for p in docs.iterdir()]
    )


# =====================================================
# 8. GITHUB STATUS
# =====================================================

print("\n--- 8. GITHUB STATUS ---")

try:

    remote = subprocess.run(
        ["git", "remote", "-v"],
        cwd=str(BASE),
        capture_output=True,
        text=True
    )

    report(
        "Git remote configured",
        remote.returncode == 0
        and bool(remote.stdout.strip())
    )

    print(
        remote.stdout.strip()
        or "No Git remote found."
    )

    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(BASE),
        capture_output=True,
        text=True
    )

    print(
        "Git changes:\n",
        status.stdout.strip()
        or "Working tree clean"
    )

except Exception as e:

    print("[WARN] Git check:", e)


# =====================================================
# FINAL AUDIT SUMMARY
# =====================================================

print("\n========== FINAL AUDIT SUMMARY ==========")

print("PASS:", PASS)
print("FAIL:", FAIL)
print("TOTAL:", PASS + FAIL)

print("CRUD TEST SENSOR:", test_id)

print("Note: API tests require Flask server running.")

print(
    "Note: Deployment and GitHub publication "
    "need separate live verification."
)

print("=========================================\n")


if client:
    client.close()
