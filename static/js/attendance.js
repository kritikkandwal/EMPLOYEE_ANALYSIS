// static/js/attendance.js
// Cleaned single file to manage attendance UI, calendar, and ML predictions

class AttendancePredictions {



    async load() {
        try {
            const res = await fetch("/api/attendance/predictions");
            const data = await res.json();

            if (!data || !data.success) return;
            this.render(data.predictions);
        } catch (e) {
            console.error("AI attendance prediction error:", e);
        }
    }

    render(p) {
        if (!p) return;
        const tom = p.tomorrow_prediction || {};

        const probEl = document.getElementById("tomorrowProbability");
        if (probEl) probEl.textContent = (tom.probability ?? 0) + "%";

        const confEl = document.getElementById("confidenceLevel");
        if (confEl) confEl.textContent = tom.confidence ?? "N/A";

        const hoursEl = document.getElementById("expectedHours");
        if (hoursEl) hoursEl.textContent = tom.expected_hours ?? "0";

        const modelEl = document.getElementById("modelUsed");
        if (modelEl) modelEl.textContent = tom.model_used ?? "N/A";

        // weekly
        const box = document.getElementById("weeklyDaysGrid");
        if (box) {
            box.innerHTML = "";
            (p.weekly_trend || []).forEach(d => {
                box.innerHTML += `
                    <div class="day-prediction">
                        <div class="day-name">${d.day || ""}</div>
                        <div class="day-probability">${d.probability ?? 0}%</div>
                        <div class="day-date">${(d.date || "").split("-").pop()}</div>
                    </div>
                `;
            });

            const avgEl = document.getElementById("weeklyAvg");
            if (avgEl && p.weekly_trend.length) {
                const sum = p.weekly_trend.reduce((s, x) => s + (x.probability || 0), 0);
                avgEl.textContent = (sum / p.weekly_trend.length).toFixed(1) + "%";
            }
        }

        // streak
        const streakProb = document.getElementById("streakProbability");
        if (streakProb) streakProb.textContent = (p.streak_analysis?.probability_continue ?? 0) + "%";

        const expectedContinuation = document.getElementById("expectedContinuation");
        if (expectedContinuation) expectedContinuation.textContent = p.streak_analysis?.expected_end_in ?? 0;

        // absence
        const absenceRisk = document.getElementById("absenceRisk");
        if (absenceRisk) {
            const rl = p.absence_likelihood?.risk_level ?? "low";
            absenceRisk.innerHTML = `<span class="risk-badge ${rl}">${rl.toUpperCase()} RISK</span>`;
        }

        const absenceProb = document.getElementById("absenceProbability");
        if (absenceProb) absenceProb.textContent = ((p.absence_likelihood?.probability ?? 0) * 100).toFixed(1) + "%";

        const factorsList = document.getElementById("riskFactorsList");
        if (factorsList) {
            factorsList.innerHTML = (p.absence_likelihood?.factors || []).map(f => `<li>${f}</li>`).join("");
        }
    }
}



class AttendanceManager {
    constructor() {
        this.currentDate = new Date();
        this.predictions = null;
        this.init();
    }

    _generateRandomAttendanceMap(startDate, endDate) {
        const map = {};
        const cursor = new Date(startDate);

        while (cursor <= endDate) {
            const iso = cursor.toISOString().slice(0, 10);

            // skip today
            const todayISO = new Date().toISOString().slice(0, 10);
            if (iso === todayISO) {
                cursor.setDate(cursor.getDate() + 1);
                continue;
            }

            // skip future
            if (cursor > new Date()) break;

            // random status
            const rnd = Math.random();
            let status = "absent";
            let hours = 0;

            if (rnd > 0.7) {                // 30%
                status = "present";
                hours = Math.floor(6 + Math.random() * 3);  // 6–9 hrs
            }
            else if (rnd > 0.5) {           // 20%
                status = "half-day";
                hours = Math.floor(3 + Math.random() * 2);  // 3–5 hrs
            }
            else {                          // 50%
                status = "absent";
                hours = 0;
            }

            map[iso] = {
                date: iso,
                status: status,
                hours_worked: hours
            };

            cursor.setDate(cursor.getDate() + 1);
        }
        return map;
    }



    init() {
        this.loadCurrentStatus();

        // ✔ REPLACED MONTHLY CALENDAR WITH YEAR HEATMAP
        this.loadYearHeatmap();

        this.loadPredictions();
        this.loadInsights();
        this.setupEventListeners();
        this.startClock();
    }

