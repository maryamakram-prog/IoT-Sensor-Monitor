# MongoDB Schema Design — IoT Sensor Monitor

## 1. Overview

The IoT Sensor Monitor project uses MongoDB Atlas as its database. The database is named `IoTSensorMonitor` and contains five collections:

1. `sensors`
2. `readings`
3. `locations`
4. `alerts`
5. `maintenance_logs`

The collections organize sensor information, recorded measurements, location details, alerts, and maintenance history.

## 2. Collection Design

### 2.1 sensors

Stores information about each sensor.

**Example fields:**
- `sensor_id` — unique sensor identifier
- `sensor_name` — sensor name
- `sensor_type` — type of sensor
- `status` — current sensor status
- `location_id` — reference to a location
- `installed_at` — installation timestamp

### 2.2 readings

Stores measurement records collected or imported for analysis.

**Example fields:**
- `sensor_id` — reference to a sensor
- `location_id` — reference to a location
- `temperature` — temperature measurement, when available
- `humidity` — humidity measurement, when available
- `recorded_at` — date and time of the record

The readings collection is designed to store many records for each sensor over time.

### 2.3 locations

Stores location information associated with sensors.

**Example fields:**
- `location_id` — location identifier
- `name` — location name
- `coordinates` — geographical coordinates, when available

A geospatial index can support location-based queries when coordinates are stored in the required GeoJSON format.

### 2.4 alerts

Stores alert information related to sensor monitoring.

**Example fields:**
- `sensor_id` — associated sensor identifier
- `severity` — alert severity
- `status` — alert status
- `message` — alert description, when available
- `created_at` — alert creation timestamp, when available

### 2.5 maintenance_logs

Stores maintenance records for sensors.

**Example fields:**
- `sensor_id` — associated sensor identifier
- `maintenance_date` — maintenance date, when available
- `description` — maintenance details, when available
- `status` — maintenance status, when available

The exact fields depend on the documents stored in each collection.

## 3. Relationships Between Collections

The database uses references to associate related information.

- One sensor can have many readings.
- One sensor can have multiple alert records.
- One sensor can have multiple maintenance records.
- A sensor can reference a location through `location_id`.
- Readings can reference sensors and locations using their identifiers.

### Relationship summary

```text
locations
   |
   | location_id
   v
sensors
   |
   | sensor_id
   +----------> readings
   |
   +----------> alerts
   |
   +----------> maintenance_logs
```

This diagram represents the intended logical relationships. MongoDB references are application-managed identifiers; they do not automatically enforce relational database foreign-key constraints.

## 4. Embedding vs. Referencing

### Embedding

Embedding means storing related information inside the same document.

**Advantages:**
- Related data can be retrieved together.
- Fewer separate lookups may be required.
- Suitable for small, closely related data that is usually accessed together.

**Limitations:**
- Documents can grow as repeated data is added.
- Updating duplicated information can become difficult.

### Referencing

Referencing means storing an identifier that points to a document in another collection.

**Advantages:**
- Reduces unnecessary duplication.
- Supports large collections of readings.
- Keeps sensor details separate from measurement history.
- Makes it easier to maintain independent records.

**Limitations:**
- Related data may require additional queries or aggregation using `$lookup`.
- The application must maintain valid references.

## 5. Design Decision

Referencing is suitable for this project because sensor readings are numerous and grow over time. Keeping readings separate from sensor documents prevents sensor records from becoming excessively large.

Sensor information, alerts, and maintenance history are also stored separately because they represent different types of records.

Small pieces of information that are always accessed together could be embedded where appropriate, but the current design primarily uses references.

## 6. Indexing Strategy

Indexes help MongoDB find relevant documents without scanning the entire collection in many query scenarios.

The project includes indexes for relevant identifiers, time-based reading queries, alert filtering, and geospatial location data.

The compound index on `sensor_id` and `recorded_at` is intended to support queries that filter by sensor and sort or filter readings by time.

The `2dsphere` index on location coordinates supports compatible geospatial queries when valid GeoJSON coordinates are present.

Query execution plans and performance comparisons are documented in `INDEX_PERFORMANCE.md`.

## 7. Data Limitations

Most historical reading records were imported from Open-Meteo reanalysis data for Hyderabad, Pakistan. These records are historical weather data, not measurements from physical IoT devices.

Demonstration air-quality values should not be treated as verified live environmental measurements.

## 8. Conclusion

The schema separates sensor information, measurements, locations, alerts, and maintenance history into five collections. Referencing supports scalable reading storage, while suitable indexes improve query efficiency. Aggregation pipelines provide a way to analyze readings and generate summaries.
