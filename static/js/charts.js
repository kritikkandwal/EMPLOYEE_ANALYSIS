// ✅ Final Chart.js integration — works with UMD build
import { Chart, registerables } from 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/+esm';
Chart.register(...registerables);


class ProductivityCharts {
    constructor() {
        this.charts = {};
        this.init();
    }

    init() {
        this.createProductivityChart();
        this.createFocusChart();
        this.createRadarChart();
    }

    createProductivityChart() {
        const ctx = document.getElementById('productivityChart');
        if (!ctx) return;

        this.charts.productivity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Productivity Score',
                    data: [],
                    borderColor: '#00ffff',
                    backgroundColor: 'rgba(0, 255, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#ffffff' }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#ffffff' }
                    }
                }
            }
        });
    }

    createFocusChart() {
        const ctx = document.getElementById('focusChart');
        if (!ctx) return;

        this.charts.focus = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Focus Time', 'Idle Time', 'Break Time'],
                datasets: [{
                    data: [65, 20, 15],
                    backgroundColor: ['#00ff88', '#ff4444', '#ffaa00'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#ffffff',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    createRadarChart() {
        const ctx = document.getElementById('skillsRadarChart');
        if (!ctx) return;

        this.charts.radar = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Task Efficiency', 'Focus', 'Consistency', 'Collaboration', 'Punctuality'],
                datasets: [
                    {
                        label: 'Current Week',
                        data: [85, 78, 92, 65, 88],
                        backgroundColor: 'rgba(0, 255, 255, 0.2)',
                        borderColor: '#00ffff',
                        borderWidth: 2,
                        pointBackgroundColor: '#00ffff'
                    },
                    {
                        label: 'Last Week',
                        data: [78, 72, 85, 70, 82],
                        backgroundColor: 'rgba(255, 100, 255, 0.2)',
                        borderColor: '#ff64ff',
                        borderWidth: 2,
                        pointBackgroundColor: '#ff64ff'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: { color: '#ffffff', font: { size: 12 } },
                        ticks: { display: false, max: 100 }
                    }
                },
                plugins: { legend: { labels: { color: '#ffffff' } } }
            }
        });
    }

    updateProductivityChart(dates, scores) {
        if (this.charts.productivity) {
            this.charts.productivity.data.labels = dates;
            this.charts.productivity.data.datasets[0].data = scores;
            this.charts.productivity.update();
        }
    }
}

// Advanced prediction functionality
class AdvancedPrediction {
    constructor() {
        this.predictionData = null;
    }

    async loadAdvancedPrediction() {
        try {
            const response = await fetch('/api/advanced-predict/productivity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ days: 7 })
            });

            if (response.ok) {
                const data = await response.json();
                this.predictionData = data;
                this.updatePredictionDisplay(data);
            }
        } catch (error) {
            console.error('Advanced prediction error:', error);
        }
    }

    updatePredictionDisplay(data) {
        // Update prediction score
        const scoreElement = document.getElementById('advancedPredictionScore');
        if (scoreElement) {
            scoreElement.textContent = data.prediction;
            
            // Color code based on score
            if (data.prediction >= 80) {
                scoreElement.style.color = 'var(--accent-glow)';
            } else if (data.prediction >= 60) {
                scoreElement.style.color = '#ffaa00';
            } else {
                scoreElement.style.color = '#ff4444';
            }
        }

        // Update confidence
        const confidenceElement = document.getElementById('confidenceValue');
        if (confidenceElement) {
            confidenceElement.textContent = `${Math.round(data.confidence * 100)}% confidence`;
        }

        // Update model used
        const modelElement = document.getElementById('modelUsed');
        if (modelElement) {
            modelElement.textContent = data.model_used || 'Unknown';
        }

        // Update key factors
        this.updateKeyFactors(data.feature_contributions);
    }

    updateKeyFactors(contributions) {
        const factorsContainer = document.getElementById('keyFactors');
        if (!factorsContainer || !contributions) return;

        // Sort factors by absolute contribution
        const sortedFactors = Object.entries(contributions)
            .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
            .slice(0, 3); // Top 3 factors

        factorsContainer.innerHTML = sortedFactors.map(([factor, value]) => `
            <div class="factor-item">
                <span class="factor-name">${this.formatFactorName(factor)}</span>
                <span class="factor-value ${value > 0 ? 'positive' : 'negative'}">
                    ${value > 0 ? '+' : ''}${value.toFixed(2)}
                </span>
            </div>
        `).join('');
    }

    formatFactorName(factor) {
        const nameMap = {
            'focus_ratio': 'Focus Level',
            'task_completion_rate': 'Task Completion',
            'burnout_risk': 'Burnout Risk',
            'recovery_potential': 'Recovery Potential',
            'consistency_index': 'Consistency',
            'momentum': 'Momentum',
            'rolling_7d_mean': 'Recent Average'
        };
        return nameMap[factor] || factor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
}

// Initialize advanced prediction
document.addEventListener('DOMContentLoaded', function() {
    window.advancedPrediction = new AdvancedPrediction();
    setTimeout(() => {
        window.advancedPrediction.loadAdvancedPrediction();
    }, 1000);
});

// Refresh prediction
async function refreshAdvancedPrediction() {
    const btn = event.target;
    const originalText = btn.innerHTML;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    btn.disabled = true;
    
    await window.advancedPrediction.loadAdvancedPrediction();
    
    setTimeout(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }, 1000);
}

// ✅ Initialize after DOM loads
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        console.log('Initializing charts...');
        window.productivityCharts = new ProductivityCharts();
        loadDashboardData();
    }, 300);
});

// ✅ Data Fetch
async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard-data?days=7');
        const data = await response.json();
        console.log('Dashboard Data Fetched:', data);

        if (window.productivityCharts) {
            window.productivityCharts.updateProductivityChart(data.dates, data.productivity_scores);
        }

        updateProductivityGauge(data.current_score);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function updateProductivityGauge(score) {
    const gauge = document.querySelector('.gauge-fill');
    const scoreText = document.querySelector('.gauge-score');
    if (!gauge || !scoreText) return;

    const degrees = (score / 100) * 180;
    gauge.style.transform = `rotate(${degrees}deg)`;
    scoreText.textContent = Math.round(score);

    if (score >= 80) gauge.style.background = '#00ff88';
    else if (score >= 60) gauge.style.background = '#ffaa00';
    else gauge.style.background = '#ff4444';
}
