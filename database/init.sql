-- ── Stations: buoy metadata ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS stations (
    station_id      VARCHAR(20) PRIMARY KEY,
    name            VARCHAR(100),
    state           VARCHAR(50),
    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6)
);

-- Pre-load our 5 East Coast stations
INSERT INTO stations VALUES
    ('8443970', 'Boston Harbor',         'MA', 42.353, -71.047),
    ('8447930', 'Woods Hole',            'MA', 41.523, -70.671),
    ('8638610', 'Sewells Point',         'VA', 36.947, -76.330),
    ('8720218', 'Mayport',               'FL', 30.397, -81.430),
    ('8534720', 'Atlantic City',         'NJ', 39.355, -74.418)
ON CONFLICT DO NOTHING;

-- ── Raw sensor readings ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sensor_readings (
    id              SERIAL PRIMARY KEY,
    station_id      VARCHAR(20) REFERENCES stations(station_id),
    timestamp       TIMESTAMP NOT NULL,
    water_temp_c    NUMERIC(6,2),
    air_temp_c      NUMERIC(6,2),
    wind_speed_ms   NUMERIC(6,2),
    water_level_m   NUMERIC(7,3),
    air_pressure_mb NUMERIC(8,2),
    ingested_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(station_id, timestamp)         -- prevent duplicate rows
);

-- ── Data quality log ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS data_quality_log (
    id              SERIAL PRIMARY KEY,
    station_id      VARCHAR(20),
    checked_at      TIMESTAMP DEFAULT NOW(),
    total_rows      INTEGER,
    null_count      INTEGER,
    outlier_count   INTEGER,
    quality_score   NUMERIC(5,2)          -- 0 to 100
);

-- ── Pipeline run audit log ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              SERIAL PRIMARY KEY,
    ran_at          TIMESTAMP DEFAULT NOW(),
    status          VARCHAR(20),          -- 'success' or 'failed'
    rows_ingested   INTEGER,
    error_message   TEXT
);