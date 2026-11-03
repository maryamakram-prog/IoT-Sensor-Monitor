import os, sys, socket, subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
print("\n===== SENSORSENSE COMPLETE AUDIT =====")
print("Python:", sys.version.split()[0])

for f in ["app.py","crud_routes.py","aggregation_tests.py",
          "INDEX_PERFORMANCE.md","README.md",".env.example"]:
    print(("PASS" if Path(f).exists() else "MISSING"), f)

print("\n===== ATLAS CONNECTION =====")
try:
    from pymongo import MongoClient
    uri = os.getenv("MONGO_URI")
    db = MongoClient(uri, serverSelectionTimeoutMS=8000)[
        os.getenv("MONGO_DB","IoTSensorMonitor")]
    db.command("ping")
    print("PASS: Atlas connected")

    info = list(db.list_collections())
    for c in info:
        name = c["name"]
        col = db[name]
        print(name, "| Documents:", col.count_documents({}),
              "| Indexes:", list(col.index_information().keys()))
        if c.get("options", {}).get("timeseries"):
            print("TIME SERIES:", c["options"]["timeseries"])

    expected = {"locations","sensors","readings","alerts","maintenance_logs"}
    print("Five collections:", expected.issubset(db.list_collection_names()))

    print("\n===== AGGREGATION TESTS =====")
    result = subprocess.run([sys.executable,"aggregation_tests.py"],
                            timeout=100)
    print("Aggregation exit code:", result.returncode)
except Exception as e:
    print("ATLAS TEST FAILED:", type(e).__name__, str(e)[:500])

print("\n===== DASHBOARD API TESTS =====")
import urllib.request
for p in ["/api/health","/api/sensors","/api/readings",
          "/api/alerts","/api/analytics","/api/counts"]:
    try:
        r = urllib.request.urlopen("http://127.0.0.1:5000"+p,timeout=3)
        print("PASS",p,"HTTP",r.status)
    except Exception as e:
        print("CHECK",p,type(e).__name__)

print("\n===== AUDIT COMPLETE =====")
