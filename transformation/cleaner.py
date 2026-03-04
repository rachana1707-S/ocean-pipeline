import pandas as pd

SENSOR_ERROR_VALUES = [999.0, 999.00, -999.0, 9999.0, -9999.0]

VALID_RANGES = {
    "water_temp":   (-2,  35),
    "air_temp":     (-30, 50),
    "wind_speed":   (0,   70),
    "water_level":  (-5,  15),
    "air_pressure": (870, 1084),
}

def remove_error_codes(df):
    for col in VALID_RANGES:
        if col in df.columns:
            df[col] = df[col].replace(SENSOR_ERROR_VALUES, pd.NA)
    return df

def remove_outliers(df):
    outlier_count = 0
    for col, (low, high) in VALID_RANGES.items():
        if col in df.columns:
            mask = df[col].notna() & ((df[col] < low) | (df[col] > high))
            outlier_count += mask.sum()
            df.loc[mask, col] = pd.NA
    return df, outlier_count

def remove_duplicates(df):
    before = len(df)
    df = df.drop_duplicates(subset=["station_id", "timestamp"], keep="first")
    dropped = before - len(df)
    if dropped:
        print(f"  🧹 Dropped {dropped} duplicate rows")
    return df

def fill_missing(df):
    sensor_cols = list(VALID_RANGES.keys())
    filled = []
    for station_id, group in df.groupby("station_id"):
        group = group.sort_values("timestamp")
        for col in sensor_cols:
            if col in group.columns:
                group[col] = group[col].ffill(limit=3)
        filled.append(group)
    return pd.concat(filled, ignore_index=True)

def clean(df):
    print(f"  🧹 Cleaning {len(df)} raw rows...")
    df = remove_error_codes(df)
    df, outlier_count = remove_outliers(df)
    df = remove_duplicates(df)
    df = fill_missing(df)
    print(f"  ✅ Cleaning done — {outlier_count} outliers replaced")
    return df, outlier_count
