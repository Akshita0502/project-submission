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
DEFAULT_FILE = Path(__file__).parent / "Dataset expanded.csv"

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
        source_label = "Dataset expanded.csv"
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
