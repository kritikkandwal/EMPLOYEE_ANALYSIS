// ✅ Complete Chart.js Integration - ESM Architecture
import { Chart, registerables } from 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/+esm';
import { format, parseISO } from 'https://cdn.jsdelivr.net/npm/date-fns/+esm';

// Register Chart.js and plugins
Chart.register(...registerables);

if (window.dashboard) {
    Object.values(window.dashboard.charts || {}).forEach(c => c.destroy());
    window.dashboard = null;
}


class HRDashboardCharts {
    constructor() {
        this.charts = {};
        this.dashboardData = null;
        this.isInitialized = false;
    }

    async initialize() {
        try {
            // 1️⃣ Create empty charts FIRST
            await this.createAllCharts();
        
            // 2️⃣ THEN load data & populate them
            await this.loadDashboardData();
        
            console.log('✅ Dashboard charts initialized successfully');
        } catch (error) {
            console.error('❌ Dashboard initialization failed:', error);
        }
    }


    createAllCharts() {
        return Promise.all([
            this.createAttendanceCalendar(),
            this.createAttendanceConsistency(),
            this.createHoursTrend(),
            this.createProductivityTrend(),
            this.createTaskCompletion(),
            this.createCorrelationChart(),
            this.createWeeklyInsights()
        ]);
    }

