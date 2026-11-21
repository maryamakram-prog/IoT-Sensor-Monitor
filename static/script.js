const API = {
    health: "/api/health",
    counts: "/api/counts",
    sensors: "/api/sensors",
    readings: "/api/readings",
    alerts: "/api/alerts",
    analytics: "/api/analytics"
};

let allSensors = [];
let allReadings = [];
let allAlerts = [];

const $ = id => document.getElementById(id);

function safe(value) {
    return String(value ?? "—").replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;",
        '"': "&quot;", "'": "&#39;"
    })[c]);
}

function value(obj, ...keys) {
    for (const key of keys) {
        if (obj && obj[key] !== undefined && obj[key] !== null) {
            return obj[key];
        }
    }
    return null;
}

function formatNumber(v, digits = 1) {
    if (v === null || v === undefined || v === "" || isNaN(Number(v))) return "—";
    return Number(v).toLocaleString(undefined, {
        maximumFractionDigits: digits,
        minimumFractionDigits: 0
    });
}

function formatDate(v) {
    if (!v) return "—";
    const d = new Date(v);
    return isNaN(d.getTime()) ? safe(v) : d.toLocaleString();
}

async function getData(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
        throw new Error(`Could not load ${url}`);
    }
    return await response.json();
}

function getArray(data, key) {
    if (Array.isArray(data)) return data;
    if (key && Array.isArray(data[key])) return data[key];
    if (data && Array.isArray(data.data)) return data.data;
    if (data && Array.isArray(data.results)) return data.results;
    return [];
}

function setText(id, text) {
    const el = $(id);
    if (el) el.textContent = text;
}

/* ========================================================= */
/* CONNECTION STATUS CHECK                                   */
/* ========================================================= */

async function checkConnection() {
    try {
        const data = await getData(API.health);
        const connected = data.status === "connected";
        const el = $("connectionStatus");

        if (el) {
            el.classList.toggle("online", connected);
            el.classList.toggle("offline", !connected);
            el.innerHTML = connected
                ? "<i></i> MongoDB Atlas Connected"
                : "<i></i> Connection unavailable";
        }

        setText("backendStatus", connected ? "Connected" : "Offline");
    } catch (error) {
        const el = $("connectionStatus");
        if (el) {
            el.classList.add("offline");
            el.innerHTML = "<i></i> Connection unavailable";
        }
        setText("backendStatus", "Offline");
    }
}

/* ========================================================= */
/* WEATHER & AIR QUALITY DISPLAY                             */
/* ========================================================= */

