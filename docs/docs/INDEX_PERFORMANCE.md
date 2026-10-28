# MongoDB Index Performance Analysis

## 1. Objective

The purpose of this test is to compare MongoDB query execution with an index and without an index. The comparison focuses on documents examined, query plan, and execution time.

## 2. Indexes Used

The project includes indexes for sensor identifiers, reading timestamps, alert filtering, and location coordinates.

The main compound index on the `readings` collection is:

```javascript
{ sensor_id: 1, recorded_at: -1 }
```

This index is intended to support queries that filter readings by sensor and work with timestamps.

Other indexes include:
- A unique index on `sensors.sensor_id`
- An index on `readings.location_id`
- An index for alert status and severity
- A `2dsphere` index on location coordinates

## 3. Test Query

The tested query filters readings for one sensor during August 2026.

```javascript
db.readings.find({
  sensor_id: "SENSOR-WEATHER-HYD-001",
  recorded_at: {
    $gte: ISODate("2026-08-01T00:00:00Z"),
    $lt: ISODate("2026-09-01T00:00:00Z")
  }
})
```

## 4. Recorded Results

| Metric | Indexed query | Collection scan |
|---|---:|---:|
| Documents returned | 24 | 24 |
| Documents examined | 24 | 1,490 |
| Query plan | IXSCAN | COLLSCAN |
| Recorded execution time | 1 ms | 1 ms |

The execution times are observations from a single test run and may vary between runs.

## 5. Analysis

The indexed query examined 24 documents and returned 24 documents. The collection-scan query examined 1,490 documents to return the same 24 results.

The indexed plan used an index scan (`IXSCAN`), while the unindexed comparison used a collection scan (`COLLSCAN`).

This demonstrates that an appropriate index can reduce the number of documents examined. The recorded execution times are too close to establish a reliable time improvement from this single run alone.

## 6. How to Verify

Use MongoDB's `explain("executionStats")` to inspect the query plan and execution statistics.

Example:

```javascript
db.readings.find({
  sensor_id: "SENSOR-WEATHER-HYD-001",
  recorded_at: {
    $gte: ISODate("2026-08-01T00:00:00Z"),
    $lt: ISODate("2026-09-01T00:00:00Z")
  }
}).explain("executionStats")
```

Inspect `winningPlan`, `nReturned`, `totalDocsExamined`, and `executionTimeMillis`.

To compare plans fairly, test the same filter against the same dataset and verify that the index is actually used. Do not drop a production index just to perform a comparison.

## 7. Conclusion

The recorded test shows that the compound index reduced documents examined from 1,490 to 24 for the selected date-range query. Index selection should be based on actual query patterns and verified execution plans.