    // 1. Attendance Calendar View
    createAttendanceCalendar() {
        return new Promise((resolve) => {
            const ctx = document.getElementById('attendanceCalendar');
            if (!ctx) {
                console.warn('Attendance calendar canvas not found');
                resolve();
                return;
            }

            this.charts.attendanceCalendar = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Attendance',
                        data: [],
                        backgroundColor: [],
                        borderWidth: 0,
                        borderRadius: 4,
                        barPercentage: 0.8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                title: (items) => {
                                    const date = items[0].label;
                                    return `Date: ${date}`;
                                },
                                label: (context) => {
                                    const isPresent = context.raw > 0;
                                    return `Status: ${isPresent ? 'Present' : 'Absent'}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            },
                            grid: { display: false }
                        },
                        y: {
                            display: false
                        }
                    }
                }
            });
            resolve();
        });
    }

    // 2. Attendance Consistency Trend
    createAttendanceConsistency() {
        return new Promise((resolve) => {
            const ctx = document.getElementById('attendanceConsistency');
            if (!ctx) {
                console.warn('Attendance consistency canvas not found');
                resolve();
                return;
            }

            this.charts.attendanceConsistency = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '7-Day Rolling Average',
                        data: [],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.3,
                        pointBackgroundColor: '#3498db',
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    return `Consistency: ${context.raw}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Attendance %'
                            },
                            ticks: {
                                callback: (value) => `${value}%`
                            }
                        },
                        x: {
                            ticks: {
                                maxTicksLimit: 8
                            }
                        }
                    }
                }
            });
            resolve();
        });
    }

    // 3. Hours Worked Trend
    createHoursTrend() {
        return new Promise((resolve) => {
            const ctx = document.getElementById('hoursTrend');
            if (!ctx) {
                console.warn('Hours trend canvas not found');
                resolve();
                return;
            }

            this.charts.hoursTrend = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Hours Worked',
                        data: [],
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.15)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Hours'
                            }
                        },
                        x: {
                            ticks: {
                                maxTicksLimit: 8
                            }
                        }
                    }
                }
            });
            resolve();
        });
    }

    // 4. Productivity Score Trend
    createProductivityTrend() {
        return new Promise((resolve) => {
            const ctx = document.getElementById('productivityTrend');
            if (!ctx) {
                console.warn('Productivity trend canvas not found');
                resolve();
                return;
            }

            this.charts.productivityTrend = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Productivity Score',
                        data: [],
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.3,
                        pointBackgroundColor: '#2ecc71',
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Score'
                            }
                        },
                        x: {
                            ticks: {
                                maxTicksLimit: 8
                            }
                        }
                    }
                }
            });
            resolve();
        });
    }

    // 5. Task Completion Ratio
    createTaskCompletion() {
        return new Promise((resolve) => {
            const ctx = document.getElementById('taskCompletion');
            if (!ctx) {
                console.warn('Task completion canvas not found');
                resolve();
                return;
            }

            this.charts.taskCompletion = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Completion Ratio (%)',
                        data: [],
                        backgroundColor: 'rgba(243, 156, 18, 0.7)',
                        borderColor: '#f39c12',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Completion %'
                            },
                            ticks: {
                                callback: (value) => `${value}%`
                            }
                        },
                        x: {
                            ticks: {
                                maxTicksLimit: 8
                            }
                        }
                    }
                }
            });
            resolve();
        });
    }

    // 6. Correlation Chart
    createCorrelationChart() {
        return new Promise((resolve) => {
            const ctx = document.getElementById('correlationChart');
            if (!ctx) {
                console.warn('Correlation chart canvas not found');
                resolve();
                return;
            }

            this.charts.correlationChart = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Hours vs Productivity',
                        data: [],
                        backgroundColor: 'rgba(52, 152, 219, 0.7)',
                        borderColor: '#3498db',
                        borderWidth: 1,
                        pointRadius: 6,
                        pointHoverRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    return [
                                        `Hours: ${context.parsed.x}`,
                                        `Score: ${context.parsed.y}`,
                                        `Date: ${context.label || 'Unknown'}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Hours Worked'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Productivity Score'
                            }
                        }
                    }
                }
            });
            resolve();
        });
    }

    // 7. Weekly Insights
    createWeeklyInsights() {
        return new Promise((resolve) => {
            const ctx = document.getElementById('weeklyInsights');
            if (!ctx) {
                console.warn('Weekly insights canvas not found');
                resolve();
                return;
            }

            this.charts.weeklyInsights = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Avg Hours',
                            data: [],
                            backgroundColor: 'rgba(231, 76, 60, 0.7)',
                            borderColor: '#e74c3c',
                            borderWidth: 1,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Avg Score',
                            data: [],
                            backgroundColor: 'rgba(46, 204, 113, 0.7)',
                            borderColor: '#2ecc71',
                            borderWidth: 2,
                            type: 'line',
                            yAxisID: 'y1',
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Hours'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Score'
                            },
                            grid: {
                                drawOnChartArea: false
                            }
                        }
                    }
                }
            });
            resolve();
        });
    }

    // Update all charts with data
    updateAllCharts(data) {
        this.dashboardData = data;
        
        // 1. Update Attendance Calendar
        if (this.charts.attendanceCalendar && data.attendanceCalendar) {
            const calendarData = data.attendanceCalendar.slice(-30);
            this.charts.attendanceCalendar.data.labels = calendarData.map(d => 
                format(parseISO(d.date), 'MMM dd')
            );
            this.charts.attendanceCalendar.data.datasets[0].data = calendarData.map(d => d.attendance);
            this.charts.attendanceCalendar.data.datasets[0].backgroundColor = calendarData.map(d => 
                d.attendance ? '#2ecc71' : '#e74c3c'
            );
            this.charts.attendanceCalendar.update('none');
        }

        // 2. Update Attendance Consistency
        if (this.charts.attendanceConsistency && data.attendanceConsistency) {
            const consistencyData = data.attendanceConsistency;
            this.charts.attendanceConsistency.data.labels = consistencyData.map(d => 
                format(parseISO(d.date), 'MMM dd')
            );
            this.charts.attendanceConsistency.data.datasets[0].data = consistencyData.map(d => 
                (d.attendance_7day_avg * 100).toFixed(1)
            );
            this.charts.attendanceConsistency.update('none');
        }

        // 3. Update Hours Trend
        if (this.charts.hoursTrend && data.hoursTrend) {
            this.charts.hoursTrend.data.labels = data.hoursTrend.map(d => 
                format(parseISO(d.date), 'MMM dd')
            );
            this.charts.hoursTrend.data.datasets[0].data = data.hoursTrend.map(d => d.hours);
            this.charts.hoursTrend.update('none');
        }

        // 4. Update Productivity Trend
        if (this.charts.productivityTrend && data.productivityTrend) {
            this.charts.productivityTrend.data.labels = data.productivityTrend.map(d => 
                format(parseISO(d.date), 'MMM dd')
            );
            this.charts.productivityTrend.data.datasets[0].data = data.productivityTrend.map(d => d.score);
            this.charts.productivityTrend.update('none');
        }

        // 5. Update Task Completion
        if (this.charts.taskCompletion && data.taskCompletion) {
            this.charts.taskCompletion.data.labels = data.taskCompletion.map(d => 
                format(parseISO(d.date), 'MMM dd')
            );
            this.charts.taskCompletion.data.datasets[0].data = data.taskCompletion.map(d => 
                d.ratio.toFixed(1)
            );
            this.charts.taskCompletion.update('none');
        }

        // 6. Update Correlation Chart
        if (this.charts.correlationChart && data.correlation) {
            const correlationData = data.correlation.map(d => ({
                x: d.hours,
                y: d.score
            }));
            
            const correlation = this.calculateCorrelation(
                data.correlation.map(d => d.hours),
                data.correlation.map(d => d.score)
            );
            
            this.charts.correlationChart.data.datasets[0].data = correlationData;
            this.charts.correlationChart.data.datasets[0].label = `Correlation: r = ${correlation.toFixed(2)}`;
            this.charts.correlationChart.update('none');
            
            // Update insight text
            this.updateCorrelationInsight(correlation);
        }

        // 7. Update Weekly Insights
        if (this.charts.weeklyInsights && data.weeklyInsights) {
            this.charts.weeklyInsights.data.labels = data.weeklyInsights.map(d => d.week);
            this.charts.weeklyInsights.data.datasets[0].data = data.weeklyInsights.map(d => d.avg_hours);
            this.charts.weeklyInsights.data.datasets[1].data = data.weeklyInsights.map(d => d.avg_score);
            this.charts.weeklyInsights.update('none');
        }

        // Update KPI cards
        this.updateKPICards(data.kpi);
        
        // Update data timestamp
        this.updateDataTimestamp();
    }

    calculateCorrelation(x, y) {
        if (x.length !== y.length || x.length === 0) return 0;
        
        const n = x.length;
        const sumX = x.reduce((a, b) => a + b, 0);
        const sumY = y.reduce((a, b) => a + b, 0);
        const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
        const sumX2 = x.reduce((sum, xi) => sum + xi * xi, 0);
        const sumY2 = y.reduce((sum, yi) => sum + yi * yi, 0);
        
        const numerator = n * sumXY - sumX * sumY;
        const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
        
        return denominator === 0 ? 0 : numerator / denominator;
    }

    updateCorrelationInsight(correlation) {
        const insightElement = document.getElementById('correlationInsightText');
        if (!insightElement) return;
        
        let insight = '';
        if (correlation > 0.5) {
            insight = `Strong positive correlation (r = ${correlation.toFixed(2)}). Longer hours are associated with higher productivity.`;
        } else if (correlation > 0.2) {
            insight = `Moderate positive correlation (r = ${correlation.toFixed(2)}). Generally, more hours lead to better productivity.`;
        } else if (correlation > -0.2) {
            insight = `Weak correlation (r = ${correlation.toFixed(2)}). Productivity is not strongly related to hours worked.`;
        } else if (correlation > -0.5) {
            insight = `Moderate negative correlation (r = ${correlation.toFixed(2)}). Longer hours may be associated with lower productivity.`;
        } else {
            insight = `Strong negative correlation (r = ${correlation.toFixed(2)}). There may be burnout or inefficiency with longer hours.`;
        }
        
        insightElement.textContent = insight;
    }

    updateKPICards(kpiData) {
        if (!kpiData) return;
        
        const updateElement = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };
        
        updateElement('kpi-attendance', `${kpiData.attendance_rate}%`);
        updateElement('kpi-productivity', kpiData.productivity_avg.toFixed(1));
        updateElement('kpi-completion', `${kpiData.completion_ratio.toFixed(1)}%`);
        updateElement('kpi-hours', kpiData.total_hours);
        updateElement('kpi-outlook', kpiData.productivity_outlook);
        
        // Style outlook indicator
        const outlookIndicator = document.getElementById('outlook-indicator');
        if (outlookIndicator) {
            outlookIndicator.textContent = kpiData.productivity_outlook;
            outlookIndicator.style.backgroundColor = `${kpiData.outlook_color}20`;
            outlookIndicator.style.color = kpiData.outlook_color;
        }
    }

    updateDataTimestamp() {
        const dateElement = document.getElementById('data-update-date');
        if (dateElement) {
            dateElement.textContent = format(new Date(), 'MMM dd, yyyy HH:mm');
        }
    }

    async loadDashboardData() {
        try {
            const response = await fetch('/api/dashboard-data');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.updateAllCharts(data);
            
            console.log('✅ Dashboard data loaded successfully');
        } catch (error) {
            console.error('❌ Failed to load dashboard data:', error);
            
            // Show error to user
            const errorElement = document.getElementById('dashboard-error');
            if (errorElement) {
                errorElement.textContent = 'Failed to load data. Please refresh.';
                errorElement.style.display = 'block';
            }
        }
    }

    // Public method to refresh all charts
    async refresh() {
        await this.loadDashboardData();
    }
}

// Advanced Prediction Integration
class AdvancedPrediction {
    constructor() {
        this.predictionData = null;
    }

    async loadPrediction() {
        try {
            const response = await fetch('/predict-productivity')
            if (response.ok) {
                this.predictionData = await response.json();
                this.updatePredictionDisplay();
            }
        } catch (error) {
            console.warn('Prediction service unavailable:', error);
        }
    }

    updatePredictionDisplay() {
        if (!this.predictionData) return;
        
        // Update prediction elements if they exist
        const scoreElement = document.getElementById('predictionScore');
        if (scoreElement && this.predictionData.score) {
            scoreElement.textContent = this.predictionData.score.toFixed(1);
            
            if (this.predictionData.score >= 80) {
                scoreElement.style.color = '#2ecc71';
            } else if (this.predictionData.score >= 60) {
                scoreElement.style.color = '#f39c12';
            } else {
                scoreElement.style.color = '#e74c3c';
            }
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Initializing HR Dashboard...');
    
    // Initialize dashboard charts
    window.dashboard = new HRDashboardCharts();
    await window.dashboard.initialize();
    
    // Initialize prediction
    window.prediction = new AdvancedPrediction();
    // await window.prediction.loadPrediction();
    
    // Set current date
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        dateElement.textContent = format(new Date(), 'EEEE, MMMM dd, yyyy');
    }
    
    // Add formula tooltip listeners
    document.querySelectorAll('.formula-tooltip').forEach(tooltip => {
        tooltip.addEventListener('click', function() {
            const formula = this.getAttribute('data-formula');
            showFormulaModal(formula);
        });
    });
    
    // Auto-refresh every 5 minutes
    setInterval(() => {
        window.dashboard.refresh();
    }, 300000);
    
    console.log('✅ HR Dashboard initialization complete');
});

// Formula modal functions (kept separate for clarity)
function showFormulaModal(formula) {
    const modal = document.getElementById('formulaModal');
    const details = document.getElementById('formulaDetails');
    if (modal && details) {
        details.innerHTML = `
            <div class="formula-detail">
                <h4><i class="fas fa-calculator"></i> Formula Definition</h4>
                <div class="formula-text">${formula}</div>
                <div class="formula-note">
                    <i class="fas fa-info-circle"></i> Based on industry-standard HR analytics methodology
                </div>
            </div>
        `;
        modal.style.display = 'flex';
    }
}

function closeFormulaModal() {
    const modal = document.getElementById('formulaModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Export for potential module use
export { HRDashboardCharts, AdvancedPrediction };