import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    url = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return create_engine(url)

def write_sensor_readings(df: pd.DataFrame):
    engine = get_engine()
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO sensor_readings
                    (station_id, timestamp, water_temp_c, air_temp_c,
                     wind_speed_ms, water_level_m, air_pressure_mb)
                VALUES
                    (:station_id, :timestamp, :water_temp_c, :air_temp_c,
                     :wind_speed_ms, :water_level_m, :air_pressure_mb)
                ON CONFLICT (station_id, timestamp) DO NOTHING
            """), row.to_dict())
    print(f"Wrote {len(df)} rows to sensor_readings")

def log_quality(station_id, total, nulls, outliers, score):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO data_quality_log
                (station_id, total_rows, null_count, outlier_count, quality_score)
            VALUES (:sid, :total, :nulls, :outliers, :score)
        """), {"sid": station_id, "total": int(total), "nulls": int(nulls),
               "outliers": int(outliers), "score": float(score)})

def log_pipeline_run(status, rows_ingested, error_message=None):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_runs (status, rows_ingested, error_message)
            VALUES (:status, :rows, :err)
        """), {"status": status, "rows": rows_ingested, "err": error_message})

def read_sensor_readings() -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql("""
        SELECT r.*, s.name, s.state, s.latitude, s.longitude
        FROM sensor_readings r
        JOIN stations s USING (station_id)
        ORDER BY timestamp DESC
    """, engine)

def read_pipeline_runs() -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql("SELECT * FROM pipeline_runs ORDER BY ran_at DESC LIMIT 20", engine)

def read_quality_log() -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql("SELECT * FROM data_quality_log ORDER BY checked_at DESC LIMIT 50", engine)
