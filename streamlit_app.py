import os
import io
import requests
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
from streamlit_searchbox import st_searchbox

load_dotenv()

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="SensorSense | IoT Monitoring",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# DESIGN SYSTEM (Dark: black + navy)
# =====================================================
PRIMARY = "#2dd4bf"
PRIMARY_HOVER = "#5eead4"
ACCENT = "#60a5fa"
PALETTE = ["#2dd4bf", "#60a5fa", "#f59e0b", "#f472b6", "#a78bfa", "#84cc16"]
CARD_BG = "#0c1630"
BG_COLOR = "#050914"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #2dd4bf;
    --primary-hover: #5eead4;
    --primary-soft: rgba(45, 212, 191, .12);
    --accent: #60a5fa;
    --ink: #f1f5f9;
    --text: #cbd5e1;
    --muted: #7c8ba6;
    --line: #1c2b4a;
    --bg: #050914;
    --card: #0c1630;
    --card-2: #101d3b;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--text); }
.stApp { background: var(--bg); }
header[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }
[data-testid="stAppDeployButton"], .stDeployButton { display: none !important; }
.block-container { padding: 2rem 2.5rem 3rem; max-width: 1500px; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #03060e 0%, #0a1733 100%);
    border-right: 1px solid #1c2b4a;
}
section[data-testid="stSidebar"] * { color: #cbd5e1; }
section[data-testid="stSidebar"] hr { border-color: rgba(148, 163, 184, .15); margin: 16px 0; }

.brand { font-size: 26px; font-weight: 800; letter-spacing: -1px; color: #ffffff !important; }
.brand span { color: #2dd4bf !important; }
.brand-subtitle { color: #64748b !important; font-size: 10px; letter-spacing: 2px; margin: 4px 0 26px; }
.sidebar-section { color: #64748b !important; font-size: 10px; font-weight: 700; letter-spacing: 1.6px; margin: 18px 0 8px; }

div[data-testid="stRadio"] > label { display: none; }
div[data-testid="stRadio"] div[role="radiogroup"] { gap: 4px; }
div[data-testid="stRadio"] div[role="radiogroup"] label {
    width: 100%; margin: 0; padding: 9px 12px; border-radius: 10px;
    transition: background .15s ease;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:hover { background: rgba(148, 163, 184, .08); }
div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child { display: none; }
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background: rgba(45, 212, 191, .12);
    box-shadow: inset 3px 0 0 #2dd4bf;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p,
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) * {
    color: #ffffff !important; font-weight: 600;
}

section[data-testid="stSidebar"] div[data-testid="stAlert"] {
    background: rgba(16, 185, 129, .10) !important;
    border: 1px solid rgba(16, 185, 129, .30) !important;
    border-radius: 12px !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(45, 212, 191, .10) !important;
    color: #5eead4 !important;
    border: 1px solid rgba(45, 212, 191, .35) !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(45, 212, 191, .20) !important;
    color: #ffffff !important;
}

/* ---------- Page header ---------- */
.page-heading { color: var(--ink); font-size: 30px; font-weight: 750; letter-spacing: -1px; line-height: 1.2; }
.page-subtitle { color: var(--muted); font-size: 14px; margin: 6px 0 24px; }

/* ---------- Section heading ---------- */
.section-heading {
    display: flex; align-items: center; gap: 12px;
    color: var(--muted); font-size: 12px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .08em;
    margin: 30px 0 14px;
}
.section-heading:after { content: ""; flex: 1; height: 1px; background: var(--line); }

/* ---------- Hero ---------- */
.hero-panel {
    position: relative; overflow: hidden; padding: 28px 32px; margin: 4px 0 24px;
    border-radius: 18px; border: 1px solid #1c2b4a; color: #f8fafc;
    background: radial-gradient(circle at 90% 0%, rgba(45, 212, 191, .18), transparent 45%),
                linear-gradient(120deg, #050914 0%, #0b1d45 60%, #123a7a 100%);
    box-shadow: 0 10px 30px rgba(0, 0, 0, .45);
}
.hero-eyebrow { color: #5eead4; font-size: 11px; font-weight: 700; letter-spacing: 1.8px; text-transform: uppercase; margin-bottom: 8px; }
.hero-title { color: #ffffff; font-size: 24px; font-weight: 750; letter-spacing: -.5px; margin: 0 0 6px; }
.hero-copy { color: #cbd5e1; font-size: 13px; max-width: 680px; line-height: 1.65; }
.hero-status {
    display: inline-flex; margin-top: 16px; padding: 6px 12px; border-radius: 30px;
    background: rgba(255, 255, 255, .06); border: 1px solid rgba(255, 255, 255, .14);
    color: #ccfbf1; font-size: 11px; font-weight: 600;
}

/* ---------- Metric cards ---------- */
.metric-card {
    background: var(--card); border: 1px solid var(--line); border-radius: 16px;
    padding: 18px 20px; min-height: 150px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, .35);
    transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 24px rgba(0, 0, 0, .5);
    border-color: #24406e;
}
.metric-icon {
    width: 40px; height: 40px; border-radius: 12px; font-size: 18px;
    background: rgba(45, 212, 191, .12); display: flex; align-items: center; justify-content: center;
}
.metric-label { color: var(--muted); font-size: 11px; font-weight: 700; letter-spacing: .06em; margin-top: 16px; }
.metric-value { color: #f8fafc; font-size: 28px; font-weight: 750; letter-spacing: -.8px; margin-top: 4px; line-height: 1.2; }
.metric-note { color: #64748b; font-size: 12px; margin-top: 4px; }

/* ---------- Status cards ---------- */
.status-card {
    background: var(--card); border: 1px solid var(--line); border-radius: 16px;
    padding: 22px; min-height: 150px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, .35);
}
.status-label { color: var(--muted); font-size: 11px; font-weight: 700; letter-spacing: .06em; }
.status-value { color: #f8fafc; font-size: 26px; font-weight: 750; margin-top: 8px; letter-spacing: -.5px; }
.status-pill { display: inline-block; border-radius: 30px; padding: 5px 12px; font-size: 11px; font-weight: 700; margin-top: 10px; }
.green-pill  { background: rgba(34, 197, 94, .15); color: #86efac; }
.orange-pill { background: rgba(245, 158, 11, .15); color: #fcd34d; }
.red-pill    { background: rgba(239, 68, 68, .15); color: #fca5a5; }
.blue-pill   { background: rgba(96, 165, 250, .15); color: #93c5fd; }

/* ---------- Info banner ---------- */
.info-banner {
    background: rgba(45, 212, 191, .08); border: 1px solid rgba(45, 212, 191, .25);
    border-radius: 12px; padding: 12px 16px; color: #99f6e4; font-size: 13px; margin: 8px 0 20px;
}

/* ---------- Native Streamlit components ---------- */
div[data-testid="stDataFrame"], div[data-testid="stPlotlyChart"] {
    background: var(--card) !important; border: 1px solid var(--line) !important;
    border-radius: 16px; box-shadow: 0 4px 18px rgba(0, 0, 0, .3); overflow: hidden;
}
div[data-testid="stPlotlyChart"] { padding: 8px 8px 0; }

div[data-testid="stMetric"] {
    background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 14px 18px;
}
div[data-testid="stMetric"] label { color: var(--muted) !important; font-weight: 600; }
div[data-testid="stMetricValue"] { color: #f8fafc; font-weight: 750; }

.stButton > button, .stDownloadButton > button {
    border-radius: 10px; min-height: 42px; font-weight: 600;
    border: 1px solid #24406e; color: var(--text); background: var(--card-2);
    transition: all .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: var(--primary); color: var(--primary);
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    background: #0f766e; border-color: #0f766e; color: #ffffff;
    box-shadow: 0 4px 14px rgba(45, 212, 191, .2);
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
    background: #115e59; border-color: #115e59; color: #ffffff;
}

div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
    border-radius: 10px !important; border-color: #24406e !important;
    background: #0a1328 !important; color: #e2e8f0 !important;
}
div[data-baseweb="input"]:focus-within > div, div[data-baseweb="select"]:focus-within > div {
    border-color: var(--primary) !important; box-shadow: 0 0 0 3px rgba(45, 212, 191, .15) !important;
}
div[data-testid="stSelectbox"] label, div[data-testid="stTextInput"] label,
div[data-testid="stDateInput"] label {
    color: var(--text); font-weight: 600; font-size: 13px;
}
div[data-testid="stCaptionContainer"] p { color: var(--muted) !important; }
div[data-testid="stAlert"] { border-radius: 12px; }

hr { border-color: var(--line); }

@media (max-width: 900px) {
    .block-container { padding: 1.2rem 1rem 2rem; }
    .page-heading { font-size: 24px; }
    .hero-title { font-size: 20px; }
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# DATABASE CONNECTION
# =====================================================
try:
    MONGO_URI = st.secrets["MONGO_URI"]
except Exception:
    MONGO_URI = os.getenv("MONGO_URI")

try:
    MONGO_DB = st.secrets["MONGO_DB"]
except Exception:
    MONGO_DB = os.getenv("MONGO_DB", "IoTSensorMonitor")

if not MONGO_URI:
    st.error("MongoDB URI missing. Configure MONGO_URI.")
    st.stop()


@st.cache_resource
def connect_database(uri, database):
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    return client[database]


try:
    db = connect_database(MONGO_URI, MONGO_DB)
except Exception as error:
    st.error(f"MongoDB connection failed: {error}")
    st.stop()


# =====================================================
# DATA FUNCTIONS
# =====================================================
def load_data(collection, limit=None, sort_field=None):
    cursor = db[collection].find({}, {"_id": 0})

    if sort_field:
        cursor = cursor.sort(sort_field, -1)

    if limit:
        cursor = cursor.limit(limit)

    return list(cursor)


def valid_value(reading, field):
    value = reading.get(field)

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None

    source = str(
        reading.get("data_source", reading.get("source", ""))
    ).lower()

    sensor_id = str(reading.get("sensor_id", "")).upper()

    if source == "demo":
        if field == "temperature_c" and sensor_id == "SENSOR-002" and value == 0:
            return None

        if field in ("pm25", "pm10", "aqi") and sensor_id == "SENSOR-001" and value == 0:
            return None

    if field == "aqi" and value < 0:
        return None

    return float(value)


def mean(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 2) if values else None


def number(value, suffix=""):
    return f"{value:,.2f}{suffix}" if value is not None else "N/A"


def aqi_info(aqi):
    if aqi is None:
        return "Unavailable", "Unknown"

    if aqi <= 50:
        return "Good", "Low"
    if aqi <= 100:
        return "Moderate", "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups", "Elevated"
    if aqi <= 200:
        return "Unhealthy", "High"
    if aqi <= 300:
        return "Very Unhealthy", "Very High"

    return "Hazardous", "Severe"


def metric_card(label, value, note, icon):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-top">
            <div class="metric-icon">{icon}</div>
        </div>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-note">{note}</div>
    </div>
    """, unsafe_allow_html=True)


def section(title):
    st.markdown(
        f'<div class="section-heading">{title}</div>',
        unsafe_allow_html=True
    )


def page_header(title, subtitle):
    st.markdown(
        f'<div class="page-heading">{title}</div>'
        f'<div class="page-subtitle">{subtitle}</div>',
        unsafe_allow_html=True
    )


def chart_style(fig, height=330):
    fig.update_layout(
        template="plotly_dark",
        colorway=PALETTE,
        height=height,
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(family="Inter", color="#cbd5e1", size=12),
        title_font=dict(size=15, color="#f1f5f9"),
        margin=dict(l=15, r=15, t=55, b=15),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(
            bgcolor="#0c1630",
            bordercolor="#24406e",
            font_size=12,
            font_family="Inter"
        )
    )

    fig.update_xaxes(showgrid=False, linecolor="#1c2b4a", zerolinecolor="#1c2b4a")
    fig.update_yaxes(gridcolor="#13223f", zeroline=False, linecolor="#1c2b4a")

    return fig


def gauge_steps():
    return [
        {"range": [0, 50], "color": "#14532d"},
        {"range": [50, 100], "color": "#713f12"},
        {"range": [100, 150], "color": "#7c2d12"},
        {"range": [150, 200], "color": "#7f1d1d"},
        {"range": [200, 300], "color": "#4c1d95"}
    ]


# =====================================================
# ADVANCED SENSOR FEATURES
# =====================================================
def as_datetime(value):
    return pd.to_datetime(value, errors="coerce", utc=True)


@st.cache_data(ttl=600, show_spinner=False)
def fetch_open_meteo(latitude, longitude):
    """Location-level API estimates; these are NOT physical IoT telemetry."""
    weather_url = "https://api.open-meteo.com/v1/forecast"
    air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {"latitude": latitude, "longitude": longitude,
              "current": "temperature_2m,relative_humidity_2m", "timezone": "auto"}
    air_params = {"latitude": latitude, "longitude": longitude,
                  "current": "pm2_5,pm10,us_aqi", "timezone": "auto"}
    w = requests.get(weather_url, params=params, timeout=12)
    a = requests.get(air_url, params=air_params, timeout=12)
    w.raise_for_status()
    a.raise_for_status()
    return {"weather": w.json().get("current", {}),
            "air": a.json().get("current", {}),
            "fetched_at": datetime.now().astimezone().isoformat()}


def latest_by_sensor(rows):
    result = {}
    for row in rows:
        sid = row.get("sensor_id")
        stamp = as_datetime(row.get("recorded_at"))
        if sid and not pd.isna(stamp):
            if sid not in result or stamp > result[sid][0]:
                result[sid] = (stamp, row)
    return result


def save_threshold_alerts(rows):
    """Create one open alert per sensor/type; reruns do not duplicate alerts."""
    created = 0
    latest = latest_by_sensor(rows)
    for sid, (_, row) in latest.items():
        value = valid_value(row, "aqi")
        if value is None or value < 100:
            continue
        severity = "High" if value >= 150 else "Warning"
        alert_type = "AQI_HIGH" if value >= 150 else "AQI_WARNING"
        exists = db.alerts.find_one({
            "sensor_id": sid, "alert_type": alert_type,
            "status": {"$in": ["open", "active", "pending"]}
        })
        if exists:
            continue
        db.alerts.insert_one({
            "sensor_id": sid, "reading_id": str(row.get("_id", "")) or None,
            "alert_type": alert_type, "severity": severity,
            "message": f"AQI reached {value:.1f}; threshold is {150 if value >= 150 else 100}.",
            "created_at": datetime.now().astimezone(),
            "status": "open"
        })
        created += 1
    return created


def build_pdf_report(readings_df, alerts_df, start_date, end_date):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    story = [
        Paragraph("SensorSense | Environmental Monitoring Report", styles["Title"]),
        Paragraph(f"Period: {start_date} to {end_date}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"Readings: {len(readings_df)} | Alerts: {len(alerts_df)}", styles["Heading2"])
    ]
    if not readings_df.empty:
        cols = [c for c in ["sensor_id", "temperature_c", "humidity_percent", "pm25", "pm10", "aqi", "recorded_at"] if c in readings_df]
        data = [cols] + readings_df[cols].head(35).astype(str).values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")])
        ]))
        story += [Spacer(1, 10), table]
    doc.build(story)
    return output.getvalue()


# =====================================================
# LOCATION SEARCH (Open-Meteo cities first, Nominatim countries/places)
# =====================================================
@st.cache_data(ttl=3600, show_spinner=False)
def search_world_location(place_name):
    headers = {"User-Agent": "SensorSense-IoT-Student-Project/1.0"}
    results = []

    # 1) Open-Meteo: cities/towns with clean English names (shown first)
    try:
        om = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": place_name, "count": 6, "language": "en", "format": "json"},
            timeout=15
        )
        om.raise_for_status()
        for item in om.json().get("results", []):
            parts = [p for p in [item.get("name"), item.get("admin1"), item.get("country")] if p]
            results.append({
                "label": "🏙️ " + ", ".join(parts) + " (City/Town)",
                "name": item.get("name", place_name),
                "latitude": float(item["latitude"]),
                "longitude": float(item["longitude"]),
                "kind": "City/Town"
            })
    except requests.RequestException:
        pass

    # 2) Nominatim (OpenStreetMap): countries and other places, English names
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": place_name,
                "format": "jsonv2",
                "addressdetails": 1,
                "limit": 8,
                "accept-language": "en"
            },
            headers=headers,
            timeout=15
        )
        response.raise_for_status()

        city_types = {"city", "town", "village", "municipality", "county", "state", "district"}
        for item in response.json():
            addr_type = item.get("addresstype", item.get("type", ""))
            if addr_type == "country":
                kind, icon = "Country", "🌍"
            elif addr_type in city_types:
                kind, icon = "City/Town", "🏙️"
            else:
                kind, icon = "Place", "📍"

            results.append({
                "label": f"{icon} {item.get('display_name', place_name)} ({kind})",
                "name": item.get("name") or place_name,
                "latitude": float(item["lat"]),
                "longitude": float(item["lon"]),
                "kind": kind
            })
    except requests.RequestException:
        pass

    # Remove duplicates: same name and nearly same coordinates
    unique = []
    seen = set()
    for item in results:
        key = (item["name"].lower(), round(item["latitude"], 2), round(item["longitude"], 2))
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


# =====================================================
# LOAD DATABASE DATA
# =====================================================
try:
    sensors = load_data("sensors", sort_field="sensor_id")
    readings = load_data("readings", limit=100, sort_field="recorded_at")
    all_readings = load_data("readings", sort_field="recorded_at")
    alerts = load_data("alerts", limit=100, sort_field="created_at")

    total_sensors = db.sensors.count_documents({})
    total_readings = db.readings.count_documents({})
    total_alerts = db.alerts.count_documents({})

    active_sensors = db.sensors.count_documents({
        "status": {"$regex": "^active$", "$options": "i"}
    })

    inactive_sensors = total_sensors - active_sensors
    newly_saved_alerts = save_threshold_alerts(all_readings)
    if newly_saved_alerts:
        total_alerts = db.alerts.count_documents({})

except Exception as error:
    st.error(f"Could not load database records: {error}")
    st.stop()


temperatures = [valid_value(r, "temperature_c") for r in all_readings]
humidities = [valid_value(r, "humidity_percent") for r in all_readings]
aqis = [valid_value(r, "aqi") for r in all_readings]

valid_aqis = [value for value in aqis if value is not None and value > 0]

latest_aqi = valid_aqis[0] if valid_aqis else None
aqi_category, aqi_risk = aqi_info(latest_aqi)


# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.markdown("""
    <div class="brand">🌤️ Sensor<span>Sense</span></div>
    <div class="brand-subtitle">IOT ENVIRONMENT MONITOR</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">WORKSPACE</div>', unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["Dashboard", "Sensors", "Readings", "Alerts", "Analytics", "Live & Map", "Reports", "Health"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown('<div class="sidebar-section">DATABASE STATUS</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:rgba(16,185,129,.10);border:1px solid rgba(16,185,129,.30);
                border-radius:12px;padding:14px;margin:8px 0 10px;">
      <div style="color:#6ee7b7;font-size:13px;font-weight:700;">● MongoDB Connected</div>
      <div style="color:#94a3b8;font-size:11px;margin-top:4px;">Database connection is active</div>
    </div>
    <div style="color:#94a3b8;font-size:12px;font-weight:600;">Database: {MONGO_DB}</div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if st.button("↻  Refresh Dashboard", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.caption("SensorSense · Version 1.0")
    st.caption("IoT Sensor Monitoring System")


# =====================================================
# DASHBOARD
# =====================================================
if page == "Dashboard":

    page_header(
        "Environmental Monitoring Dashboard",
        "A centralized view of IoT sensor activity, environmental conditions, and air quality."
    )

    st.markdown("""
    <div class="hero-panel">
        <div class="hero-eyebrow">IoT environmental intelligence</div>
        <div class="hero-title">Monitor the environment. Understand the data.</div>
        <div class="hero-copy">
            Track connected sensors, review environmental measurements and
            identify air-quality conditions from one centralized workspace.
        </div>
        <div class="hero-status">● SYSTEM ONLINE &nbsp; | &nbsp; MONGODB ATLAS CONNECTED</div>
    </div>
    """, unsafe_allow_html=True)

    section("System Overview")

    cols = st.columns(4)

    cards = [
        ("TOTAL SENSORS", f"{total_sensors:,}", "Registered devices", "📡"),
        ("ACTIVE SENSORS", f"{active_sensors:,}", "Operational devices", "🟢"),
        ("TOTAL READINGS", f"{total_readings:,}", "Stored measurements", "📊"),
        ("TOTAL ALERTS", f"{total_alerts:,}", "Recorded alerts", "🚨")
    ]

    for col, item in zip(cols, cards):
        with col:
            metric_card(*item)

    section("Environmental Overview")

    cols = st.columns(3)

    environmental_cards = [
        ("AVERAGE TEMPERATURE", number(mean(temperatures), " °C"), "Valid temperature records", "🌡️"),
        ("AVERAGE HUMIDITY", number(mean(humidities), " %"), "Valid humidity records", "💧"),
        ("AVERAGE AQI", number(mean(valid_aqis)), "Air quality index", "🌫️")
    ]

    for col, item in zip(cols, environmental_cards):
        with col:
            metric_card(*item)

    section("Current Air Quality")

    left, right = st.columns([1, 2])

    with left:
        if latest_aqi is not None:
            pill = (
                "green-pill" if latest_aqi <= 50
                else "orange-pill" if latest_aqi <= 100
                else "red-pill"
            )

            st.markdown(f"""
            <div class="status-card">
                <div class="status-label">LATEST AVAILABLE AQI</div>
                <div class="status-value">{latest_aqi:.1f}</div>
                <span class="status-pill {pill}">{aqi_category}</span>
            </div>
            """, unsafe_allow_html=True)

            gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=latest_aqi,
                number={"font": {"size": 27, "color": "#f1f5f9"}},
                title={"text": "Air Quality Index", "font": {"size": 12}},
                gauge={
                    "axis": {"range": [0, 300], "tickwidth": 1, "tickcolor": "#475569"},
                    "bar": {"color": PRIMARY, "thickness": 0.24},
                    "bgcolor": CARD_BG,
                    "borderwidth": 0,
                    "steps": gauge_steps()
                }
            ))
            st.plotly_chart(chart_style(gauge, 205), use_container_width=True)
        else:
            st.info("AQI data unavailable.")

    with right:
        st.markdown(f"""
        <div class="status-card">
            <div class="status-label">AIR QUALITY RISK ASSESSMENT</div>
            <div class="status-value">{aqi_risk} Risk</div>
            <p style="color:#94a3b8;font-size:13px;margin-top:10px;">
                Current category: {aqi_category}
            </p>
            <p style="color:#64748b;font-size:12px;">
                Based on the latest valid stored AQI measurement.
            </p>
        </div>
        """, unsafe_allow_html=True)

    section("Environmental Trends")

    chart_data = pd.DataFrame(readings)

    if not chart_data.empty and "recorded_at" in chart_data.columns:

        chart_data["recorded_at"] = pd.to_datetime(chart_data["recorded_at"], errors="coerce")
        chart_data["temperature_c"] = chart_data.apply(lambda r: valid_value(r, "temperature_c"), axis=1)
        chart_data["aqi"] = chart_data.apply(lambda r: valid_value(r, "aqi"), axis=1)

        chart_data = chart_data.dropna(subset=["recorded_at"])
        chart_data = chart_data.sort_values("recorded_at")

        c1, c2 = st.columns(2)

        with c1:
            temp_df = chart_data.dropna(subset=["temperature_c"])

            if not temp_df.empty:
                fig = px.area(
                    temp_df,
                    x="recorded_at",
                    y="temperature_c",
                    title="Temperature History",
                    labels={"recorded_at": "Time", "temperature_c": "Temperature °C"}
                )
                fig.update_traces(line_color=PRIMARY, fillcolor="rgba(45,212,191,0.15)")
                st.plotly_chart(chart_style(fig), use_container_width=True)
            else:
                st.info("No temperature data available.")

        with c2:
            aqi_df = chart_data.dropna(subset=["aqi"])

            if not aqi_df.empty:
                fig = px.line(
                    aqi_df,
                    x="recorded_at",
                    y="aqi",
                    title="Air Quality History",
                    labels={"recorded_at": "Time", "aqi": "AQI"}
                )
                fig.update_traces(line_color=ACCENT, line_width=3)
                st.plotly_chart(chart_style(fig), use_container_width=True)
            else:
                st.info("No AQI data available.")

    else:
        st.info("No historical readings available.")

    section("Latest Sensor Readings")

    if readings:
        latest_df = pd.DataFrame(readings)
        preferred_columns = [
            "sensor_id", "temperature_c", "humidity_percent",
            "pm25", "pm10", "aqi", "recorded_at", "data_source"
        ]
        display_columns = [c for c in preferred_columns if c in latest_df.columns]
        if display_columns:
            latest_df = latest_df[display_columns]
        st.dataframe(latest_df, use_container_width=True, hide_index=True, height=310)
        st.caption("Showing the 100 most recent stored readings. Use the Readings page to search and export records.")
    else:
        st.info("No readings found.")


# =====================================================
# SENSORS
# =====================================================
elif page == "Sensors":

    page_header("Sensor Management", "Manage and monitor registered IoT devices.")

    cols = st.columns(3)

    sensor_cards = [
        ("TOTAL SENSORS", total_sensors, "All registered devices", "📡"),
        ("ACTIVE SENSORS", active_sensors, "Operational devices", "🟢"),
        ("INACTIVE SENSORS", inactive_sensors, "Inactive devices", "⚪")
    ]

    for col, item in zip(cols, sensor_cards):
        with col:
            metric_card(*item)

    section("Registered Devices")

    if sensors:
        df = pd.DataFrame(sensors)

        if "status" in df.columns:
            selected = st.selectbox("Filter sensor status", ["All", "active", "inactive"])

            if selected != "All":
                df = df[df["status"].astype(str).str.lower() == selected]

        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{len(df)} sensor records displayed.")
    else:
        st.info("No sensors found.")


# =====================================================
# READINGS
# =====================================================
elif page == "Readings":

    page_header("Sensor Readings", "Explore environmental measurements and sensor records.")

    if readings:

        df = pd.DataFrame(readings)

        c1, c2 = st.columns(2)

        with c1:
            options = ["All"]

            if "sensor_id" in df.columns:
                options += sorted(df["sensor_id"].dropna().astype(str).unique().tolist())

            selected = st.selectbox("Select Sensor", options)

        with c2:
            search = st.text_input("Search Sensor", placeholder="Enter sensor ID...")

        if selected != "All" and "sensor_id" in df.columns:
            df = df[df["sensor_id"].astype(str) == selected]

        if search and "sensor_id" in df.columns:
            df = df[df["sensor_id"].astype(str).str.contains(search, case=False, na=False)]

        c1, c2 = st.columns(2)

        with c1:
            metric_card("DISPLAYED READINGS", f"{len(df):,}", "Matching records", "📋")

        with c2:
            metric_card("TOTAL DATABASE READINGS", f"{total_readings:,}", "All stored records", "🗄️")

        section("Measurement Records")

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇ Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="sensorsense_readings.csv",
            mime="text/csv"
        )

    else:
        st.info("No readings found.")


# =====================================================
# ALERTS
# =====================================================
elif page == "Alerts":

    page_header("System Alerts", "Monitor environmental warnings and sensor notifications.")

    open_alerts = sum(
        1 for a in alerts
        if str(a.get("status", "")).lower() in ("open", "active", "pending")
    )

    c1, c2 = st.columns(2)

    with c1:
        metric_card("TOTAL ALERTS", f"{total_alerts:,}", "Stored in database", "🚨")

    with c2:
        metric_card("OPEN / PENDING", f"{open_alerts:,}", "Among latest 100 alerts", "⚠️")

    section("Alert Records")

    if alerts:
        df = pd.DataFrame(alerts)

        if "severity" in df.columns:
            options = ["All"] + sorted(df["severity"].dropna().astype(str).unique().tolist())
            selected = st.selectbox("Filter by Severity", options)

            if selected != "All":
                df = df[df["severity"].astype(str) == selected]

        st.dataframe(df, use_container_width=True, hide_index=True)

    else:
        st.success("No alerts found.")


# =====================================================
# ANALYTICS
# =====================================================
elif page == "Analytics":

    page_header("Sensor Analytics", "Analyze environmental trends and database statistics.")

    st.markdown(
        f'<div class="info-banner">ANALYTICS SUMMARY &nbsp; · &nbsp; '
        f'{len(all_readings):,} records analyzed</div>',
        unsafe_allow_html=True
    )

    cols = st.columns(3)

    analytics_cards = [
        ("AVERAGE TEMPERATURE", number(mean(temperatures), " °C"), "Valid measurements", "🌡️"),
        ("AVERAGE HUMIDITY", number(mean(humidities), " %"), "Valid measurements", "💧"),
        ("AVERAGE AQI", number(mean(valid_aqis)), "Valid measurements", "🌫️")
    ]

    for col, item in zip(cols, analytics_cards):
        with col:
            metric_card(*item)

    section("Air Quality Assessment")

    c1, c2 = st.columns(2)

    with c1:
        if latest_aqi is not None:
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=latest_aqi,
                    title={"text": "Latest AQI"},
                    gauge={
                        "axis": {"range": [0, 300], "tickcolor": "#475569"},
                        "bar": {"color": PRIMARY},
                        "bgcolor": CARD_BG,
                        "steps": gauge_steps()
                    }
                )
            )
            st.plotly_chart(chart_style(fig, 290), use_container_width=True)
        else:
            st.info("AQI unavailable.")

    with c2:
        st.markdown(f"""
        <div class="status-card">
            <div class="status-label">AIR QUALITY CATEGORY</div>
            <div class="status-value">{aqi_category}</div>
            <br>
            <div class="status-label">RISK LEVEL</div>
            <div class="status-value">{aqi_risk}</div>
            <p style="color:#94a3b8;font-size:13px;">
                Latest AQI: {latest_aqi if latest_aqi is not None else "N/A"}
            </p>
        </div>
        """, unsafe_allow_html=True)

    section("Readings by Sensor")

    if all_readings:
        df = pd.DataFrame(all_readings)

        if "sensor_id" in df.columns:
            summary = (
                df.groupby("sensor_id")
                .size()
                .reset_index(name="Reading Count")
                .sort_values("Reading Count", ascending=False)
            )

            c1, c2 = st.columns([1, 1])

            with c1:
                st.dataframe(summary, use_container_width=True, hide_index=True)

            with c2:
                fig = px.bar(
                    summary,
                    x="sensor_id",
                    y="Reading Count",
                    title="Sensor Contribution",
                    color="Reading Count",
                    color_continuous_scale=["#134e4a", PRIMARY]
                )
                st.plotly_chart(chart_style(fig, 300), use_container_width=True)

    else:
        st.info("No analytics data available.")

    section("Daily / Weekly / Monthly Trends")

    trend_df = pd.DataFrame(all_readings)
    if not trend_df.empty and "recorded_at" in trend_df:
        trend_df["recorded_at"] = pd.to_datetime(trend_df["recorded_at"], errors="coerce")
        trend_df["aqi"] = trend_df.apply(lambda r: valid_value(r, "aqi"), axis=1)
        trend_df["temperature_c"] = trend_df.apply(lambda r: valid_value(r, "temperature_c"), axis=1)
        trend_df = trend_df.dropna(subset=["recorded_at"])

        granularity = st.selectbox("Trend interval", ["Daily", "Weekly", "Monthly"], key="analytics_interval")
        rule = {"Daily": "D", "Weekly": "W", "Monthly": "MS"}[granularity]

        trend_df = trend_df.set_index("recorded_at").sort_index()
        trend = trend_df.resample(rule).agg({"aqi": "mean", "temperature_c": "mean"}).dropna(how="all").reset_index()

        if not trend.empty:
            trend_long = trend.melt(
                id_vars="recorded_at", value_vars=["aqi", "temperature_c"],
                var_name="Metric", value_name="Average"
            )
            fig = px.line(
                trend_long, x="recorded_at", y="Average", color="Metric",
                markers=True, title=f"{granularity} Environmental Trends"
            )
            st.plotly_chart(chart_style(fig), use_container_width=True)

            daily = trend_df.resample("D")["aqi"].max().dropna()
            if not daily.empty:
                st.metric("Highest AQI day", f"{daily.max():.1f}", daily.idxmax().strftime("%d %b %Y"))

            st.caption("Trend values are calculated from historical MongoDB readings.")

    section("AQI Estimate (Experimental)")

    forecast_rows = pd.DataFrame(all_readings)
    if not forecast_rows.empty and {"recorded_at", "aqi"}.issubset(forecast_rows.columns):
        forecast_rows["recorded_at"] = pd.to_datetime(forecast_rows["recorded_at"], errors="coerce")
        forecast_rows["aqi"] = forecast_rows.apply(lambda r: valid_value(r, "aqi"), axis=1)
        forecast_rows = (
            forecast_rows.dropna(subset=["recorded_at", "aqi"])
            .sort_values("recorded_at")
            .tail(48)
        )
        if len(forecast_rows) >= 3:
            forecast_rows["step"] = range(len(forecast_rows))
            slope, intercept = np.polyfit(forecast_rows["step"], forecast_rows["aqi"], 1)
            estimate = max(0, float(slope * (len(forecast_rows) + 3) + intercept))
            st.metric("Next-step AQI estimate", f"{estimate:.1f}")
            st.caption("Experimental linear-trend estimate only; not a certified forecast or health advisory.")
        else:
            st.info("At least three valid AQI readings are needed for an estimate.")

    st.markdown("""
    <div class="info-banner">
        Note: Analytics are calculated from stored database records.
        Historical or demo records may not represent live sensor measurements.
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# LIVE API + INTERACTIVE SENSOR MAP
# =====================================================
elif page == "Live & Map":

    page_header(
        "Live Environment & Sensor Map",
        "Open-Meteo location estimates and registered sensor locations."
    )

    st.info("Live values are Open-Meteo location-level estimates, not direct measurements from physical IoT devices. Your MongoDB sensor records remain unchanged.")

    if "anywhere_location" not in st.session_state:
        st.session_state["anywhere_location"] = {
            "name": "World view", "latitude": 20.0, "longitude": 0.0
        }

    section("Explore Any Location")

    def live_search(query):
        """Runs as the user types. Returns a list of labels for the dropdown."""
        st.session_state.pop("search_error", None)
        if not query or len(query.strip()) < 2:
            return []
        try:
            matches = search_world_location(query.strip())
        except Exception as e:
            st.session_state["search_error"] = str(e)
            return []
        st.session_state["anywhere_matches_by_label"] = {m["label"]: m for m in matches}
        return [m["label"] for m in matches]

    selected_label = st_searchbox(
        live_search,
        key="anywhere_searchbox",
        placeholder="Type a country, city or town (e.g. Pakistan, Karachi, Tokyo)...",
        clear_on_submit=False,
        debounce=300,
    )

    if st.session_state.get("search_error"):
        st.warning(f"Search mein error: {st.session_state['search_error']}")

    if selected_label:
        chosen = st.session_state.get("anywhere_matches_by_label", {}).get(selected_label)
        if chosen:
            new_location = {
                "name": chosen["name"],
                "latitude": chosen["latitude"],
                "longitude": chosen["longitude"],
            }
            if st.session_state.get("anywhere_location") != new_location:
                st.session_state["anywhere_location"] = new_location
                st.rerun()

    current_place = st.session_state["anywhere_location"]
    st.caption("Ya map par kisi point par click karein, wahan ki live values update ho jayengi.")

    try:
        import folium
        from streamlit_folium import st_folium

        map_obj = folium.Map(
            location=[current_place["latitude"], current_place["longitude"]],
            zoom_start=3 if current_place["name"] == "World view" else 9,
            tiles="OpenStreetMap",
            control_scale=True
        )

        map_obj.get_root().header.add_child(folium.Element("""
        <style>
        .leaflet-tile-pane {
            filter: invert(1) hue-rotate(180deg) brightness(0.9) contrast(0.95);
        }
        .leaflet-container { background: #050914 !important; }
        </style>
        """))

        if current_place["name"] != "World view":
            folium.Marker(
                [current_place["latitude"], current_place["longitude"]],
                tooltip=current_place["name"],
                popup=current_place["name"],
                icon=folium.Icon(color="cadetblue", icon="cloud")
            ).add_to(map_obj)

        map_event = st_folium(
            map_obj, height=480, width=None,
            returned_objects=["last_clicked"],
            key=f"sensorsense_anywhere_world_map_{current_place['latitude']:.2f}_{current_place['longitude']:.2f}"
        )
        clicked = map_event.get("last_clicked") if map_event else None
        if clicked and clicked.get("lat") is not None and clicked.get("lng") is not None:
            new_lat, new_lon = float(clicked["lat"]), float(clicked["lng"])
            old = st.session_state["anywhere_location"]
            if abs(new_lat - old["latitude"]) > 0.0001 or abs(new_lon - old["longitude"]) > 0.0001:
                st.session_state["anywhere_location"] = {
                    "name": f"Selected map point ({new_lat:.4f}, {new_lon:.4f})",
                    "latitude": new_lat,
                    "longitude": new_lon
                }
                st.rerun()
    except ImportError:
        st.warning("Interactive map needs streamlit-folium and folium. Install them using requirements.txt.")

    current_place = st.session_state["anywhere_location"]
    st.markdown(f"**Selected location:** {current_place['name']}  ")
    st.caption(f"Coordinates: {current_place['latitude']:.5f}, {current_place['longitude']:.5f}")

    if st.button("↻ Refresh Live Weather & AQI", key="fetch_anywhere_live"):
        fetch_open_meteo.clear()

    live = None
    try:
        with st.spinner("Loading live conditions for the selected location..."):
            live = fetch_open_meteo(current_place["latitude"], current_place["longitude"])
        st.session_state["anywhere_live_result"] = live
        st.session_state["anywhere_live_for"] = current_place["name"]
    except Exception as e:
        st.warning(f"Live API unavailable right now: {e}")

    if live:
        weather, air = live["weather"], live["air"]
        live_aqi = air.get("us_aqi")
        live_category, live_risk = aqi_info(float(live_aqi)) if live_aqi is not None else ("Unavailable", "Unknown")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Temperature", f"{weather.get('temperature_2m', 'N/A')} °C")
        c2.metric("Humidity", f"{weather.get('relative_humidity_2m', 'N/A')} %")
        c3.metric("PM2.5", f"{air.get('pm2_5', 'N/A')} µg/m³")
        c4.metric("PM10", f"{air.get('pm10', 'N/A')} µg/m³")
        c5.metric("US AQI", f"{live_aqi if live_aqi is not None else 'N/A'}")

        st.markdown(f"**Air quality:** {live_category} · **Risk level:** {live_risk}")
        st.caption(f"Open-Meteo • fetched {live['fetched_at']} • approximate location-level data; not a physical sensor reading")

    loc_rows = load_data("locations")
    coords = []
    for loc in loc_rows:
        raw = loc.get("coordinates", {})
        if isinstance(raw, dict):
            lat = raw.get("lat", raw.get("latitude"))
            lon = raw.get("lon", raw.get("lng", raw.get("longitude")))
            if lat is None and raw.get("coordinates"):
                pair = raw.get("coordinates")
                if isinstance(pair, list) and len(pair) >= 2:
                    lon, lat = pair[0], pair[1]
        elif isinstance(raw, list) and len(raw) >= 2:
            lon, lat = raw[0], raw[1]
        else:
            lat = lon = None
        try:
            if lat is not None and lon is not None:
                coords.append((loc, float(lat), float(lon)))
        except (TypeError, ValueError):
            pass

    section("Registered Sensor Locations")

    latest_map = latest_by_sensor(all_readings)
    map_rows = []
    for loc, lat, lon in coords:
        loc_id = loc.get("_id") or loc.get("location_id")
        for sensor in sensors:
            if str(sensor.get("location_id")) != str(loc_id):
                continue
            sid = sensor.get("sensor_id")
            row = latest_map.get(sid, (None, {}))[1]
            map_rows.append({
                "latitude": lat, "longitude": lon,
                "Sensor": sid, "Name": sensor.get("sensor_name", ""),
                "Status": sensor.get("status", "unknown"),
                "Temperature °C": valid_value(row, "temperature_c"),
                "AQI": valid_value(row, "aqi")
            })

    if map_rows:
        map_df = pd.DataFrame(map_rows)
        try:
            import pydeck as pdk
            layer = pdk.Layer(
                "ScatterplotLayer", data=map_df,
                get_position="[longitude, latitude]",
                get_radius=180, get_fill_color=[45, 212, 191, 200],
                pickable=True, auto_highlight=True
            )
            view = pdk.ViewState(
                latitude=float(map_df.latitude.mean()),
                longitude=float(map_df.longitude.mean()),
                zoom=10, pitch=0
            )
            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view,
                map_style=None,
                tooltip={"text": "{Name}\nID: {Sensor}\nStatus: {Status}\nTemp: {Temperature °C} °C\nAQI: {AQI}"}
            )
            st.pydeck_chart(deck, use_container_width=True)
        except Exception:
            st.map(map_df[["latitude", "longitude"]])
        st.dataframe(map_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No sensors could be matched with saved location coordinates. Check sensors.location_id against locations IDs.")


# =====================================================
# REPORTS
# =====================================================
elif page == "Reports":

    page_header("Reports & Export Center", "Generate date-range CSV and PDF reports from stored records.")

    today = datetime.now().date()
    start_date = st.date_input("Start date", today - timedelta(days=30), key="report_start")
    end_date = st.date_input("End date", today, key="report_end")

    if start_date > end_date:
        st.error("Start date must be before or equal to end date.")
    else:
        report_df = pd.DataFrame(all_readings)
        alert_df = pd.DataFrame(load_data("alerts", sort_field="created_at"))

        if not report_df.empty and "recorded_at" in report_df:
            report_df["recorded_at"] = pd.to_datetime(report_df["recorded_at"], errors="coerce")
            report_df = report_df[
                (report_df.recorded_at.dt.date >= start_date) &
                (report_df.recorded_at.dt.date <= end_date)
            ]

        if not alert_df.empty and "created_at" in alert_df:
            alert_df["created_at"] = pd.to_datetime(alert_df["created_at"], errors="coerce")
            alert_df = alert_df[
                (alert_df.created_at.dt.date >= start_date) &
                (alert_df.created_at.dt.date <= end_date)
            ]

        c1, c2, c3 = st.columns(3)
        c1.metric("Readings in period", len(report_df))
        c2.metric("Alerts in period", len(alert_df))
        c3.metric("Average AQI", number(pd.to_numeric(report_df.get("aqi", pd.Series(dtype=float)), errors="coerce").mean()))

        st.dataframe(report_df, use_container_width=True, hide_index=True)

        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button(
                "Download readings CSV",
                report_df.to_csv(index=False).encode("utf-8"),
                f"sensorsense_report_{start_date}_{end_date}.csv",
                "text/csv",
                use_container_width=True
            )
        with d2:
            st.download_button(
                "Download alerts CSV",
                alert_df.to_csv(index=False).encode("utf-8"),
                f"sensorsense_alerts_{start_date}_{end_date}.csv",
                "text/csv",
                use_container_width=True
            )
        with d3:
            try:
                pdf = build_pdf_report(report_df, alert_df, start_date, end_date)
                st.download_button(
                    "Download PDF Report",
                    pdf,
                    f"sensorsense_report_{start_date}_{end_date}.pdf",
                    "application/pdf",
                    type="primary",
                    use_container_width=True
                )
            except ImportError:
                st.warning("PDF export needs reportlab. Install it with: pip install reportlab")


# =====================================================
# SENSOR HEALTH + MAINTENANCE
# =====================================================
elif page == "Health":

    page_header("Sensor Health & Maintenance", "Last communication, stale devices, missing readings and maintenance history.")

    latest_health = latest_by_sensor(all_readings)
    health_rows = []
    now_utc = pd.Timestamp.now(tz="UTC")

    for sensor in sensors:
        sid = sensor.get("sensor_id")
        latest = latest_health.get(sid)

        if latest:
            stamp, reading = latest
            age_hours = (now_utc - stamp).total_seconds() / 3600
            comm = stamp.strftime("%Y-%m-%d %H:%M UTC")
            health = "Stale (>24h)" if age_hours > 24 else "Reporting"
        else:
            age_hours, comm, health = None, "No readings", "Missing readings"

        health_rows.append({
            "Sensor ID": sid,
            "Sensor Name": sensor.get("sensor_name"),
            "Configured Status": sensor.get("status"),
            "Health": health,
            "Last Communication": comm,
            "Hours Since Reading": round(age_hours, 1) if age_hours is not None else "N/A"
        })

    health_df = pd.DataFrame(health_rows)

    if not health_df.empty:
        st.dataframe(health_df, use_container_width=True, hide_index=True)
        st.caption("Health rule: a sensor is marked stale when its latest stored reading is older than 24 hours.")
        st.metric("Sensors missing readings", int((health_df["Health"] == "Missing readings").sum()))

    section("Maintenance History")

    maintenance = load_data("maintenance_logs", sort_field="maintenance_date")
    if maintenance:
        st.dataframe(pd.DataFrame(maintenance), use_container_width=True, hide_index=True)
    else:
        st.info("No maintenance logs are currently stored in maintenance_logs.")