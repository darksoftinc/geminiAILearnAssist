document.addEventListener('DOMContentLoaded', function() {
    // Get chart elements with null checks
    const trendsChartEl = document.getElementById('trendsChart');
    const curriculumChartEl = document.getElementById('curriculumChart');
    const periodButtons = document.querySelectorAll('[data-period]');
    const studentSelect = document.getElementById('student_id');
    const chartData = window.chartData || {};
    
    // Initialize trends chart if element exists
    if (trendsChartEl) {
        const trendsCtx = trendsChartEl.getContext('2d');
        const trendsChart = new Chart(trendsCtx, {
            type: 'line',
            data: {
                labels: chartData.recentTrend?.map(item => item.date) || [],
                datasets: [{
                    label: 'Quiz Puanları',
                    data: chartData.recentTrend?.map(item => item.score) || [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false
                }, {
                    label: 'Hareketli Ortalama',
                    data: chartData.recentTrend?.map(item => item.moving_average) || [],
                    borderColor: 'rgb(255, 159, 64)',
                    borderDash: [5, 5],
                    tension: 0.1,
                    fill: false
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
                            text: 'Puan (%)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Tarih'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                return `${label}: ${value.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });

        // Handle period selection for trends if buttons exist
        if (periodButtons && periodButtons.length > 0) {
            periodButtons.forEach(button => {
                if (button) {
                    button.addEventListener('click', function() {
                        if (!this) return;
                        
                        periodButtons.forEach(btn => {
                            if (btn) btn.classList.remove('active');
                        });
                        this.classList.add('active');
                        
                        const studentId = studentSelect?.value || '';
                        const period = this.dataset.period;
                        
                        if (!period) return;
                        
                        fetch(`/analytics/performance_trends?period=${period}&student_id=${studentId}`)
                            .then(response => response.json())
                            .then(data => {
                                if (data[period]) {
                                    // Calculate moving average for the new data
                                    const scores = data[period].map(item => item.score);
                                    const movingAverages = scores.map((_, index) => {
                                        const slice = scores.slice(Math.max(0, index - 2), index + 1);
                                        return slice.reduce((a, b) => a + b, 0) / slice.length;
                                    });

                                    trendsChart.data.labels = data[period].map(item => item.date);
                                    trendsChart.data.datasets[0].data = scores;
                                    trendsChart.data.datasets[1].data = movingAverages;
                                    trendsChart.update();
                                }
                            })
                            .catch(error => {
                                console.error('Error fetching performance trends:', error);
                            });
                    });
                }
            });
        }
    }
    
    // Initialize curriculum chart if element exists
    if (curriculumChartEl) {
        const curriculumCtx = curriculumChartEl.getContext('2d');
        const curriculumData = chartData.curriculumPerformance || {};
        
        const curriculumChart = new Chart(curriculumCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(curriculumData),
                datasets: [{
                    label: 'Ortalama Puan',
                    data: Object.values(curriculumData).map(item => item?.average || 0),
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 1
                }, {
                    label: 'Medyan Puan',
                    data: Object.values(curriculumData).map(item => item?.median || 0),
                    backgroundColor: 'rgba(255, 159, 64, 0.2)',
                    borderColor: 'rgb(255, 159, 64)',
                    borderWidth: 1
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
                            text: 'Puan (%)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const curriculum = curriculumData[context.label] || {};
                                const label = context.dataset.label || '';
                                return [
                                    `${label}: ${context.parsed.y.toFixed(1)}%`,
                                    `Standart Sapma: ${curriculum.std_dev?.toFixed(1) || 0}`,
                                    `Toplam Deneme: ${curriculum.attempts || 0}`,
                                    `Öğrenci Sayısı: ${curriculum.student_count || 0}`,
                                    `Gelişim Oranı: ${curriculum.improvement_rate?.toFixed(1) || 0}%`
                                ];
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Handle student filter changes if select exists
    if (studentSelect) {
        const form = studentSelect.closest('form');
        if (form) {
            studentSelect.addEventListener('change', () => form.submit());
        }
    }
});
