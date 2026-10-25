# IoT Sensor Monitor — Weather & Air-Quality Tracker

## Project Overview

IoT Sensor Monitor is a database-driven application developed using Flask and MongoDB. It provides a dashboard for monitoring sensor information, weather readings, air-quality indicators, alerts, and analytical summaries.

The project demonstrates database design, CRUD operations, aggregation pipelines, indexing, and query performance analysis.

## Objectives

- Store and manage sensor information using MongoDB.
- Record and analyze weather and air-quality-related readings.
- Perform CRUD operations on sensor records.
- Use aggregation pipelines to summarize and analyze data.
- Improve query efficiency using MongoDB indexes.
- Display sensor and analytics information through a Flask dashboard.

## Technologies Used

- **Backend:** Python, Flask
- **Database:** MongoDB Atlas
- **Database Library:** PyMongo
- **Frontend:** HTML, CSS
- **Configuration:** python-dotenv
- **Data Import:** Python Requests

## Main Features

- Sensor management: Create, read, update, and delete sensor records.
- Sensor dashboard: View sensor information and summary statistics.
- Reading history: Retrieve recent sensor readings.
- Alerts: View stored alerts.
- Data analytics: Analyze temperature, humidity, and reading trends.
- Aggregation pipelines: Perform grouping, counting, summarization, and bucketing.
- Index performance analysis: Compare indexed queries with collection scans.
- Geospatial indexing: Includes a 2dsphere index for location-related queries.

## Database Collections

The database contains five collections:

1. **sensors** — sensor identifiers, names, types, status, and installation details.
2. **readings** — recorded weather and sensor measurements with timestamps.
3. **locations** — location information associated with sensors.
4. **alerts** — alert details, severity, and status.
5. **maintenance_logs** — sensor maintenance records.

## Data and Testing Notes

The development database contains more than 1,000 reading documents. Most historical weather records were imported from Open-Meteo reanalysis data for Hyderabad, Pakistan. A small number of demonstration records are also included.

**Important:** These historical and demonstration records are not measurements from physical IoT hardware or a live air-quality monitoring device. Air-quality values in demonstration records should not be interpreted as verified real-time environmental measurements.

The project includes five MongoDB aggregation pipeline tests and index-performance comparisons documented in `INDEX_PERFORMANCE.md`.

## Project Structure

```text
IoT-Sensor-Monitor/
├── app.py
├── crud_routes.py
├── aggregation_tests.py
├── import_weather_data.py
├── INDEX_PERFORMANCE.md
├── requirements.txt
├── .env.example
├── .gitignore
└── templates/
    └── index.html
```

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/maryamakram-prog/IoT-Sensor-Monitor.git
cd IoT-Sensor-Monitor
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a template:

```text
MONGO_URI=your_mongodb_atlas_connection_string
MONGO_DB=IoTSensorMonitor
```

Replace the placeholder with your own MongoDB Atlas connection string. Never publish database passwords or real connection strings.

### 5. Run the application

```bash
python app.py
```

Open the local URL displayed by Flask, usually:

`http://127.0.0.1:5000`

## Database and Performance Work

The project demonstrates:

- CRUD operations for sensor records.
- Five aggregation pipeline examples.
- Compound and other indexes for relevant collections.
- Query execution-plan comparisons using MongoDB `explain`.
- A geospatial index on location data.

See `INDEX_PERFORMANCE.md` for the recorded performance tests.

## Limitations

- The current dataset primarily uses historical weather data and demonstration records.
- Physical IoT hardware and verified live air-quality sensor integration are not included.
- Deployment and live public access must be configured separately if required.

## Future Improvements

- Integrate physical IoT sensors.
- Add a verified live air-quality data source.
- Implement automated alert generation.
- Add authentication and role-based access.
- Deploy the application to a public hosting platform.

##
