document.addEventListener('DOMContentLoaded', function() {
    // Get elements with null checks
    const quizForm = document.getElementById('quizForm');
    const createCurriculumForm = document.getElementById('createCurriculumForm');
    
    // Handle quiz form submission
    if (quizForm) {
        quizForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            const spinner = submitBtn?.querySelector('.spinner-border');
            
            if (submitBtn && spinner) {
                // Show loading state
                submitBtn.disabled = true;
                spinner.classList.remove('d-none');
                submitBtn.textContent = ' Yanıtlar Gönderiliyor...';
                submitBtn.prepend(spinner);
            }
        });
    }
    
    // Handle curriculum form submission
    if (createCurriculumForm) {
        createCurriculumForm.addEventListener('submit', function(e) {
            const submitBtn = document.getElementById('submitBtn');
            const spinner = submitBtn?.querySelector('.spinner-border');
            
            if (submitBtn && spinner) {
                // Show loading state
                submitBtn.disabled = true;
                spinner.classList.remove('d-none');
                submitBtn.textContent = ' Generating Curriculum...';
                submitBtn.prepend(spinner);
            }
        });
    }

    // Initialize tooltips if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});