function displayWeather(latest) {
    if (!latest && allReadings.length) {
        // Find newest record with temperature or AQI data
        latest = allReadings.find(r => r.temperature_c !== null && r.temperature_c !== undefined) || allReadings[0];
    }
    if (!latest) return;

    const temp = value(latest, "temperature_c", "temperature");
    const hum = value(latest, "humidity_percent", "humidity");
    const pm25 = latest.pm25;
    const pm10 = latest.pm10;
    const aqi = latest.aqi;
    const dateFormatted = formatDate(value(latest, "recorded_at", "timestamp"));
    const source = latest.data_source || "Open-Meteo";

    // Hero Card
    setText("weatherTemperature", temp !== null ? `${Number(temp).toFixed(1)}°C` : "—°C");
    setText("weatherHeroSub", `Real-time meteorological & air quality observations for Hyderabad, Sindh, Pakistan.`);
    setText("weatherObsTime", `Latest Telemetry: ${dateFormatted} · ${source}`);

    // Weather condition & icons
    const tempNum = Number(temp);
    let conditionText = "Pleasant & Clear";
    let iconText = "🌤️";
    let iconLabel = "Clear Sky";
    let tempTag = "Comfortable";

    if (tempNum >= 35) {
        conditionText = "Very Hot & Sunny";
        iconText = "☀️";
        iconLabel = "High Heat";
        tempTag = "Extreme Heat";
    } else if (tempNum >= 28) {
        conditionText = "Warm & Dry";
        iconText = "☀️";
        iconLabel = "Sunny";
        tempTag = "Warm Climate";
    } else if (tempNum >= 20) {
        conditionText = "Mild & Pleasant";
        iconText = "🌤️";
        iconLabel = "Pleasant";
        tempTag = "Optimal Comfort";
    } else if (tempNum < 20 && tempNum > 0) {
        conditionText = "Cool & Breezy";
        iconText = "🌥️";
        iconLabel = "Cool";
        tempTag = "Cool";
    }

    setText("weatherCondition", conditionText);
    setText("weatherIcon", iconText);
    setText("weatherIconLabel", iconLabel);

    // Weather Grid Elements
    setText("temperatureValue", temp !== null ? Number(temp).toFixed(1) : "—");
    setText("tempFeelBadge", `Thermal: ${tempTag}`);

    setText("humidityValue", hum !== null ? Number(hum).toFixed(1) : "—");
    const humNum = Number(hum);
    let humStatus = "Normal moisture";
    if (humNum < 25) humStatus = "Dry air";
    else if (humNum > 70) humStatus = "High humidity";
    setText("humidityBadge", humStatus);

    setText("pm25Value", pm25 !== null ? Number(pm25).toFixed(1) : "—");
    const pm25Num = Number(pm25);
    let pm25Status = "Moderate particle level";
    if (pm25Num <= 12) pm25Status = "Good (WHO Standard)";
    else if (pm25Num > 35) pm25Status = "Elevated dust level";
    setText("pm25Badge", pm25Status);

    setText("pm10Value", pm10 !== null ? Number(pm10).toFixed(1) : "—");
    setText("aqiValue", aqi !== null ? Math.round(Number(aqi)) : "—");

    // AQI Category & Advisory
    const aqiNum = aqi !== null ? Number(aqi) : null;
    let aqiCat = "Moderate";
    let aqiClass = "moderate";
    let advTitle = "Moderate Air Quality";
    let advMsg = "Air quality is acceptable for most individuals; however, sensitive people with respiratory illnesses should consider limiting prolonged outdoor exertion.";

    if (aqiNum === null || aqiNum === undefined) {
        aqiCat = "Data Pending";
        aqiClass = "neutral";
        advTitle = "Awaiting Telemetry";
        advMsg = "Awaiting air quality index records from MongoDB Atlas.";
    } else if (aqiNum <= 50) {
        aqiCat = "Good (Low Risk)";
        aqiClass = "good";
        advTitle = "Good Air Quality (Low Risk)";
        advMsg = "Air pollution poses little or no health risk. Clean ambient air suitable for all outdoor physical activities.";
    } else if (aqiNum <= 100) {
        aqiCat = "Moderate Quality";
        aqiClass = "moderate";
        advTitle = "Moderate Air Quality";
        advMsg = "Air quality is acceptable; unusually sensitive individuals should consider limiting prolonged outdoor physical exertion.";
    } else if (aqiNum <= 150) {
        aqiCat = "Unhealthy for Sensitive Groups";
        aqiClass = "sensitive";
        advTitle = "Elevated Alert: Sensitive Groups Affected";
        advMsg = "Members of sensitive groups (children, elderly, asthma patients) may experience health effects. General public is less likely to be affected.";
    } else if (aqiNum <= 200) {
        aqiCat = "Unhealthy";
        aqiClass = "unhealthy";
        advTitle = "High Health Warning: Unhealthy Air";
        advMsg = "Everyone may begin to experience adverse health effects; members of sensitive groups may experience more serious health effects.";
    } else {
        aqiCat = "Hazardous (Severe)";
        aqiClass = "hazardous";
        advTitle = "Hazardous Environmental Warning";
        advMsg = "Health warning of emergency conditions: everyone should avoid outdoor exertion and use indoor air filtration.";
    }

    const aqiCatEl = $("aqiCategory");
    if (aqiCatEl) {
        aqiCatEl.textContent = aqiCat;
        aqiCatEl.className = `badge badge-aqi aqi-${aqiClass}`;
    }
    setText("aqiSub", aqiCat);

    // Advisory Card
    setText("advisoryTitle", advTitle);
    setText("advisoryMessage", advMsg);
    const advCard = $("advisoryCard");
    if (advCard) {
        advCard.className = `advisory-card advisory-${aqiClass}`;
    }

    // Populate Weather Observations Table on Weather Page
    const obsTable = $("weatherObservationsTable");
    if (obsTable && allReadings.length) {
        obsTable.innerHTML = allReadings.slice(0, 15).map(r => `
            <tr>
                <td><strong>${formatDate(value(r, "recorded_at", "timestamp"))}</strong></td>
                <td>${formatNumber(value(r, "temperature_c", "temperature"))} °C</td>
                <td>${formatNumber(value(r, "humidity_percent", "humidity"))} %</td>
                <td>${formatNumber(r.pm25)} μg/m³</td>
                <td>${formatNumber(r.pm10)} μg/m³</td>
                <td><span class="badge aqi-badge aqi-${r.aqi <= 50 ? 'good' : r.aqi <= 100 ? 'moderate' : 'sensitive'}">${formatNumber(r.aqi, 0)}</span></td>
                <td><span class="tag-source">${safe(r.data_source || 'historical')}</span></td>
            </tr>
        `).join("") || `<tr><td colspan="7">No records available.</td></tr>`;
    }
}

