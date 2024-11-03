document.addEventListener('DOMContentLoaded', function() {
    // Get chart elements with null checks
    const trendsChartEl = document.getElementById('trendsChart');
    const curriculumChartEl = document.getElementById('curriculumChart');
    const periodButtons = document.querySelectorAll('[data-period]');
    const studentSelect = document.getElementById('student_id');
    
    // Initialize charts if elements exist
    if (trendsChartEl) {
        const trendsCtx = trendsChartEl.getContext('2d');
        const trendsChart = new Chart(trendsCtx, {
            type: 'line',
            data: {
                labels: window.chartData?.recentTrend?.map(item => item.date) || [],
                datasets: [{
                    label: 'Quiz Puanları',
                    data: window.chartData?.recentTrend?.map(item => item.score) || [],
                    borderColor: 'rgb(75, 192, 192)',
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
                                return `Puan: ${context.parsed.y.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });

        // Handle period selection for trends if buttons exist
        if (periodButtons.length > 0) {
            periodButtons.forEach(button => {
                button.addEventListener('click', function() {
                    periodButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                    
                    const studentId = studentSelect?.value || '';
                    const period = this.dataset.period;
                    
                    fetch(`/analytics/performance_trends?period=${period}&student_id=${studentId}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data[period]) {
                                trendsChart.data.labels = data[period].map(item => item.date);
                                trendsChart.data.datasets[0].data = data[period].map(item => item.score);
                                trendsChart.update();
                            }
                        })
                        .catch(error => {
                            console.error('Error fetching performance trends:', error);
                        });
                });
            });
        }
    }
    
    // Initialize curriculum chart if element exists
    if (curriculumChartEl) {
        const curriculumCtx = curriculumChartEl.getContext('2d');
        const curriculumChart = new Chart(curriculumCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(window.chartData?.curriculumPerformance || {}),
                datasets: [{
                    label: 'Ortalama Puan',
                    data: Object.values(window.chartData?.curriculumPerformance || {}).map(item => item.average),
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgb(75, 192, 192)',
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
                            text: 'Ortalama Puan (%)'
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
                                const curriculum = window.chartData?.curriculumPerformance[context.label];
                                return [
                                    `Ortalama: ${context.parsed.y.toFixed(1)}%`,
                                    `Toplam Deneme: ${curriculum?.attempts || 0}`,
                                    `Öğrenci Sayısı: ${curriculum?.student_count || 0}`
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
        studentSelect.addEventListener('change', function() {
            this.form.submit();
        });
    }
});
