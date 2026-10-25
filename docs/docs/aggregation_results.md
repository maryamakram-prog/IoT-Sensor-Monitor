# MongoDB Aggregation Pipeline Results

## 1. Overview

This document describes five MongoDB aggregation pipelines tested in the IoT Sensor Monitor project. Aggregation pipelines process documents through stages such as `$match`, `$group`, `$project`, `$sort`, and `$bucket` to summarize and analyze sensor readings.

The tests use the project's historical weather dataset stored in the `readings` collection.

## 2. Pipeline 1 — Average Temperature and Humidity by Sensor

**Objective:** Calculate average temperature and humidity for each sensor.

**Aggregation stages:**
- `$group` groups readings by sensor identifier.
- `$avg` calculates the average of available numeric values.

**Recorded result:**
- Historical records analyzed: 1,488
- Average temperature: approximately 31.18 °C
- Average humidity: approximately 66.22%

**Purpose:** This analysis summarizes weather measurements associated with each sensor.

## 3. Pipeline 2 — Hourly Reading Counts

**Objective:** Count reading documents by hour.

**Aggregation stages:**
- Extract the hour from the timestamp.
- `$group` counts readings for each hour.

**Recorded result:** The dataset contains 62 records per hour in the tested hourly grouping.

**Purpose:** Hourly counts help inspect the distribution of records over time.

## 4. Pipeline 3 — Daily Temperature Summary

**Objective:** Summarize temperature measurements by day.

**Aggregation stages:**
- Group readings by calendar date.
- Calculate daily temperature statistics.

**Purpose:** Daily summaries help identify changes in temperature across the historical dataset.

The exact daily values can be obtained by rerunning `aggregation_tests.py`.

## 5. Pipeline 4 — Temperature Bucketing

**Objective:** Group readings into temperature ranges.

**Recorded bucket counts:**

| Temperature range | Number of records |
|---|---:|
| Below 20 °C | 0 |
| 20 °C to below 30 °C | 703 |
| 30 °C to below 40 °C | 777 |
| 40 °C and above | 8 |

**Purpose:** Bucketing makes it easier to understand the distribution of temperature readings.

## 6. Pipeline 5 — Humidity Bucketing

**Objective:** Group readings into humidity ranges.

**Recorded bucket counts:**

| Humidity range | Number of records |
|---|---:|
| Below 25% | 0 |
| 25% to below 50% | 283 |
| 50% to below 75% | 626 |
| 75% and above | 579 |

**Purpose:** Humidity buckets summarize how readings are distributed across different humidity levels.

## 7. How to Run the Tests

Activate the project's virtual environment, configure the `.env` file with a valid MongoDB Atlas connection string, and run:

```bash
python aggregation_tests.py
```

The script connects to MongoDB and executes the aggregation tests implemented in the project.

## 8. Interpretation and Limitations

The results demonstrate grouping, counting, averaging, date-based analysis, and bucketing with MongoDB aggregation pipelines.

Most historical readings were imported from Open-Meteo reanalysis data for Hyderabad, Pakistan. They are not direct measurements from physical IoT hardware. Demonstration air-quality values are not verified live environmental measurements.

Results can differ if the underlying dataset changes.

## 9. Conclusion

The five pipelines demonstrate how MongoDB aggregation can transform a large set of readings into useful summaries. These operations support analysis of weather patterns, time-based record distributions, and measurement ranges.
