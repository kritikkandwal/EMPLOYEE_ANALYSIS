// Chart.js implementations for productivity dashboard
import Chart from 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/+esm';

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
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#ffffff'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#ffffff'
                        }
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
                    backgroundColor: [
                        '#00ff88',
                        '#ff4444',
                        '#ffaa00'
                    ],
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
                            font: {
                                size: 12
                            }
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
                datasets: [{
                    label: 'Current Week',
                    data: [85, 78, 92, 65, 88],
                    backgroundColor: 'rgba(0, 255, 255, 0.2)',
                    borderColor: '#00ffff',
                    borderWidth: 2,
                    pointBackgroundColor: '#00ffff'
                }, {
                    label: 'Last Week',
                    data: [78, 72, 85, 70, 82],
                    backgroundColor: 'rgba(255, 100, 255, 0.2)',
                    borderColor: '#ff64ff',
                    borderWidth: 2,
                    pointBackgroundColor: '#ff64ff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        pointLabels: {
                            color: '#ffffff',
                            font: {
                                size: 12
                            }
                        },
                        ticks: {
                            display: false,
                            max: 100
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    }
                }
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

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.productivityCharts = new ProductivityCharts();
    
    // Load initial data
    loadDashboardData();
});

async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard-data?days=7');
        const data = await response.json();
        
        if (window.productivityCharts) {
            window.productivityCharts.updateProductivityChart(data.dates, data.productivity_scores);
        }
        
        // Update productivity gauge
        updateProductivityGauge(data.current_score);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function updateProductivityGauge(score) {
    const gauge = document.querySelector('.gauge-fill');
    const scoreText = document.querySelector('.gauge-score');
    
    if (gauge && scoreText) {
        const degrees = (score / 100) * 180;
        gauge.style.transform = `rotate(${degrees}deg)`;
        scoreText.textContent = Math.round(score);
        
        // Update color based on score
        if (score >= 80) {
            gauge.style.background = '#00ff88';
        } else if (score >= 60) {
            gauge.style.background = '#ffaa00';
        } else {
            gauge.style.background = '#ff4444';
        }
    }
}