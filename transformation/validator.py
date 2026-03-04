import pandas as pd

NULL_THRESHOLD = 0.30

def check_nulls(df):
    sensor_cols = ["water_temp", "air_temp", "wind_speed", "water_level", "air_pressure"]
    result = {}
    for col in sensor_cols:
        if col in df.columns:
            pct = df[col].isna().mean()
            result[col] = round(pct, 4)
            if pct > NULL_THRESHOLD:
                print(f"  ⚠️  High nulls in '{col}': {pct:.0%}")
    return result

def check_row_count(df, min_rows=10):
    ok = True
    for sid, group in df.groupby("station_id"):
        if len(group) < min_rows:
            print(f"  ⚠️  Station {sid} only has {len(group)} rows")
            ok = False
    return ok

def check_time_gaps(df, max_gap_minutes=60):
    gap_count = 0
    for _, group in df.groupby("station_id"):
        group = group.sort_values("timestamp")
        gaps = group["timestamp"].diff().dt.total_seconds() / 60
        gap_count += (gaps > max_gap_minutes).sum()
    if gap_count:
        print(f"  ⚠️  {gap_count} time gaps larger than {max_gap_minutes} mins")
    return gap_count

def compute_quality_score(df, outlier_count):
    sensor_cols = ["water_temp", "air_temp", "wind_speed", "water_level", "air_pressure"]
    existing = [c for c in sensor_cols if c in df.columns]
    total_cells = len(df) * len(existing)
    if total_cells == 0:
        return 0.0
    null_count = df[existing].isna().sum().sum()
    null_penalty    = (null_count / total_cells) * 40
    outlier_penalty = min((outlier_count / total_cells) * 30, 30)
    gap_count       = check_time_gaps(df)
    gap_penalty     = min(gap_count * 2, 30)
    score = round(max(100 - null_penalty - outlier_penalty - gap_penalty, 0), 2)
    print(f"  📊 Quality score: {score}/100")
    return score

def validate(df, outlier_count):
    print(f"  🔍 Validating {len(df)} rows...")
    check_nulls(df)
    check_row_count(df)
    score = compute_quality_score(df, outlier_count)
    sensor_cols = ["water_temp", "air_temp", "wind_speed", "water_level", "air_pressure"]
    existing = [c for c in sensor_cols if c in df.columns]
    null_count = df[existing].isna().sum().sum()
    return score, int(null_count)
