import os
from dotenv import load_dotenv
from pymongo import MongoClient
import dns.resolver

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB", "IoTSensorMonitor")]

print("=== LOCATIONS COLLECTION & INDEXES ===")
print("Document count:", db.locations.count_documents({}))
print("Indexes:", list(db.locations.index_information().keys()))

for loc in db.locations.find({}):
    print("Found location:", loc.get("location_name", loc.get("city")), loc.get("coordinates"))

print("\n=== TESTING GEOSPATIAL $near QUERY (Radius: 25 km) ===")
# Center point: Hyderabad, Sindh [Longitude 68.3578, Latitude 25.3960]
query = {
    "coordinates": {
        "$near": {
            "$geometry": {
                "type": "Point",
                "coordinates": [68.3578, 25.3960]
            },
            "$maxDistance": 25000
        }
    }
}

try:
    results = list(db.locations.find(query))
    print(f"SUCCESS! Found {len(results)} location(s) within 25km:")
    for r in results:
        print(f" -> Name: {r.get('location_name')}, City: {r.get('city')}, Coordinates: {r.get('coordinates')}")
        
    explain_res = db.locations.find(query).explain()
    winning_stage = explain_res.get("queryPlanner", {}).get("winningPlan", {}).get("stage")
    print(f"Query execution stage: {winning_stage} (Uses 2dsphere index!)")
except Exception as e:
    print("Geospatial test failed:", e)
