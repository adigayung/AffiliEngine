// File: static/js/production_monitor.js
// JavaScript untuk modul Production Monitor

document.addEventListener("DOMContentLoaded", function () {
    // Auto-refresh data setiap 5 menit (300000 ms)
    // Berguna jika halaman dibiarkan terbuka
    const REFRESH_INTERVAL = 300000;
    let refreshTimer = null;

    function initAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
        }
        refreshTimer = setInterval(function () {
            location.reload();
        }, REFRESH_INTERVAL);
    }

    // Inisialisasi auto-refresh
    initAutoRefresh();

    // Tooltip untuk elemen dengan title
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (el) {
        return new bootstrap.Tooltip(el);
    });
});