    startClock() {
        const update = () => {
            const now = new Date();
            const el = document.getElementById("currentTime");
            if (el) {
                el.textContent = now.toLocaleTimeString('en-US', {
                    hour12: true,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
            }
        };
        update();
        setInterval(update, 1000);
    }

    setupEventListeners() {
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');
        if (loginBtn) loginBtn.addEventListener('click', () => this.logAttendance('login'));
        if (logoutBtn) logoutBtn.addEventListener('click', () => this.logAttendance('logout'));

        const prev = document.getElementById('prevMonth');
        const next = document.getElementById('nextMonth');
        if (prev) prev.addEventListener('click', () => this.changeMonth(-1));
        if (next) next.addEventListener('click', () => this.changeMonth(1));

        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabPanes.forEach(p => p.classList.remove('active'));

                button.classList.add('active');
                const pane = document.getElementById(`${button.dataset.tab}-tab`);
                if (pane) pane.classList.add('active');
            });
        });
    }



    /* -------------------------- INSIGHTS -------------------------- */
    async loadInsights() {
        try {
            const res = await fetch('/api/attendance/insights');
            const data = await res.json();

            if (!data.success) throw new Error(data.error);

            const i = data.insights;

            document.getElementById("predictionsContent").innerHTML = `
                <div class="prediction-item">
                    <div class="prediction-icon"><i class="fas fa-chart-line"></i></div>
                    <div class="prediction-content">
                        <h4>Attendance Accuracy</h4>
                        <p>${i.predicted_attendance_rate}% expected attendance</p>
                    </div>
                </div>
                <div class="prediction-item">
                    <div class="prediction-icon"><i class="fas fa-brain"></i></div>
                    <div class="prediction-content">
                        <h4>Confidence Level</h4>
                        <p>${(i.confidence_score * 100).toFixed(0)}% model confidence</p>
                    </div>
                </div>
                <div class="prediction-item">
                    <div class="prediction-icon"><i class="fas fa-lightbulb"></i></div>
                    <div class="prediction-content">
                        <h4>AI Recommendations</h4>
                        <p>${i.recommended_improvements[0]}</p>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error("Insights error:", error);
            document.getElementById("predictionsContent").innerHTML =
                "<p>Error loading insights</p>";
        }
    }

    



    /* -------------------------- ATTENDANCE LOG -------------------------- */
    async logAttendance(action) {
        try {
            const response = await fetch('/api/attendance/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            });

            const result = await response.json();
            if (!result.success) {
                this.showNotification(result.message || result.error, "error");
                return;
            }

            this.showNotification(result.message, "success");

            await this.loadCurrentStatus();
            await new Promise(r => setTimeout(r, 300));
            await this.loadYearHeatmap();
            await this.loadPredictions();

        } catch (err) {
            console.error('Attendance logging error:', err);
            this.showNotification('Attendance logging failed', 'error');
        }
    }



    /* -------------------------- CURRENT STATUS -------------------------- */
    async loadCurrentStatus() {
        try {
            const res = await fetch('/api/attendance/current-status');
            const data = await res.json();

            // stats
            document.getElementById('presentDays').textContent = data.present_days ?? 0;
            document.getElementById('attendanceRate').textContent =
                data.present_days > 0 ? "100%" : "0%";
            document.getElementById('totalHours').textContent = data.total_hours ?? 0;
            document.getElementById('currentStreak').textContent = data.present_days ?? 0;

            const todayStatus = document.getElementById('todayStatus');

            if (!data.logged_in) {
                todayStatus.innerHTML = `
                    <div class="status-card status-absent">
                        <div class="status-icon">❌</div>
                        <div class="status-message">Not Logged In Today</div>
                        <div class="status-details">Click "Log In" to start tracking</div>
                    </div>
                `;
            } else {
                const s = data.status || 'present';
                const cls =
                    s === 'present' ? 'status-present' :
                        s === 'half-day' ? 'status-half-day' :
                            'status-absent';

                const icon =
                    s === 'present' ? '✅' :
                        s === 'half-day' ? '🟡' :
                            '❌';

                todayStatus.innerHTML = `
                    <div class="status-card ${cls}">
                        <div class="status-icon">${icon}</div>
                        <div class="status-message">${s.toUpperCase()}</div>
                        <div class="status-details">Hours: ${data.total_hours}</div>
                    </div>
                `;
            }

        } catch (err) {
            console.error("Current status loading error:", err);
        }
    }



    /* ===================================================================
       🔵 GITHUB YEAR HEATMAP (REPLACES loadCalendar)
       =================================================================== */
    async loadYearHeatmap() {
        try {
            const today = new Date();
            const endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
            const startDate = new Date(endDate);
            startDate.setDate(endDate.getDate() - 364);

            const startDow = startDate.getDay();
            if (startDow !== 0) startDate.setDate(startDate.getDate() - startDow);

            const monthRequests = this._getMonthRequestsForRange(startDate, endDate);
            const monthData = await this._fetchMonthlyData(monthRequests);
            let recMap = this._buildDateMapFromMonths(monthData);

            // If no attendance data → fill with random values
            const hasAnyData = Object.keys(recMap).length > 0;

            if (!hasAnyData) {
                console.warn("⚠ No attendance data found. Generating random history...");
                recMap = this._generateRandomAttendanceMap(startDate, endDate);
            }


            const container = document.getElementById("attendanceCalendar");
            if (!container) return;

            const weekCount = 52;
            container.style.setProperty("--week-count", weekCount);

            // ---- BUILD MONTH LABELS ----
            let html = `<div class="year-heatmap-wrapper">`;

            html += `<div class="heatmap-month-row">`;
            const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

            let prevMonth = null;
            for (let w = 0; w < weekCount; w++) {
                const date = new Date(startDate);
                date.setDate(startDate.getDate() + w * 7);
                const m = date.getMonth();
                const label = (date.getDate() <= 7 && m !== prevMonth) ? monthNames[m] : "";
                html += `<div class="month-label">${label}</div>`;
                prevMonth = m;
            }
            html += `</div>`;

            // ---- MAIN HEATMAP ----
            html += `<div style="display:flex;align-items:flex-start;">
                    <div class="heatmap-left-labels">
                        <div>Sun</div><div>Mon</div><div>Tue</div>
                        <div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div>
                    </div>
                    <div class="year-heatmap">`;

            // Build month blocks
            let currentMonthIndex = -1;
            let monthHTML = "";

            for (let w = 0; w < weekCount; w++) {
                const date = new Date(startDate);
                date.setDate(startDate.getDate() + w * 7);

                const m = date.getMonth();

                // Month change → push block
                if (m !== currentMonthIndex) {
                    if (currentMonthIndex !== -1)
                        html += `<div class="month-block">${monthHTML}</div>`;
                    monthHTML = "";
                    currentMonthIndex = m;
                }

                // Build one week column
                let weekCol = `<div class="week-column">`;

                for (let d = 0; d < 7; d++) {
                    const cellDate = new Date(startDate);
                    cellDate.setDate(startDate.getDate() + w * 7 + d);

                    const iso = cellDate.toISOString().slice(0, 10);
                    const entry = recMap[iso];
                    const isWeekend = cellDate.getDay() >= 5;

                    let cls = "absent";
                    if (entry) {
                        if (entry.status === "present") {
                            const h = Number(entry.hours_worked);
                            if (h >= 8) cls = "present";
                            else if (h >= 6) cls = "present-2";
                            else cls = "present-1";
                        } else if (entry.status === "half-day") cls = "half-day";
                        else cls = "absent";
                    } else if (isWeekend) cls = "weekend";

                    const todayStr = new Date().toISOString().slice(0, 10);
                    if (iso === todayStr) cls += " today";

                    weekCol += `<div class="heat-day ${cls}" title="${iso}"></div>`;
                }

                weekCol += `</div>`;
                monthHTML += weekCol;
            }

            // Push last month block
            html += `<div class="month-block">${monthHTML}</div>`;

            html += `</div></div></div>`;
            container.innerHTML = html;

            // Legend
            const legend = document.createElement("div");
            legend.className = "heatmap-legend";
            legend.innerHTML = `
            <div><strong>Legend</strong></div>
            <div class="box" style="background:#2f81f7"></div> Present (8h+)
            <div class="box" style="background:#5b9fff"></div> Present (6–8h)
            <div class="box" style="background:#9fc8ff"></div> Present (0–6h)
            <div class="box" style="background:#184a8f"></div> Half-day
            <div class="box" style="background:#111"></div> Absent
            <div class="box" style="background:#1a1a1a"></div> Weekend`;
            container.appendChild(legend);

            this._attachHeatmapHover();

        } catch (err) {
            console.error("Year heatmap error:", err);
            this.renderEmptyCalendar();
        }
    }





    _getMonthRequestsForRange(startDate, endDate) {
        const months = new Set();
        const cursor = new Date(startDate);

        while (cursor <= endDate) {
            months.add(`${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, '0')}`);
            cursor.setDate(cursor.getDate() + 1);
        }

        return Array.from(months).map(v => {
            const [y, m] = v.split('-');
            return { year: Number(y), month: Number(m) };
        });
    }

    async _fetchMonthlyData(monthRequests) {
        const promises = monthRequests.map(m => {
            return fetch(`/api/attendance/monthly?year=${m.year}&month=${m.month}`)
                .then(r => r.json())
                .then(json => ({ year: m.year, month: m.month, records: json.records || [] }))
                .catch(() => ({ year: m.year, month: m.month, records: [] }));
        });

        return Promise.all(promises);
    }

    _buildDateMapFromMonths(monthData) {
        const map = {};
        monthData.forEach(m => {
            m.records.forEach(r => map[r.date] = r);
        });
        return map;
    }

    _attachHeatmapHover() {
        if ('ontouchstart' in window) return;

        const tooltip = document.createElement('div');
        tooltip.style.position = 'fixed';
        tooltip.style.pointerEvents = 'none';
        tooltip.style.padding = '8px 10px';
        tooltip.style.background = 'var(--bg-card)';
        tooltip.style.border = '1px solid var(--glass-border)';
        tooltip.style.borderRadius = '6px';
        tooltip.style.fontSize = '0.75rem';
        tooltip.style.color = 'var(--text-primary)';
        tooltip.style.boxShadow = '0 6px 18px rgba(0,0,0,0.6)';
        tooltip.style.display = 'none';
        document.body.appendChild(tooltip);

        document.querySelectorAll('.heat-day').forEach(node => {
            node.addEventListener('mouseenter', () => {
                tooltip.textContent = node.getAttribute('title');
                tooltip.style.display = 'block';
            });
            node.addEventListener('mousemove', e => {
                tooltip.style.left = (e.pageX + 12) + 'px';
                tooltip.style.top = (e.pageY + 12) + 'px';
            });
            node.addEventListener('mouseleave', () => tooltip.style.display = 'none');
        });
    }



    /* -------------------------- PREDICTIONS -------------------------- */
    async loadPredictions() {
        try {
            const res = await fetch('/api/attendance/predictions');
            const data = await res.json();

            if (!data.success) throw new Error(data.error);
            this.predictions = data.predictions;

            this.renderPredictions();

        } catch (err) {
            console.error("Predictions loading error:", err);
            this.predictions = null;
            this.renderFallbackPredictions();
        }
    }

    renderPredictions() {
        const p = this.predictions;
        if (!p) return;

        const tom = p.tomorrow_prediction || {};
        document.getElementById('tomorrowProbability').textContent = (tom.probability || 0) + "%";
        document.getElementById('confidenceLevel').textContent = tom.confidence || "N/A";
        document.getElementById('expectedHours').textContent = tom.expected_hours || 0;
        document.getElementById('modelUsed').textContent = tom.model_used || "N/A";

        const grid = document.getElementById("weeklyDaysGrid");
        if (grid) {
            grid.innerHTML = "";
            (p.weekly_trend || []).forEach(d => {
                grid.innerHTML += `
                    <div class="day-prediction">
                        <div class="day-name">${d.day}</div>
                        <div class="day-probability">${d.probability}%</div>
                    </div>
                `;
            });
        }

        document.getElementById("streakProbability").textContent =
            (p.streak_analysis?.probability_continue || 0) + "%";

        document.getElementById("expectedContinuation").textContent =
            p.streak_analysis?.expected_end_in || 0;

        const rl = p.absence_likelihood?.risk_level || "low";
        document.getElementById("absenceRisk").innerHTML =
            `<span class="risk-badge ${rl}">${rl.toUpperCase()} RISK</span>`;

        document.getElementById("absenceProbability").textContent =
            ((p.absence_likelihood?.probability || 0) * 100).toFixed(1) + "%";

        document.getElementById("riskFactorsList").innerHTML =
            (p.absence_likelihood?.factors || []).map(f => `<li>${f}</li>`).join("");
    }

    renderFallbackPredictions() {
        const fallback = {
            tomorrow_prediction: { probability: 65, confidence: 'medium', expected_hours: 6, model_used: 'Fallback' },
            weekly_trend: [{ day: 'Mon', probability: 65 }],
            streak_analysis: { current_streak: 2, probability_continue: 55, expected_end_in: 3 },
            absence_likelihood: { risk_level: 'low', probability: 0.25, factors: ['Limited data'] }
        };
        this.predictions = fallback;
        this.renderPredictions();
        this.showNotification("Using fallback predictions", "warning");
    }



    showNotification(message, type = "info") {
        if (window.dashboardAnimations?.showNotification) {
            window.dashboardAnimations.showNotification(message, type);
        } else {
            console.log(type.toUpperCase(), message);
        }
    }
}



async function refreshPredictions() {
    await window.attendanceManager.loadPredictions();
    window.attendanceManager.showNotification("Predictions refreshed", "success");
}

async function trainModels() {
    try {
        const response = await fetch('/train-attendance-models');
        const result = await response.json();

        if (!result.success) throw new Error(result.error);
        window.attendanceManager.showNotification('Model training triggered', 'success');

        setTimeout(refreshPredictions, 1500);

    } catch (err) {
        console.error(err);
        window.attendanceManager.showNotification("Training failed", "error");
    }
}





document.addEventListener('DOMContentLoaded', () => {
    window.attendanceAI = new AttendancePredictions();
    window.attendanceAI.load();

    window.attendanceManager = new AttendanceManager();
});
