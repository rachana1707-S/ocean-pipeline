# 🌊 Ocean Sensor Data Pipeline

A production grade end to end data engineering pipeline that ingests real time ocean buoy sensor data from NOAA CO-OPS, validates and transforms it, stores it in PostgreSQL, and displays it on an interactive analytics dashboard. Fully containerized with Docker.

> Built to demonstrate core data engineering skills in the context of marine and ocean technology.

---

## 📸 Dashboard Preview

*Screenshot coming soon*

---

## Architecture

```
NOAA CO-OPS API  (5 live East Coast buoy stations)
        │
        ▼
  noaa_fetcher.py          Extract: raw JSON to pandas DataFrame
        │
        ▼
  cleaner.py               Remove sensor error codes, outliers, duplicates
        │
        ▼
  validator.py             Score data quality per batch (0 to 100)
        │
        ▼
  transformer.py           Add season, wind category, heat index columns
        │
        ▼
  PostgreSQL 15            Persistent structured storage
        │
        ▼
  Streamlit + Plotly       Interactive dashboard with maps, time series, and KPIs
```

---

## Data Source

Live data is pulled from the **[NOAA CO-OPS API](https://api.tidesandcurrents.noaa.gov/api/prod/)** with no API key required.

### Monitored Stations

| Station ID | Location | State |
|---|---|---|
| 8443970 | Boston Harbor | MA |
| 8447930 | Woods Hole | MA |
| 8638610 | Sewells Point | VA |
| 8720218 | Mayport | FL |
| 8534720 | Atlantic City | NJ |

### Collected Metrics

| Metric | Unit | Description |
|---|---|---|
| Water Temperature | °C | Sea surface temperature |
| Air Temperature | °C | Atmospheric temperature at station |
| Wind Speed | m/s | Surface wind speed |
| Water Level | m | Tidal water level (MLLW datum) |
| Air Pressure | mb | Barometric pressure |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Ingestion | Python 3.11, requests |
| Transformation | pandas, numpy |
| Validation | Custom quality scoring engine |
| Storage | PostgreSQL 15 |
| Dashboard | Streamlit, Plotly |
| Scheduling | APScheduler |
| Containerization | Docker, Docker Compose |

---

## Project Structure

```
ocean-pipeline/
│
├── docker-compose.yml          Service orchestration
├── Dockerfile.pipeline         Pipeline container definition
├── Dockerfile.dashboard        Dashboard container definition
├── requirements.txt            Python dependencies
├── .env                        Environment variables (not committed)
├── .gitignore
│
├── ingestion/
│   ├── noaa_fetcher.py         NOAA API client that fetches all products per station
│   └── scheduler.py            Pipeline orchestrator with hourly scheduling
│
├── transformation/
│   ├── cleaner.py              Null handling, error code replacement, deduplication
│   ├── validator.py            Quality checks, null thresholds, gap detection
│   └── transformer.py         Feature engineering and unit normalization
│
├── database/
│   ├── db_client.py            SQLAlchemy read and write interface
│   ├── models.py               Table definitions
│   └── init.sql                Schema initialization script
│
└── dashboard/
    └── app.py                  Streamlit application
```

---

## Getting Started

### Prerequisites

Docker Desktop installed and running and Python 3.11 or above.

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ocean-pipeline.git
cd ocean-pipeline
```

### 2. Start all services

```bash
docker compose up --build
```

This starts three services in order. PostgreSQL on port 5432 initializes the schema automatically on first boot. The pipeline runs immediately on startup then every hour after that. The dashboard is available at [http://localhost:8501](http://localhost:8501).

### 3. Run the pipeline manually during local development

```bash
# Switch POSTGRES_HOST to localhost in .env first
python3 -c "from ingestion.scheduler import run_pipeline; run_pipeline()"
```

### 4. Run the dashboard locally

```bash
streamlit run dashboard/app.py
```

---

## Database Schema

```sql
stations (
    station_id      VARCHAR PRIMARY KEY,
    name            VARCHAR,
    state           VARCHAR,
    latitude        NUMERIC,
    longitude       NUMERIC
)

sensor_readings (
    id              SERIAL PRIMARY KEY,
    station_id      VARCHAR REFERENCES stations,
    timestamp       TIMESTAMP,
    water_temp_c    NUMERIC,
    air_temp_c      NUMERIC,
    wind_speed_ms   NUMERIC,
    water_level_m   NUMERIC,
    air_pressure_mb NUMERIC,
    ingested_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(station_id, timestamp)
)

data_quality_log (
    station_id      VARCHAR,
    checked_at      TIMESTAMP,
    total_rows      INTEGER,
    null_count      INTEGER,
    outlier_count   INTEGER,
    quality_score   NUMERIC
)

pipeline_runs (
    ran_at          TIMESTAMP,
    status          VARCHAR,
    rows_ingested   INTEGER,
    error_message   TEXT
)
```

---

## Dashboard Features

| Feature | Description |
|---|---|
| Pipeline Health KPIs | Total rows ingested, active stations, average quality score, last run status |
| Station Map | Interactive map colored by latest water temperature |
| Time Series View | Per metric line charts with station filter and date range selector |
| Station Comparison | Average temperature bar chart and wind speed distribution |
| Tidal Patterns | Area chart showing water level changes over 72 hours |
| Data Quality Log | Quality score trends and recent pipeline run history |

---

## Pipeline Behavior

- Runs automatically every hour using APScheduler
- Fetches the last 2 days of data on each run
- Skips duplicate rows using ON CONFLICT DO NOTHING
- Forward fills gaps of up to 3 consecutive missing readings
- Replaces NOAA sensor error codes like 999.0 and -999.0 with NULL
- Logs every run to the pipeline_runs table with status, row count, and any errors

---

## Data Quality Scoring

Each batch is automatically scored from 0 to 100 based on three factors.

| Factor | Max Penalty |
|---|---|
| Null or missing value percentage | 40 points |
| Outlier readings detected | 30 points |
| Time gaps exceeding 60 minutes | 30 points |

Typical observed score is 92 out of 100. The 8 point deduction is expected because most stations do not operate wind sensors.

---

## Roadmap

- AI powered anomaly alerts with natural language explanations
- Automated daily ocean condition reports generated by an LLM
- Natural language query interface to ask questions about the data
- 24 hour predictive forecasting based on historical trends
- AUV telemetry data ingestion with mission replay and CTD sync
- Cloud deployment on AWS using RDS, ECS, and CloudFront

---

## Author

**Rachana Sudhakar**
MS Computer Science, Northeastern University
Robotics Software Engineering Intern at Orpheus Ocean
[sudhakar.r@northeastern.edu](mailto:sudhakar.r@northeastern.edu)
