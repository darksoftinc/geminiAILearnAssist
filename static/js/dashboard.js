document.addEventListener('DOMContentLoaded', function() {
    // Null kontrolü ile elementleri al
    const progressChartEl = document.getElementById('progressChart');
    
    // Element varsa ilerleme grafiğini başlat
    if (progressChartEl) {
        const ctx = progressChartEl.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: window.chartData?.dates || [],
                datasets: [{
                    label: 'Quiz Puanları',
                    data: window.chartData?.scores || [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    // Null kontrolü ile form gönderimlerini işle
    const quizForm = document.getElementById('quizForm');
    const createCurriculumForm = document.getElementById('createCurriculumForm');
    
    // Quiz form gönderimini işle
    if (quizForm) {
        quizForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            const spinner = submitBtn?.querySelector('.spinner-border');
            
            if (submitBtn && spinner) {
                // Yükleme durumunu göster
                submitBtn.disabled = true;
                spinner.classList.remove('d-none');
                submitBtn.textContent = ' Yanıtlar Gönderiliyor...';
                submitBtn.prepend(spinner);
            }
        });
    }
    
    // Müfredat form gönderimini işle
    if (createCurriculumForm) {
        createCurriculumForm.addEventListener('submit', function(e) {
            const submitBtn = document.getElementById('submitBtn');
            const spinner = submitBtn?.querySelector('.spinner-border');
            
            if (submitBtn && spinner) {
                // Yükleme durumunu göster
                submitBtn.disabled = true;
                spinner.classList.remove('d-none');
                submitBtn.textContent = ' Müfredat Oluşturuluyor...';
                submitBtn.prepend(spinner);
            }
        });
    }

    // Bootstrap yüklü ise ipuçlarını başlat
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
