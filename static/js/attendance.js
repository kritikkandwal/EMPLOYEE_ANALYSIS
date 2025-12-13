// static/js/attendance.js
// Cleaned file to manage attendance UI, calendar, and ML predictions (NO MOCK DATA)

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

    init() {
        this.loadCurrentStatus();
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

            const presentMonth = data.present_days_month ?? 0;
            const attendanceRateMonth = (data.attendance_rate_month ?? 0) + "%";
            const totalHoursMonth = data.total_hours_month ?? 0;
            const currentStreakMonth = data.current_streak_month ?? 0;

            document.getElementById('presentDays').textContent = presentMonth;
            document.getElementById('attendanceRate').textContent = attendanceRateMonth;
            document.getElementById('totalHours').textContent = totalHoursMonth;
            document.getElementById('currentStreak').textContent = currentStreakMonth;

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
   GITHUB YEAR HEATMAP
   =================================================================== */
    async loadYearHeatmap() {
        try {
            const today = new Date();

            // --- LOCAL "today" in YYYY-MM-DD (no UTC shift) ---
            const todayIso =
                today.getFullYear() +
                "-" +
                String(today.getMonth() + 1).padStart(2, "0") +
                "-" +
                String(today.getDate()).padStart(2, "0");

            const endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
            const startDate = new Date(endDate);
            startDate.setDate(endDate.getDate() - 364);

            const startDow = startDate.getDay();
            if (startDow !== 0) startDate.setDate(startDate.getDate() - startDow);

            // STEP 2 - Replace with RANDOM generation
            // get today's ISO and real status for today ONLY
            const todayIsoForRandom = new Date().toISOString().slice(0, 10);

            let todayRealRecord = null;
            try {
                const realStatus = await fetch('/api/attendance/current-status').then(r => r.json());
                if (realStatus.success !== false) {
                    todayRealRecord = {
                        status: realStatus.status || "absent",
                        hours_worked: realStatus.total_hours || 0
                    };
                }
            } catch (e) { }

            let recMap = await this._buildAttendanceMapFromCSV(startDate, endDate, todayIsoForRandom, todayRealRecord);


            const container = document.getElementById("attendanceCalendar");
            if (!container) return;

            const weekCount = 52;
            container.style.setProperty("--week-count", weekCount);

            // ---------------- NEW MONTHLY GRID HEATMAP ----------------
            container.innerHTML = "";

            const currentYear = today.getFullYear();
            const calendarRow = document.createElement("div");
            calendarRow.className = "calendar-row";
            container.appendChild(calendarRow);

            for (let month = 0; month < 12; month++) {
                const monthContainer = document.createElement("div");
                monthContainer.className = "month-container";

                const monthTitle = document.createElement("div");
                monthTitle.className = "month-title";
                monthTitle.textContent = new Date(currentYear, month)
                    .toLocaleString("default", { month: "short" });

                monthContainer.appendChild(monthTitle);

                // Weekday headings
                const weekdaysRow = document.createElement("div");
                weekdaysRow.className = "weekdays";
                ["S", "M", "T", "W", "T", "F", "S"].forEach(d => {
                    const label = document.createElement("div");
                    label.className = "weekday";
                    label.textContent = d;
                    weekdaysRow.appendChild(label);
                });
                monthContainer.appendChild(weekdaysRow);

                // Month grid
                const grid = document.createElement("div");
                grid.className = "days-grid";

                const firstDay = new Date(currentYear, month, 1);
                const totalDays = new Date(currentYear, month + 1, 0).getDate();
                const startOffset = firstDay.getDay();

                // Empty before first day
                for (let i = 0; i < startOffset; i++) {
                    const empty = document.createElement("div");
                    empty.className = "day-cell empty";
                    grid.appendChild(empty);
                }

                // Attendance cells
                for (let d = 1; d <= totalDays; d++) {
                    const dateObj = new Date(currentYear, month, d);

                    // ❗ NO toISOString() here – build ISO manually in local time
                    const iso =
                        currentYear +
                        "-" +
                        String(month + 1).padStart(2, "0") +
                        "-" +
                        String(d).padStart(2, "0");

                    const cell = document.createElement("div");
                    cell.className = "day-cell";

                    const entry = recMap[iso];
                    const isWeekend = entry && entry.status === "weekend";


                    let cls = "absent";

                    if (entry) {
                        switch (entry.status) {
                            case "present":
                                const h = Number(entry.hours_worked);
                                if (h >= 8) cls = "present";
                                else if (h >= 6) cls = "present-2";
                                else cls = "present-1";
                                break;

                            case "half-day":
                                cls = "half-day";
                                break;

                            case "weekend":
                                cls = "weekend";
                                break;

                            case "absent":
                                cls = "absent";
                                break;

                            default:
                                cls = "absent";
                        }
                    } else if (entry?.status === "weekend") {
                        cls = "weekend";
                    }



                    // highlight *local* today
                    if (iso === todayIso) {
                        cell.classList.add("today");
                    }

                    cell.classList.add(cls);
                    cell.title = `${iso} — ${entry ? entry.status : "No Data"}`;

                    grid.appendChild(cell);
                }

                monthContainer.appendChild(grid);
                calendarRow.appendChild(monthContainer);

                // enable month click
                monthContainer.dataset.year = currentYear;
                monthContainer.dataset.month = month + 1;

                monthContainer.addEventListener("click", () => {
                    document
                        .querySelectorAll(".month-container")
                        .forEach(m => m.classList.remove("month-selected"));
                    monthContainer.classList.add("month-selected");

                    this.loadMonthlyStats(
                        Number(monthContainer.dataset.year),
                        Number(monthContainer.dataset.month)
                    );
                });
            }

            // Legend
            const legend = `
        <div class="calendar-legend">
            <div class="legend-item"><div class="color-box present"></div> Present (8h+)</div>
            <div class="legend-item"><div class="color-box present-2"></div> Present (6–8h)</div>
            <div class="legend-item"><div class="color-box present-1"></div> Present (0–6h)</div>
            <div class="legend-item"><div class="color-box half-day"></div> Half-day</div>
            <div class="legend-item"><div class="color-box absent"></div> Absent</div>
            <div class="legend-item"><div class="color-box weekend"></div> Weekend</div>
        </div>`;

            const currentMonth = today.getMonth();
            const allMonths = container.querySelectorAll(".month-container");

            if (allMonths[currentMonth]) {
                allMonths[currentMonth].classList.add("month-selected");
                this.loadMonthlyStats(currentYear, currentMonth + 1);
            }

            container.insertAdjacentHTML("beforeend", legend);
        } catch (err) {
            console.error("Year heatmap error:", err);
            this.renderEmptyCalendar?.();
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

    async loadMonthlyStats(year, month) {
        try {
            const res = await fetch(`/api/attendance/monthly?year=${year}&month=${month}`);
            const data = await res.json();

            if (!data.success) return;

            const records = data.records || [];
            let present = 0;
            let hours = 0;

            const working = records.filter(r => !r.is_weekend);

            working.forEach(r => {
                if (r.status === "present") present++;
                hours += r.hours_worked;
            });

            const attendanceRate = working.length
                ? Math.round((present / working.length) * 100)
                : 0;

            document.getElementById('presentDays').textContent = present;
            document.getElementById('attendanceRate').textContent = attendanceRate + "%";
            document.getElementById('totalHours').textContent = hours.toFixed(2);

        } catch (err) {
            console.error("Monthly Stats Error:", err);
        }
    }

    async _buildAttendanceMapFromCSV(startDate, endDate, todayIso, todayRealRecord) {
        let csv = {};
        
        try {
            const res = await fetch("/api/attendance/all-days");
            const data = await res.json();
            if (data.success) csv = data.records;
        } catch (e) {
            console.error("CSV load error:", e);
        }
    
        const map = {};
        const cursor = new Date(startDate);
    
        while (cursor <= endDate) {
        
            const iso =
                cursor.getFullYear() +
                "-" +
                String(cursor.getMonth() + 1).padStart(2, "0") +
                "-" +
                String(cursor.getDate()).padStart(2, "0");
        
            const dow = cursor.getDay();
        
            // 1️⃣ Load CSV if exists
            if (csv[iso]) {
                map[iso] = {
                    status: csv[iso].status,
                    hours_worked: csv[iso].hours_worked
                };
            }
            // 2️⃣ Fallback: weekend/absent
            else {
                map[iso] = {
                    status: (dow === 0 || dow === 6) ? "weekend" : "absent",
                    hours_worked: 0
                };
            }
        
            // 3️⃣ Today overrides CSV
            if (iso === todayIso && todayRealRecord) {
                map[iso] = {
                    status: todayRealRecord.status,
                    hours_worked: todayRealRecord.hours_worked
                };
            }
        
            cursor.setDate(cursor.getDate() + 1);
        }
    
        return map;
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



/* -------------------------- GLOBALS -------------------------- */

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



/* -------------------------- INIT -------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    window.attendanceAI = new AttendancePredictions();
    window.attendanceAI.load();

    window.attendanceManager = new AttendanceManager();
});