/* ========================================================= */
/* ANALYTICS POPULATION                                      */
/* ========================================================= */

function displayAnalytics(data) {
    const avgTemp = value(data, "average_temperature_c", "avg_temperature");
    const avgHum = value(data, "average_humidity_percent", "avg_humidity");
    const avgAqi = value(data, "average_aqi", "avg_aqi");

    setText("averageTemperature", avgTemp !== null ? `${formatNumber(avgTemp, 1)} °C` : "—");
    setText("averageHumidity", avgHum !== null ? `${formatNumber(avgHum, 1)} %` : "—");
    setText("averageAQI", avgAqi !== null ? `${formatNumber(avgAqi, 0)} AQI` : "—");

    const aqiStatus = data.aqi_status || {};
    setText("aqiRiskLabel", aqiStatus.message || "Mean environmental index across dataset");
}

/* ========================================================= */
/* DASHBOARD DATA LOADER                                     */
/* ========================================================= */

async function loadDashboard() {
    try {
        const [counts, analytics, readings] = await Promise.all([
            getData(API.counts),
            getData(API.analytics),
            getData(API.readings)
        ]);

        setText("totalSensors", formatNumber(value(counts, "total_sensors", "sensors"), 0));
        setText("totalReadings", formatNumber(value(counts, "total_readings", "readings"), 0));
        setText("totalAlerts", formatNumber(value(counts, "total_alerts", "alerts"), 0));

        displayAnalytics(analytics);

        const records = getArray(readings, "readings");
        allReadings = records;

        if (records.length) {
            displayWeather(records[0]);
        }

        const table = $("dashboardReadings");
        if (table) {
            table.innerHTML = records.slice(0, 6).map(r => `
                <tr>
                    <td><strong>${safe(value(r, "sensor_id", "sensor_name"))}</strong></td>
                    <td>${formatNumber(value(r, "temperature_c", "temperature"))} °C</td>
                    <td>${formatNumber(value(r, "humidity_percent", "humidity"))} %</td>
                    <td>${formatNumber(r.pm25)}</td>
                    <td><span class="badge aqi-${r.aqi <= 50 ? 'good' : r.aqi <= 100 ? 'moderate' : 'sensitive'}">${formatNumber(r.aqi, 0)}</span></td>
                    <td>${formatDate(value(r, "recorded_at", "timestamp"))}</td>
                    <td><span class="tag-source">${safe(r.data_source || 'telemetry')}</span></td>
                </tr>
            `).join("") || `<tr><td colspan="7">No stored readings found.</td></tr>`;
        }
    } catch (err) {
        console.error("Dashboard error:", err);
    }
}

/* ========================================================= */
/* SENSORS & CRUD OPERATIONS                                 */
/* ========================================================= */

function toggleSensorForm() {
    const sec = $("sensorFormSection");
    if (sec) {
        sec.style.display = sec.style.display === "none" ? "block" : "none";
        if (sec.style.display === "block") {
            $("sensorEditSection").style.display = "none";
            $("formSensorId")?.focus();
        }
    }
}

function toggleEditSensorForm() {
    const sec = $("sensorEditSection");
    if (sec) {
        sec.style.display = sec.style.display === "none" ? "block" : "none";
    }
}

function openEditSensorModal(sid, sname, stype, status) {
    const sec = $("sensorEditSection");
    if (sec) {
        $("sensorFormSection").style.display = "none";
        $("editSensorId").value = sid;
        $("editSensorIdDisplay").value = sid;
        $("editSensorName").value = sname;
        $("editSensorType").value = stype;
        $("editSensorStatus").value = status;
        sec.style.display = "block";
        sec.scrollIntoView({ behavior: "smooth" });
        $("editSensorName").focus();
    }
}

