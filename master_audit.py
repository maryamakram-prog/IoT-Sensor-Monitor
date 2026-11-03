import os, re, json, urllib.request
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
print("\n===== SENSORSENSE REMAINING AUDIT =====")

print("\n1. PROJECT FILES")
for f in ["app.py","crud_routes.py","aggregation_tests.py",
          "INDEX_PERFORMANCE.md","README.md",".env.example","docs"]:
    print(("PASS" if Path(f).exists() else "MISSING"),f)

print("\n2. PYTHON COMPILATION")
import py_compile
for f in ["app.py","crud_routes.py","aggregation_tests.py"]:
    try:
        py_compile.compile(f,doraise=True)
        print("PASS",f)
    except Exception as e:
        print("FAIL",f,str(e))

print("\n3. CRUD ROUTE INSPECTION")
if Path("crud_routes.py").exists():
    source=Path("crud_routes.py").read_text(encoding="utf-8")
    routes=re.findall(r'@\w+\.route\([^\n]+',source)
    for r in routes: print(r)
    print("Total route declarations:",len(routes))

print("\n4. ATLAS DATABASE")
try:
    client=MongoClient(os.getenv("MONGO_URI"),serverSelectionTimeoutMS=10000)
    db=client[os.getenv("MONGO_DB","IoTSensorMonitor")]
    db.command("ping")
    print("Atlas: CONNECTED")
    for n in ["locations","sensors","readings","alerts","maintenance_logs","sensor_readings_ts"]:
        if n in db.list_collection_names():
            c=db[n]
            print(n,"documents:",c.count_documents({}))
            print("Indexes:",list(c.index_information()))
    ts=list(db.list_collections(filter={"name":"sensor_readings_ts"}))
    if ts: print("Time-series options:",ts[0].get("options",{}).get("timeseries"))
    if db.readings.count_documents({}):
        doc=db.readings.find_one({"sensor_id":{"$exists":True}},{"sensor_id":1})
        plan=db.readings.find({"sensor_id":doc["sensor_id"]}).sort("recorded_at",-1).explain()
        print("Explain execution stats:",plan.get("executionStats",{}))
    client.close()
except Exception as e:
    print("DATABASE ERROR:",type(e).__name__,str(e)[:300])

print("\n5. DASHBOARD APIs")
for p in ["/api/health","/api/sensors","/api/readings","/api/alerts","/api/analytics","/api/counts"]:
    try:
        r=urllib.request.urlopen("http://127.0.0.1:5000"+p,timeout=3)
        print("PASS",p,r.status)
    except Exception as e: print("NOT AVAILABLE",p,str(e)[:100])

print("\n===== AUDIT FINISHED =====")
