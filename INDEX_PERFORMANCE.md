# MongoDB Index Performance Comparison

## Objective
To compare MongoDB query execution with an index and without an index using `explain()`.

## Query
```python
query = {"sensor_id": "SENSOR-WEATHER-HYD-001"}
```

## Results

| Metric | With Index | Without Index |
|---|---|---|
| Query plan | IXSCAN | COLLSCAN |
| Documents returned | 1488 | 1488 |
| Documents examined | 1488 | 1490 |
| Execution time | 3 ms | 2 ms |

## Analysis
The indexed query used the compound index `sensor_id_1_recorded_at_-1`. The query without an index used a collection scan (`COLLSCAN`) and examined all 1490 documents.

The indexed query examined 1488 documents, matching the number of results. Because this query returned almost every record for the selected sensor, the performance difference was small. Execution time can vary due to caching and server conditions.

## Conclusion
MongoDB indexes can help reduce the amount of data examined for suitable queries. A more selective query, such as filtering by sensor ID and a date range, can provide a more meaningful performance comparison.
## Date-Range Query Performance Test

### Query Conditions
- Sensor ID: `SENSOR-WEATHER-HYD-001`
- Start date: 1 August 2026
- End date: Before 2 August 2026

### Results

| Metric | With Index | Without Index |
|---|---|---|
| Query plan | IXSCAN | COLLSCAN |
| Documents returned | 24 | 24 |
| Documents examined | 24 | 1490 |
| Execution time | 1 ms | 1 ms |

### Analysis
The indexed query used the compound index `sensor_id_1_recorded_at_-1` and examined 24 documents to return 24 matching records. Without the index, MongoDB performed a collection scan and examined all 1490 documents to return the same results.

The execution time was 1 ms in both tests, so these measurements do not show a timing improvement. However, the reduction in documents examined demonstrates the index's benefit for this date-range query.

### Conclusion
The `explain()` results demonstrate the difference between index scanning (`IXSCAN`) and collection scanning (`COLLSCAN`). The existing compound index supports filtering by sensor ID and recording date.