async function handleCreateSensor(event) {
    event.preventDefault();
    const sensor_id = $("formSensorId").value.trim();
    const sensor_name = $("formSensorName").value.trim();
    const sensor_type = $("formSensorType").value;
    const status = $("formSensorStatus").value;

    if (!sensor_id || !sensor_name) {
        alert("Please provide both Sensor ID and Sensor Name.");
        return;
    }

    try {
        const res = await fetch(API.sensors, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sensor_id, sensor_name, sensor_type, status })
        });

        const result = await res.json();
        if (res.status === 201) {
            alert(`✅ Sensor "${sensor_id}" registered in MongoDB!`);
            $("addSensorForm").reset();
            toggleSensorForm();
            await loadSensors();
        } else {
            alert(`Error: ${result.error || "Failed to register sensor"}`);
        }
    } catch (err) {
        alert("Network or server error while adding sensor.");
    }
}

async function handleUpdateSensor(event) {
    event.preventDefault();
    const sensor_id = $("editSensorId").value.trim();
    const sensor_name = $("editSensorName").value.trim();
    const sensor_type = $("editSensorType").value;
    const status = $("editSensorStatus").value;

    if (!sensor_name) {
        alert("Please provide a valid sensor name.");
        return;
    }

    try {
        const res = await fetch(`${API.sensors}/${encodeURIComponent(sensor_id)}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sensor_name, sensor_type, status })
        });

        const result = await res.json();
        if (res.ok) {
            alert(`✅ Sensor "${sensor_id}" updated in MongoDB Atlas!`);
            toggleEditSensorForm();
            await loadSensors();
        } else {
            alert(`Error: ${result.error || "Failed to update sensor"}`);
        }
    } catch (err) {
        alert("Network or server error while updating sensor.");
    }
}

async function handleDeleteSensor(sensorId) {
    if (!confirm(`Are you sure you want to delete sensor "${sensorId}" from MongoDB?`)) {
        return;
    }

    try {
        const res = await fetch(`${API.sensors}/${encodeURIComponent(sensorId)}`, {
            method: "DELETE"
        });

        const result = await res.json();
        if (res.ok) {
            alert(`✅ Sensor "${sensorId}" deleted successfully.`);
            await loadSensors();
        } else {
            alert(`Error: ${result.error || "Could not delete sensor."}`);
        }
    } catch (err) {
        alert("Error connecting to server to delete sensor.");
    }
}

function renderSensors() {
    const q = ($("sensorSearch")?.value || "").toLowerCase();
    const filtered = allSensors.filter(s =>
        JSON.stringify(s).toLowerCase().includes(q)
    );

    const container = $("sensorContainer");
    if (!container) return;

    container.innerHTML = filtered.map(s => {
        const sid = safe(value(s, "sensor_id", "_id"));
        const sname = safe(value(s, "sensor_name", "name", sid));
        const stype = safe(value(s, "sensor_type", "type") || "weather");
        const status = safe(s.status || "active").toLowerCase();
        const loc = safe(value(s, "location_name", "location") || "Hyderabad Station");
        const installed = formatDate(s.installed_at);

        return `
            <div class="sensor-card">
                <div class="sensor-card-header">
                    <div>
                        <h3>${sname}</h3>
                        <span class="sensor-id-pill">${sid}</span>
                    </div>
                    <span class="status-chip ${status === 'active' ? 'chip-active' : 'chip-inactive'}">
                        ● ${status.toUpperCase()}
                    </span>
                </div>
                <div class="sensor-card-body">
                    <p><strong>Type:</strong> ${stype}</p>
                    <p><strong>Location:</strong> ${loc}</p>
                    <p><strong>Installed:</strong> ${installed}</p>
                </div>
                <div class="sensor-card-actions">
                    <button class="btn-edit" onclick="openEditSensorModal('${sid}', '${sname.replace(/'/g, "\\'")}', '${stype}', '${status}')">✏️ Edit</button>
                    <button class="btn-delete" onclick="handleDeleteSensor('${sid}')">🗑️ Delete</button>
                </div>
            </div>
        `;
    }).join("") || "<p class='no-records'>No matching sensor records found.</p>";
}

async function loadSensors() {
    const data = await getData(API.sensors);
    allSensors = getArray(data, "sensors");
    renderSensors();
}

/* ========================================================= */
/* READINGS & HISTORY TABLES                                 */
/* ========================================================= */

function renderReadings(target, records) {
    const tbody = $(target);
    if (!tbody) return;

    tbody.innerHTML = records.map(r => `
        <tr>
            <td><strong>${safe(value(r, "sensor_id", "sensor_name"))}</strong></td>
            <td>${formatNumber(value(r, "temperature_c", "temperature"))}</td>
            <td>${formatNumber(value(r, "humidity_percent", "humidity"))}</td>
            <td>${formatNumber(r.pm25)}</td>
            ${target === "historyTable" ? `<td>${formatNumber(r.pm10)}</td>` : ""}
            <td><span class="badge aqi-${r.aqi <= 50 ? 'good' : r.aqi <= 100 ? 'moderate' : 'sensitive'}">${formatNumber(r.aqi, 0)}</span></td>
            <td>${formatDate(value(r, "recorded_at", "timestamp"))}</td>
        </tr>
    `).join("") || `<tr><td colspan="7">No records found.</td></tr>`;
}

async function loadReadings() {
    const data = await getData(API.readings);
    allReadings = getArray(data, "readings");
    renderReadings("readingsTable", allReadings);
    renderReadings("historyTable", allReadings);
}

/* ========================================================= */
/* ALERTS                                                    */
/* ========================================================= */

function renderAlerts() {
    const q = ($("alertSearch")?.value || "").toLowerCase();
    const filtered = allAlerts.filter(a =>
        JSON.stringify(a).toLowerCase().includes(q)
    );

    const container = $("alertContainer");
    if (!container) return;

    container.innerHTML = filtered.map(a => {
        const severity = value(a, "severity", "level", "status") || "Medium";
        const cls = /critical|high|severe/i.test(severity)
            ? "danger"
            : /warning|medium/i.test(severity)
            ? "warning"
            : "info";

        return `
            <div class="alert-card alert-border-${cls}">
                <div class="alert-top">
                    <h3>${safe(value(a, "title", "alert_type", "type") || "Environmental Warning")}</h3>
                    <span class="severity-badge sev-${cls}">${safe(severity).toUpperCase()}</span>
                </div>
                <p class="alert-msg">${safe(value(a, "message", "description", "details"))}</p>
                <div class="alert-meta">
                    <span>📡 Device: <strong>${safe(a.sensor_id || "System")}</strong></span>
                    <span>🕒 ${formatDate(value(a, "created_at", "timestamp"))}</span>
                </div>
            </div>
        `;
    }).join("") || "<p class='no-records'>No alerts found.</p>";
}

async function loadAlerts() {
    const data = await getData(API.alerts);
    allAlerts = getArray(data, "alerts");
    renderAlerts();
}

/* ========================================================= */
/* SEARCH LISTENERS                                          */
/* ========================================================= */

function setupSearch(id, target) {
    const input = $(id);
    if (!input) return;

    input.addEventListener("input", () => {
        const q = input.value.toLowerCase();
        const filtered = allReadings.filter(r =>
            JSON.stringify(r).toLowerCase().includes(q)
        );
        renderReadings(target, filtered);
    });
}

/* ========================================================= */
/* TREND CANVAS CHART                                        */
/* ========================================================= */

function drawChart() {
    const canvas = $("trendChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const width = canvas.parentElement.clientWidth || 800;
    const height = 300;
    const dpr = window.devicePixelRatio || 1;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";

    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const records = allReadings
        .slice(0, 24)
        .reverse()
        .filter(r => Number.isFinite(Number(r.temperature_c)));

    if (!records.length) {
        ctx.fillStyle = "#64748b";
        ctx.font = "14px 'Plus Jakarta Sans', sans-serif";
        ctx.fillText("No temperature readings available to chart.", 30, 40);
        return;
    }

    const values = records.map(r => Number(r.temperature_c));
    let min = Math.min(...values);
    let max = Math.max(...values);
    if (min === max) { min -= 2; max += 2; }

    const padLeft = 45;
    const padRight = 30;
    const padTop = 30;
    const padBottom = 40;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    // Gridlines
    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#94a3b8";
    ctx.font = "11px 'Plus Jakarta Sans', sans-serif";

    for (let i = 0; i <= 4; i++) {
        const y = padTop + (i * plotH / 4);
        const val = (max - (i * (max - min) / 4)).toFixed(1);

        ctx.beginPath();
        ctx.moveTo(padLeft, y);
        ctx.lineTo(width - padRight, y);
        ctx.stroke();

        ctx.fillText(`${val}°C`, 5, y + 4);
    }

    // Gradient Area Fill
    const gradient = ctx.createLinearGradient(0, padTop, 0, padTop + plotH);
    gradient.addColorStop(0, "rgba(59, 130, 246, 0.25)");
    gradient.addColorStop(1, "rgba(59, 130, 246, 0.0)");

    ctx.beginPath();
    values.forEach((v, i) => {
        const x = padLeft + (i * plotW / (values.length - 1));
        const y = padTop + plotH - ((v - min) / (max - min)) * plotH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    const lastX = padLeft + plotW;
    const firstX = padLeft;
    ctx.lineTo(lastX, padTop + plotH);
    ctx.lineTo(firstX, padTop + plotH);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Line Plot
    ctx.beginPath();
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 3;
    values.forEach((v, i) => {
        const x = padLeft + (i * plotW / (values.length - 1));
        const y = padTop + plotH - ((v - min) / (max - min)) * plotH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Data points
    values.forEach((v, i) => {
        const x = padLeft + (i * plotW / (values.length - 1));
        const y = padTop + plotH - ((v - min) / (max - min)) * plotH;

        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = "#ffffff";
        ctx.fill();
        ctx.strokeStyle = "#2563eb";
        ctx.lineWidth = 2.5;
        ctx.stroke();
    });
}

/* ========================================================= */
/* 5 MONGODB AGGREGATION PIPELINES RUNNER                    */
/* ========================================================= */

async function loadAggregationPipelines() {
    try {
        const data = await getData("/api/aggregations/run");
        if (data.status === "success") {
            setText("pipeline1Output", JSON.stringify(data.pipeline_1_sensor_averages, null, 2));
            setText("pipeline2Output", JSON.stringify(data.pipeline_2_hourly_distribution, null, 2));
            setText("pipeline3Output", JSON.stringify(data.pipeline_3_daily_summary_last_7_days, null, 2));
            setText("pipeline4Output", JSON.stringify(data.pipeline_4_temperature_buckets, null, 2));
            setText("pipeline5Output", JSON.stringify(data.pipeline_5_humidity_buckets, null, 2));
        }
    } catch (err) {
        console.error("Aggregation run error:", err);
        setText("pipeline1Output", "Error executing aggregation pipeline on Atlas.");
    }
}

/* ========================================================= */
/* PAGE INITIALIZER                                          */
/* ========================================================= */

async function loadPageData() {
    const page = typeof CURRENT_PAGE === "undefined" ? "dashboard" : CURRENT_PAGE;
    await checkConnection();

    try {
        if (page === "dashboard") {
            await loadDashboard();
        } else if (page === "weather") {
            await Promise.all([loadReadings(), loadDashboard()]);
            if (allReadings.length) {
                displayWeather(allReadings[0]);
            }
        } else if (page === "analytics") {
            await Promise.all([loadReadings(), loadDashboard()]);
            drawChart();
            loadAggregationPipelines();
        } else if (page === "sensors") {
            await loadSensors();
        } else if (page === "latest" || page === "history") {
            await loadReadings();
        } else if (page === "alerts") {
            await loadAlerts();
        }
    } catch (err) {
        console.error("Page loader error:", err);
    }
}

/* ========================================================= */
/* NAVIGATION & EVENT LISTENERS                              */
/* ========================================================= */

function toggleMenu() {
    const sb = $("sidebar");
    if (sb) sb.classList.toggle("show");
}

document.addEventListener("DOMContentLoaded", () => {
    setText("currentDate", new Date().toDateString());

    if ($("sensorSearch")) $("sensorSearch").addEventListener("input", renderSensors);
    if ($("alertSearch")) $("alertSearch").addEventListener("input", renderAlerts);

    setupSearch("readingSearch", "readingsTable");
    setupSearch("historySearch", "historyTable");

    loadPageData();

    // Handle window resize for canvas chart
    window.addEventListener("resize", () => {
        if (typeof CURRENT_PAGE !== "undefined" && CURRENT_PAGE === "analytics") {
            drawChart();
        }
    });
});
