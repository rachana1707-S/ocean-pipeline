import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_client import read_sensor_readings, read_pipeline_runs, read_quality_log

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ocean Sensor Dashboard",
    page_icon="🌊",
    layout="wide"
)

# ── Custom CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0a1628; }
    .block-container { padding-top: 1rem; }
    h1, h2, h3 { color: #4fc3f7; }
    .metric-card {
        background: linear-gradient(135deg, #0d2137, #1a3a5c);
        border: 1px solid #1e88e5;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    [data-testid="stMetricValue"] { color: #4fc3f7; font-size: 2rem; }
    [data-testid="stMetricLabel"] { color: #90caf9; }
</style>
""", unsafe_allow_html=True)


# ── Load data ──────────────────────────────────────────────────────
@st.cache_data(ttl=300)  # refresh cache every 5 minutes
def load_data():
    df      = read_sensor_readings()
    runs    = read_pipeline_runs()
    quality = read_quality_log()
    return df, runs, quality

df, runs, quality = load_data()

# ── Header ─────────────────────────────────────────────────────────
st.title("🌊 Ocean Sensor Data Pipeline")
st.caption("Live buoy data from NOAA CO-OPS — East Coast stations")
st.divider()

# ══════════════════════════════════════════════════════════════════
# SECTION 1 — Pipeline Health KPIs
# ══════════════════════════════════════════════════════════════════
st.subheader("📡 Pipeline Health")

k1, k2, k3, k4, k5 = st.columns(5)

last_run    = runs.iloc[0] if not runs.empty else None
total_rows  = len(df)
avg_quality = quality["quality_score"].mean() if not quality.empty else 0
stations    = df["station_id"].nunique() if not df.empty else 0
last_ts     = df["timestamp"].max() if not df.empty else "N/A"

k1.metric("Total Rows Ingested",  f"{total_rows:,}")
k2.metric("Active Stations",      f"{stations}")
k3.metric("Avg Quality Score",    f"{avg_quality:.1f}/100")
k4.metric("Last Pipeline Status", last_run["status"].upper() if last_run is not None else "N/A")
k5.metric("Latest Reading",       pd.to_datetime(last_ts).strftime("%b %d %H:%M") if last_ts != "N/A" else "N/A")

st.divider()

# ══════════════════════════════════════════════════════════════════
# SECTION 2 — Station Map
# ══════════════════════════════════════════════════════════════════
st.subheader("🗺️ Station Map")

# Get latest reading per station for the map
latest = (
    df.sort_values("timestamp")
      .groupby("station_id")
      .last()
      .reset_index()
)

if not latest.empty:
    fig_map = px.scatter_mapbox(
        latest,
        lat="latitude", lon="longitude",
        color="water_temp_c",
        size=[15] * len(latest),
        hover_name="name",
        hover_data={
            "water_temp_c": ":.1f",
            "air_temp_c":   ":.1f",
            "water_level_m":":.2f",
            "latitude": False,
            "longitude": False
        },
        color_continuous_scale="Turbo",
        labels={"water_temp_c": "Water Temp (°C)"},
        mapbox_style="carto-darkmatter",
        zoom=4,
        center={"lat": 38.5, "lon": -74.5},
        title="Latest Water Temperature by Station"
    )
    fig_map.update_layout(
        height=450,
        margin={"r":0,"t":40,"l":0,"b":0},
        paper_bgcolor="#0a1628",
        font_color="#90caf9"
    )
    st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# SECTION 3 — Time Series Charts
# ══════════════════════════════════════════════════════════════════
st.subheader("📈 Sensor Readings Over Time")

col_left, col_right = st.columns([1, 3])

with col_left:
    selected_stations = st.multiselect(
        "Select Stations",
        options=df["name"].unique().tolist(),
        default=df["name"].unique().tolist()
    )
    metric = st.selectbox("Select Metric", [
        "water_temp_c",
        "air_temp_c",
        "wind_speed_ms",
        "water_level_m",
        "air_pressure_mb"
    ], format_func=lambda x: {
        "water_temp_c":    "🌡️ Water Temp (°C)",
        "air_temp_c":      "🌡️ Air Temp (°C)",
        "wind_speed_ms":   "💨 Wind Speed (m/s)",
        "water_level_m":   "🌊 Water Level (m)",
        "air_pressure_mb": "🌬️ Air Pressure (mb)"
    }[x])
    days = st.slider("Days to show", 1, 30, 7)

with col_right:
    filtered = df[
        (df["name"].isin(selected_stations)) &
        (df["timestamp"] >= pd.Timestamp.now() - pd.Timedelta(days=days))
    ]

    if not filtered.empty:
        fig_ts = px.line(
            filtered.sort_values("timestamp"),
            x="timestamp", y=metric,
            color="name",
            labels={metric: metric.replace("_", " ").title(), "name": "Station"},
            template="plotly_dark"
        )
        fig_ts.update_layout(
            height=380,
            paper_bgcolor="#0a1628",
            plot_bgcolor="#0d2137",
            legend=dict(orientation="h", y=-0.2),
            margin={"t": 20}
        )
        fig_ts.update_traces(line=dict(width=1.5))
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("No data for selected filters.")

st.divider()

# ══════════════════════════════════════════════════════════════════
# SECTION 4 — Station Comparison
# ══════════════════════════════════════════════════════════════════
st.subheader("📊 Station Comparison")

c1, c2 = st.columns(2)

with c1:
    # Average water temp per station — bar chart
    avg_temp = (
        df.groupby("name")["water_temp_c"]
          .mean()
          .reset_index()
          .rename(columns={"water_temp_c": "avg_water_temp"})
          .sort_values("avg_water_temp", ascending=True)
    )
    fig_bar = px.bar(
        avg_temp,
        x="avg_water_temp", y="name",
        orientation="h",
        color="avg_water_temp",
        color_continuous_scale="Blues",
        labels={"avg_water_temp": "Avg Water Temp (°C)", "name": ""},
        title="Average Water Temperature by Station",
        template="plotly_dark"
    )
    fig_bar.update_layout(
        paper_bgcolor="#0a1628",
        plot_bgcolor="#0d2137",
        showlegend=False,
        height=320,
        margin={"t": 40}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    # Wind speed distribution — histogram
    wind_df = df[df["wind_speed_ms"].notna()]
    if not wind_df.empty:
        fig_hist = px.histogram(
            wind_df,
            x="wind_speed_ms",
            color="name",
            nbins=30,
            labels={"wind_speed_ms": "Wind Speed (m/s)", "name": "Station"},
            title="Wind Speed Distribution",
            template="plotly_dark",
            barmode="overlay",
            opacity=0.7
        )
        fig_hist.update_layout(
            paper_bgcolor="#0a1628",
            plot_bgcolor="#0d2137",
            height=320,
            margin={"t": 40}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("No wind speed data available.")

st.divider()

# ══════════════════════════════════════════════════════════════════
# SECTION 5 — Water Level Tidal Pattern
# ══════════════════════════════════════════════════════════════════
st.subheader("🌊 Tidal Patterns — Water Level")

tide_station = st.selectbox(
    "Select station for tidal view",
    options=df["name"].unique().tolist(),
    key="tide_select"
)

tide_df = df[
    (df["name"] == tide_station) &
    (df["timestamp"] >= pd.Timestamp.now() - pd.Timedelta(days=3))
].sort_values("timestamp")

if not tide_df.empty:
    fig_tide = go.Figure()
    fig_tide.add_trace(go.Scatter(
        x=tide_df["timestamp"],
        y=tide_df["water_level_m"],
        fill="tozeroy",
        fillcolor="rgba(30, 136, 229, 0.2)",
        line=dict(color="#1e88e5", width=2),
        name="Water Level"
    ))
    fig_tide.update_layout(
        height=300,
        paper_bgcolor="#0a1628",
        plot_bgcolor="#0d2137",
        font_color="#90caf9",
        xaxis_title="Time",
        yaxis_title="Water Level (m)",
        margin={"t": 20}
    )
    st.plotly_chart(fig_tide, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# SECTION 6 — Data Quality Log
# ══════════════════════════════════════════════════════════════════
st.subheader("🔍 Data Quality Log")

q1, q2 = st.columns(2)

with q1:
    if not quality.empty:
        fig_quality = px.line(
            quality.sort_values("checked_at"),
            x="checked_at", y="quality_score",
            color="station_id",
            labels={"quality_score": "Quality Score", "checked_at": "Time"},
            title="Quality Score Over Time",
            template="plotly_dark"
        )
        fig_quality.update_layout(
            paper_bgcolor="#0a1628",
            plot_bgcolor="#0d2137",
            height=300,
            margin={"t": 40}
        )
        st.plotly_chart(fig_quality, use_container_width=True)

with q2:
    if not runs.empty:
        display_runs = runs[["ran_at", "status", "rows_ingested"]].head(10).copy()
        display_runs["ran_at"] = pd.to_datetime(display_runs["ran_at"]).dt.strftime("%b %d %H:%M")
        display_runs["status"] = display_runs["status"].apply(
            lambda x: "success" if x == "success" else " failed"
        )
        st.markdown("**Recent Pipeline Runs**")
        st.dataframe(display_runs, use_container_width=True, hide_index=True)

st.divider()
st.caption("🌊 Ocean Sensor Data Pipeline — Built with NOAA CO-OPS API, PostgreSQL & Streamlit")