import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.blocking import BlockingScheduler
from ingestion.noaa_fetcher import fetch_all_stations
from transformation.cleaner import clean
from transformation.validator import validate
from transformation.transformer import transform
from database.db_client import write_sensor_readings, log_quality, log_pipeline_run


def run_pipeline():
    print("\n" + "="*50)
    print("🌊 Pipeline run starting...")
    print("="*50)

    rows_ingested = 0
    try:
        raw_df = fetch_all_stations(days_back=2)
        if raw_df.empty:
            print("No data fetched — skipping run")
            log_pipeline_run("failed", 0, "No data returned from NOAA")
            return

        cleaned_df, outlier_count = clean(raw_df)
        quality_score, null_count = validate(cleaned_df, outlier_count)
        final_df = transform(cleaned_df)

        db_cols = ["station_id", "timestamp", "water_temp_c", "air_temp_c",
                   "wind_speed_ms", "water_level_m", "air_pressure_mb"]
        db_cols = [c for c in db_cols if c in final_df.columns]
        write_sensor_readings(final_df[db_cols])
        rows_ingested = len(final_df)

        for sid, group in final_df.groupby("station_id"):
            log_quality(
                station_id=sid,
                total=len(group),
                nulls=null_count,
                outliers=outlier_count,
                score=quality_score
            )

        log_pipeline_run("success", rows_ingested)
        print(f"\nPipeline complete — {rows_ingested} rows ingested")

    except Exception as e:
        print(f"\nPipeline failed: {e}")
        log_pipeline_run("failed", rows_ingested, str(e))


if __name__ == "__main__":
    run_pipeline()

    scheduler = BlockingScheduler()
    scheduler.add_job(run_pipeline, "interval", hours=1)
    print("\n Scheduler running — next run in 1 hour. Press Ctrl+C to stop.")
    scheduler.start()
