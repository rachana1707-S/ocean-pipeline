import os
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("NOAA_API_BASE")

STATIONS = {
    "8443970": "Boston Harbor",
    "8447930": "Woods Hole",
    "8638610": "Sewells Point",
    "8720218": "Mayport",
    "8534720": "Atlantic City",
}

# NOAA product codes
PRODUCTS = {
    "water_temp":    "water_temperature",
    "air_temp":      "air_temperature",
    "wind_speed":    "wind",
    "water_level":   "water_level",
    "air_pressure":  "air_pressure",
}


def fetch_product(station_id: str, product: str, start: str, end: str) -> pd.DataFrame:
    """Fetch a single product for a single station from NOAA API."""
    params = {
        "station":   station_id,
        "product":   product,
        "begin_date": start,
        "end_date":  end,
        "datum":     "MLLW",
        "time_zone": "GMT",
        "units":     "metric",
        "format":    "json",
        "application": "ocean_pipeline"
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        print(f" {station_id} / {product}: {data['error'].get('message', 'unknown error')}")
        return pd.DataFrame()

    rows = data.get("data", [])
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # NOAA sometimes returns different column names depending on the product
    # wind returns: 's' (speed), 'd' (direction), 'dr' (direction label)
    # all others return: 'v' (value)
    if "v" in df.columns:
        val_col = "v"
    elif "s" in df.columns:
        val_col = "s"   # wind speed
    else:
        print(f"Unexpected columns from NOAA: {list(df.columns)}")
        return pd.DataFrame()

    df["t"] = pd.to_datetime(df["t"])
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
    return df[["t", val_col]].rename(columns={"t": "timestamp", val_col: product})


def fetch_station(station_id: str, days_back: int = 30) -> pd.DataFrame:
    """Fetch all products for one station and merge into a single DataFrame."""
    end   = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)
    s_str = start.strftime("%Y%m%d")
    e_str = end.strftime("%Y%m%d")

    print(f"Fetching station {station_id} ({STATIONS[station_id]})...")

    frames = []
    for col, product in PRODUCTS.items():
        df = fetch_product(station_id, product, s_str, e_str)
        if not df.empty:
            df = df.rename(columns={product: col})
            frames.append(df.set_index("timestamp"))

    if not frames:
        print(f"No data returned for {station_id}")
        return pd.DataFrame()

    # Merge all products on timestamp
    merged = frames[0]
    for f in frames[1:]:
        merged = merged.join(f, how="outer")

    merged = merged.reset_index()
    merged["station_id"] = station_id
    return merged


def fetch_all_stations(days_back: int = 30) -> pd.DataFrame:
    """Fetch data for all stations and combine into one DataFrame."""
    all_frames = []
    for station_id in STATIONS:
        df = fetch_station(station_id, days_back)
        if not df.empty:
            all_frames.append(df)

    if not all_frames:
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    print(f"\n Total raw rows fetched: {len(combined)}")
    return combined


if __name__ == "__main__":
    df = fetch_all_stations(days_back=7)
    print(df.head())
    print(df.dtypes)