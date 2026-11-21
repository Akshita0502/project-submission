import os
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Smart Home IoT Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp {background: #f5f7fb;}
    [data-testid="stMetric"] {
        background: white; padding: 16px 18px; border-radius: 12px;
        border: 1px solid #e7ebf2;
    }
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
    h1, h2, h3 {color: #17243a;}
    .small-note {color:#64748b; font-size:0.88rem;}
    div[data-testid="stAlert"] {border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

EXPECTED = [
    "timestamp", "device_id", "sensor_type", "room",
    "temperature_C", "humidity_pct", "value", "alert_flag"
]
BASE_DIR = Path(__file__).parent
DEFAULT_FILE = BASE_DIR / "Dataset expanded.csv"
if not DEFAULT_FILE.exists():
    for candidate in sorted(BASE_DIR.glob("*.csv")):
        name = candidate.name.lower()
        if "dataset" in name and "dictionary" not in name:
            DEFAULT_FILE = candidate
            break

BLUE = "#2563eb"
RED = "#dc2626"
NAVY = "#17243a"

@st.cache_data
def read_csv(file_obj_or_path):
    return pd.read_csv(file_obj_or_path)

def normalize_data(raw):
    missing = [c for c in EXPECTED if c not in raw.columns]
    if missing:
        raise ValueError("Dataset is missing required columns: " + ", ".join(missing))
    df = raw[EXPECTED].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in ["temperature_C", "humidity_pct", "value", "alert_flag"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["alert_flag"] = df["alert_flag"].fillna(0).astype(int)
    df["room"] = df["room"].fillna("Unknown").astype(str)
    df["device_id"] = df["device_id"].fillna("Unknown").astype(str)
    df["sensor_type"] = df["sensor_type"].fillna("Unknown").astype(str)
    df = df.dropna(subset=["timestamp"])
    return df.sort_values("timestamp")

def style(fig, x_title, y_title):
    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_color=NAVY,
        margin=dict(l=10, r=10, t=50, b=10),
        height=360,
    )
    fig.update_xaxes(gridcolor="#eef1f6")
    fig.update_yaxes(gridcolor="#eef1f6")
    return fig

st.title("🏠 Smart Home IoT Monitoring")
st.caption("IoT Based Smart Home Automation System | Embedded IoT")

with st.sidebar:
    st.header("Dashboard controls")
    uploaded = st.file_uploader("Upload sensor dataset (CSV)", type=["csv"])
    st.caption("Expected schema: the eight columns in your project data dictionary.")
    if uploaded is not None:
        raw = read_csv(uploaded)
        source_label = uploaded.name
    elif DEFAULT_FILE.exists():
        raw = read_csv(str(DEFAULT_FILE))
        source_label = DEFAULT_FILE.name
    else:
        raw = None
        source_label = "No dataset loaded"

    st.divider()
    st.subheader("Filters")
    st.caption("Filters are applied to the dataset currently loaded.")

if raw is None:
    st.warning("Upload Dataset expanded.csv from the sidebar to begin.")
    st.stop()

try:
    data = normalize_data(raw)
except Exception as exc:
    st.error(str(exc))
    st.stop()

with st.sidebar:
    rooms = sorted(data["room"].dropna().unique().tolist())
    selected_rooms = st.multiselect("Room", rooms, default=rooms)
    sensors = sorted(data["sensor_type"].dropna().unique().tolist())
    selected_sensors = st.multiselect("Sensor type", sensors, default=sensors)
    devices = sorted(data["device_id"].dropna().unique().tolist())
    selected_devices = st.multiselect("Device ID", devices, default=devices)
    min_date = data["timestamp"].min().date()
    max_date = data["timestamp"].max().date()
    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.info("Select both a start date and an end date in the sidebar.")
    st.stop()

start_date, end_date = date_range
mask = (
    data["room"].isin(selected_rooms)
    & data["sensor_type"].isin(selected_sensors)
    & data["device_id"].isin(selected_devices)
    & (data["timestamp"].dt.date >= start_date)
    & (data["timestamp"].dt.date <= end_date)
)
fdf = data[mask]

if fdf.empty:
    st.warning("No records match the selected filters. Adjust the filters in the sidebar.")
    st.stop()

st.markdown(f"<span class='small-note'>Data source: {source_label}</span>", unsafe_allow_html=True)

alerts = int(fdf["alert_flag"].sum())
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Records", f"{len(fdf):,}")
c2.metric("Avg temperature (°C)", f"{fdf['temperature_C'].mean():.1f}")
c3.metric("Avg humidity (%)", f"{fdf['humidity_pct'].mean():.1f}")
c4.metric("Alerts", f"{alerts:,}")
c5.metric("Alert rate", f"{alerts / len(fdf) * 100:.2f}%")

tab_overview, tab_alerts, tab_data = st.tabs(["Overview", "Alerts", "Data"])

with tab_overview:
    left, right = st.columns(2)
    with left:
        fig = px.histogram(fdf, x="temperature_C", nbins=20, title="Temperature distribution",
                           color_discrete_sequence=[BLUE])
        fig.update_traces(marker_line_color="white", marker_line_width=1)
        st.plotly_chart(style(fig, "Temperature (°C)", "Frequency"))
    with right:
        room_hum = fdf.groupby("room", as_index=False)["humidity_pct"].mean().round(2)
        fig = px.bar(room_hum, x="room", y="humidity_pct", title="Average humidity by room",
                     color_discrete_sequence=[BLUE], text="humidity_pct")
        fig.update_traces(textposition="outside")
        st.plotly_chart(style(fig, "Room", "Humidity (%)"))

    left, right = st.columns(2)
    with left:
        daily = (
            fdf.set_index("timestamp")[["temperature_C", "humidity_pct"]]
            .resample("D").mean().dropna().reset_index()
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily["timestamp"], y=daily["temperature_C"].round(2),
                                 mode="lines+markers", name="Temperature (°C)",
                                 line=dict(color=BLUE)))
        fig.update_layout(title="Daily average temperature")
        st.plotly_chart(style(fig, "Date", "Temperature (°C)"))
    with right:
        counts = fdf["alert_flag"].value_counts().sort_index().reset_index()
        counts.columns = ["alert_flag", "records"]
        counts["alert_flag"] = counts["alert_flag"].map({0: "0 (no alert)", 1: "1 (alert)"})
        fig = px.bar(counts, x="alert_flag", y="records", title="Alert flag counts",
                     color="alert_flag",
                     color_discrete_map={"0 (no alert)": BLUE, "1 (alert)": RED}, text="records")
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(style(fig, "Alert flag", "Records"))

with tab_alerts:
    alert_df = fdf[fdf["alert_flag"] == 1]
    if alert_df.empty:
        st.info("No alerts in the current selection.")
    else:
        left, right = st.columns(2)
        with left:
            by_sensor = alert_df.groupby("sensor_type", as_index=False).size().rename(columns={"size": "alerts"})
            fig = px.bar(by_sensor, x="sensor_type", y="alerts", title="Alerts by sensor type",
                         color_discrete_sequence=[RED], text="alerts")
            fig.update_traces(textposition="outside")
            st.plotly_chart(style(fig, "Sensor type", "Alerts"))
        with right:
            by_room = alert_df.groupby("room", as_index=False).size().rename(columns={"size": "alerts"})
            fig = px.bar(by_room, x="room", y="alerts", title="Alerts by room",
                         color_discrete_sequence=[RED], text="alerts")
            fig.update_traces(textposition="outside")
            st.plotly_chart(style(fig, "Room", "Alerts"))
        st.subheader("Most recent alerts")
        st.dataframe(alert_df.sort_values("timestamp", ascending=False).head(25), hide_index=True)

with tab_data:
    st.dataframe(fdf, hide_index=True)
    st.download_button(
        "Download filtered data (CSV)",
        fdf.to_csv(index=False).encode("utf-8"),
        file_name="filtered_smart_home_data.csv",
        mime="text/csv",
    )

st.markdown(
    "<span class='small-note'>The expanded dataset includes synthetic generated records. Charts describe the "
    "dataset only and do not establish physical sensor accuracy or prove that a prototype is operating.</span>",
    unsafe_allow_html=True,
)
