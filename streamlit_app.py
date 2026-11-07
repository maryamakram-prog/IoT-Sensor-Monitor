import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv

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
# PREMIUM UI DESIGN
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #f5f7fb;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding: 2rem 2.5rem 3rem;
    max-width: 1550px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #101b31 0%, #172b49 100%);
    border-right: 1px solid #263d5e;
}

section[data-testid="stSidebar"] * {
    color: #eaf0fa;
}

.brand {
    font-size: 27px;
    font-weight: 800;
    letter-spacing: -1.2px;
    color: white;
}

.brand span {
    color: #39c8b4;
}

.brand-subtitle {
    color: #91a5c4;
    font-size: 11px;
    letter-spacing: 1.7px;
    margin-top: 4px;
    margin-bottom: 30px;
}

.sidebar-section {
    color: #8095b5;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.5px;
    margin: 20px 0 10px;
}

/* DATABASE STATUS - PREMIUM DESIGN */
.db-status-box {
    background: linear-gradient(135deg, #123b43, #174b50);
    border: 1px solid #26766f;
    border-radius: 12px;
    padding: 14px;
    margin-top: 10px;
    margin-bottom: 15px;
}

.db-status-title {
    color: #9bb5c9 !important;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.5px;
    margin-bottom: 13px;
}

.db-connected {
    color: #52e0ae !important;
    font-size: 13px;
    font-weight: 700;
}

.db-dot {
    color: #52e0ae !important;
    font-size: 15px;
}

.db-name {
    color: #c0d7e8 !important;
    font-size: 11px;
    margin-top: 8px;
}

.page-heading {
    color: #172943;
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -1.4px;
    margin-bottom: 3px;
}

.page-subtitle {
    color: #8290a4;
    font-size: 13px;
    margin-bottom: 25px;
}

.section-heading {
    color: #203650;
    font-size: 17px;
    font-weight: 750;
    margin: 25px 0 13px;
}

.metric-card {
    position: relative;
    overflow: hidden;
    background: linear-gradient(145deg, #ffffff, #f9fbff);
    border: 1px solid #e7edf5;
    border-radius: 17px;
    padding: 19px 20px;
    min-height: 155px;
    box-shadow: 0 5px 18px rgba(25, 45, 75, 0.045);
    transition: all .25s ease;
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 26px rgba(25, 45, 75, 0.09);
    border-color: #b5ded8;
}

.metric-card:before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(180deg, #20b6a5, #4b8de0);
}

.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.metric-icon {
    width: 39px;
    height: 39px;
    border-radius: 12px;
    background: #eaf7f5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 19px;
}

.metric-label {
    color: #8190a5;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
    margin-top: 14px;
}

.metric-value {
    color: #172b47;
    font-size: 29px;
    font-weight: 800;
    letter-spacing: -1.2px;
    margin-top: 3px;
}

.metric-note {
    color: #9aa6b7;
    font-size: 10px;
    margin-top: 3px;
}

.status-card {
    background: linear-gradient(135deg, #ffffff, #f0f7ff);
    border: 1px solid #e1eaf5;
    border-radius: 17px;
    padding: 23px;
    min-height: 155px;
    box-shadow: 0 5px 18px rgba(25, 45, 75, .04);
}

.status-label {
    color: #8190a5;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
}

.status-value {
    color: #172b47;
    font-size: 25px;
    font-weight: 800;
    margin-top: 10px;
}

.status-pill {
    display: inline-block;
    border-radius: 30px;
    padding: 6px 12px;
    font-size: 10px;
    font-weight: 800;
    margin-top: 9px;
}

.green-pill {
    background: #e1f7eb;
    color: #087a4e;
}

.orange-pill {
    background: #fff1d9;
    color: #a65b00;
}

.red-pill {
    background: #ffe5e9;
    color: #b42335;
}

.blue-pill {
    background: #e7f0ff;
    color: #2459a6;
}

.info-banner {
    background: linear-gradient(90deg, #e9f5ff, #eef9f7);
    border: 1px solid #dcecf5;
    border-radius: 12px;
    padding: 13px 16px;
    color: #456782;
    font-size: 12px;
    margin: 15px 0 20px;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #e6ebf2;
    border-radius: 13px;
    overflow: hidden;
    background: white;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label {
    color: #465a73;
    font-weight: 650;
}

.stButton button,
.stDownloadButton button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 650;
}

.stButton button:hover,
.stDownloadButton button:hover {
    border-color: #20a99a;
    color: #168f85;
}

div[data-testid="stRadio"] label {
    font-size: 13px;
    font-weight: 600;
}

hr {
    border-color: #e6ebf2;
}

footer {
    visibility: hidden;
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
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter", color="#52647c", size=11),
        title_font=dict(size=15, color="#172943"),
        margin=dict(l=15, r=15, t=55, b=15),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Inter"
        )
    )

    fig.update_xaxes(showgrid=False, linecolor="#e8edf4")
    fig.update_yaxes(gridcolor="#edf1f6", zeroline=False)

    return fig


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

except Exception as error:
    st.error(f"Could not load database records: {error}")
    st.stop()


temperatures = [valid_value(r, "temperature_c") for r in all_readings]
humidities = [valid_value(r, "humidity_percent") for r in all_readings]
aqis = [valid_value(r, "aqi") for r in all_readings]

valid_aqis = [
    value for value in aqis
    if value is not None and value > 0
]

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

    st.markdown(
        '<div class="sidebar-section">WORKSPACE</div>',
        unsafe_allow_html=True
    )

    page = st.radio(
        "Navigation",
        ["Dashboard", "Sensors", "Readings", "Alerts", "Analytics"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # CUSTOM DATABASE STATUS
    st.markdown(f"""
    <div class="db-status-box">
        <div class="db-status-title">DATABASE STATUS</div>
        <div class="db-connected">
            <span class="db-dot">●</span>
            MongoDB Connected
        </div>
        <div class="db-name">
            Database: {MONGO_DB}
        </div>
    </div>
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
        "Dashboard Overview",
        "Welcome to your environmental monitoring workspace."
    )

    st.markdown("""
    <div class="info-banner">
        ● SYSTEM ONLINE &nbsp; · &nbsp;
        MongoDB Atlas Connected &nbsp; · &nbsp;
        Weather & Air Quality Monitoring
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
        ("AVERAGE TEMPERATURE", number(mean(temperatures), " °C"),
         "Valid temperature records", "🌡️"),
        ("AVERAGE HUMIDITY", number(mean(humidities), " %"),
         "Valid humidity records", "💧"),
        ("AVERAGE AQI", number(mean(valid_aqis)),
         "Air quality index", "🌫️")
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
        else:
            st.info("AQI data unavailable.")

    with right:
        st.markdown(f"""
        <div class="status-card">
            <div class="status-label">AIR QUALITY RISK ASSESSMENT</div>
            <div class="status-value">{aqi_risk} Risk</div>
            <p style="color:#8190a5;font-size:12px;">
                Current category: {aqi_category}
            </p>
            <p style="color:#8190a5;font-size:11px;">
                Based on the latest valid stored AQI measurement.
            </p>
        </div>
        """, unsafe_allow_html=True)

    section("Environmental Trends")

    chart_data = pd.DataFrame(readings)

    if not chart_data.empty and "recorded_at" in chart_data.columns:

        chart_data["recorded_at"] = pd.to_datetime(
            chart_data["recorded_at"], errors="coerce"
        )

        chart_data["temperature_c"] = chart_data.apply(
            lambda r: valid_value(r, "temperature_c"), axis=1
        )

        chart_data["aqi"] = chart_data.apply(
            lambda r: valid_value(r, "aqi"), axis=1
        )

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
                    labels={
                        "recorded_at": "Time",
                        "temperature_c": "Temperature °C"
                    }
                )

                fig.update_traces(
                    line_color="#18a999",
                    fillcolor="rgba(24,169,153,0.12)"
                )

                st.plotly_chart(
                    chart_style(fig),
                    use_container_width=True
                )
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
                    labels={
                        "recorded_at": "Time",
                        "aqi": "AQI"
                    }
                )

                fig.update_traces(
                    line_color="#477fe0",
                    line_width=3
                )

                st.plotly_chart(
                    chart_style(fig),
                    use_container_width=True
                )
            else:
                st.info("No AQI data available.")

    else:
        st.info("No historical readings available.")

    section("Latest Sensor Readings")

    if readings:
        st.dataframe(
            pd.DataFrame(readings),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No readings found.")


# =====================================================
# SENSORS
# =====================================================
elif page == "Sensors":

    page_header(
        "Sensor Management",
        "Manage and monitor registered IoT devices."
    )

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
            selected = st.selectbox(
                "Filter sensor status",
                ["All", "active", "inactive"]
            )

            if selected != "All":
                df = df[
                    df["status"].astype(str).str.lower() == selected
                ]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(f"{len(df)} sensor records displayed.")
    else:
        st.info("No sensors found.")


# =====================================================
# READINGS
# =====================================================
elif page == "Readings":

    page_header(
        "Sensor Readings",
        "Explore environmental measurements and sensor records."
    )

    if readings:

        df = pd.DataFrame(readings)

        c1, c2 = st.columns(2)

        with c1:
            options = ["All"]

            if "sensor_id" in df.columns:
                options += sorted(
                    df["sensor_id"].dropna().astype(str).unique().tolist()
                )

            selected = st.selectbox("Select Sensor", options)

        with c2:
            search = st.text_input(
                "Search Sensor",
                placeholder="Enter sensor ID..."
            )

        if selected != "All" and "sensor_id" in df.columns:
            df = df[df["sensor_id"].astype(str) == selected]

        if search and "sensor_id" in df.columns:
            df = df[
                df["sensor_id"].astype(str).str.contains(
                    search, case=False, na=False
                )
            ]

        c1, c2 = st.columns(2)

        with c1:
            metric_card(
                "DISPLAYED READINGS",
                f"{len(df):,}",
                "Matching records",
                "📋"
            )

        with c2:
            metric_card(
                "TOTAL DATABASE READINGS",
                f"{total_readings:,}",
                "All stored records",
                "🗄️"
            )

        section("Measurement Records")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

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

    page_header(
        "System Alerts",
        "Monitor environmental warnings and sensor notifications."
    )

    open_alerts = sum(
        1 for a in alerts
        if str(a.get("status", "")).lower()
        in ("open", "active", "pending")
    )

    c1, c2 = st.columns(2)

    with c1:
        metric_card(
            "TOTAL ALERTS",
            f"{total_alerts:,}",
            "Stored in database",
            "🚨"
        )

    with c2:
        metric_card(
            "OPEN / PENDING",
            f"{open_alerts:,}",
            "Among latest 100 alerts",
            "⚠️"
        )

    section("Alert Records")

    if alerts:
        df = pd.DataFrame(alerts)

        if "severity" in df.columns:
            options = ["All"] + sorted(
                df["severity"].dropna().astype(str).unique().tolist()
            )

            selected = st.selectbox("Filter by Severity", options)

            if selected != "All":
                df = df[df["severity"].astype(str) == selected]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.success("No alerts found.")


# =====================================================
# ANALYTICS
# =====================================================
elif page == "Analytics":

    page_header(
        "Sensor Analytics",
        "Analyze environmental trends and database statistics."
    )

    st.markdown(
        f'<div class="info-banner">ANALYTICS SUMMARY &nbsp; · &nbsp; '
        f'{len(all_readings):,} records analyzed</div>',
        unsafe_allow_html=True
    )

    cols = st.columns(3)

    analytics_cards = [
        ("AVERAGE TEMPERATURE", number(mean(temperatures), " °C"),
         "Valid measurements", "🌡️"),
        ("AVERAGE HUMIDITY", number(mean(humidities), " %"),
         "Valid measurements", "💧"),
        ("AVERAGE AQI", number(mean(valid_aqis)),
         "Valid measurements", "🌫️")
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
                        "axis": {"range": [0, 300]},
                        "bar": {"color": "#20a99a"},
                        "steps": [
                            {"range": [0, 50], "color": "#d9f3e6"},
                            {"range": [50, 100], "color": "#fff0c9"},
                            {"range": [100, 150], "color": "#ffdfbd"},
                            {"range": [150, 200], "color": "#ffd7dc"},
                            {"range": [200, 300], "color": "#e8dafa"}
                        ]
                    }
                )
            )

            st.plotly_chart(
                chart_style(fig, 290),
                use_container_width=True
            )
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
            <p style="color:#8290a4;font-size:12px;">
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
                st.dataframe(
                    summary,
                    use_container_width=True,
                    hide_index=True
                )

            with c2:
                fig = px.bar(
                    summary,
                    x="sensor_id",
                    y="Reading Count",
                    title="Sensor Contribution",
                    color="Reading Count",
                    color_continuous_scale=["#b9e9e2", "#168f85"]
                )

                st.plotly_chart(
                    chart_style(fig, 300),
                    use_container_width=True
                )

    else:
        st.info("No analytics data available.")

    st.markdown("""
    <div class="info-banner">
        Note: Analytics are calculated from stored database records.
        Historical or demo records may not represent live sensor measurements.
    </div>
    """, unsafe_allow_html=True)
