import pandas as pd
import numpy as np

def add_time_features(df):
    df["hour"]  = df["timestamp"].dt.hour
    df["month"] = df["timestamp"].dt.month
    df["time_of_day"] = pd.cut(
        df["hour"],
        bins=[-1, 5, 11, 16, 20, 23],
        labels=["night", "morning", "afternoon", "evening", "night2"]
    ).astype(str).replace("night2", "night")
    df["season"] = df["month"].map({
        12:"winter",1:"winter",2:"winter",
        3:"spring",4:"spring",5:"spring",
        6:"summer",7:"summer",8:"summer",
        9:"autumn",10:"autumn",11:"autumn"
    })
    return df

def add_heat_index(df):
    if "air_temp_c" not in df.columns or "water_temp_c" not in df.columns:
        return df
    mask = df["air_temp_c"].notna() & df["water_temp_c"].notna() & (df["air_temp_c"] > 27)
    df["heat_index_c"] = np.nan
    df.loc[mask, "heat_index_c"] = (
        df.loc[mask, "air_temp_c"] + 0.33 * (df.loc[mask, "water_temp_c"] * 0.1) - 4
    ).round(2)
    return df

def add_wind_category(df):
    if "wind_speed_ms" not in df.columns:
        return df
    df["wind_category"] = pd.cut(
        df["wind_speed_ms"],
        bins=[-1, 1.5, 5.4, 10.7, 17.1, 24.4, 70],
        labels=["calm","light","moderate","fresh","strong","storm"]
    ).astype(str)
    return df

def rename_for_db(df):
    rename_map = {
        "water_temp":   "water_temp_c",
        "air_temp":     "air_temp_c",
        "wind_speed":   "wind_speed_ms",
        "water_level":  "water_level_m",
        "air_pressure": "air_pressure_mb",
    }
    rename_map = {k:v for k,v in rename_map.items() if k in df.columns}
    return df.rename(columns=rename_map)

def transform(df):
    print(f" Transforming {len(df)} rows...")
    df = rename_for_db(df)
    df = add_time_features(df)
    df = add_heat_index(df)
    df = add_wind_category(df)
    print(f"Transformation done")
    return df
