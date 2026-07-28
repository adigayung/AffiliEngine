/**
 * Product Radar Chart
 * 
 * Menampilkan radar chart profil kualitas produk pada halaman detail produk.
 * Data dinormalisasi ke skala 0-100 berdasarkan TARGET BISNIS (bukan angka maksimum):
 *   1. Peluang      (pesanan / jumlah_kreator) → cap di 20/creator
 *   2. CTR          (ctr)                      → cap di 10%
 *   3. Komisi       (komisi)                   → cap di Rp10.000
 *   4. Rating       (rating)                   → linear (5 = 100)
 *   5. Penjualan    (pesanan)                  → log10, cap di 10.000 (log10=4)
 *   6. Keranjang    (pembeli_keranjang)         → log10, cap di 10.000 (log10=4)
 * 
 * Chart.js v4.4.7 (CDN) - library yang sudah digunakan project.
 */

/* global Chart */

// ================================================================
// NORMALISASI BERDASARKAN TARGET BISNIS
// ================================================================

const NORMALIZERS = {
    /**
     * 1. Peluang = pesanan / jumlah_kreator
     *    Target: rasio 20 sudah sangat bagus.
     *    score = MIN((ratio / 20) * 100, 100)
     */
    peluang: function (pesanan, jumlahKreator) {
        if (!jumlahKreator || jumlahKreator <= 0) return 0;
        if (!pesanan) return 0;
        var ratio = pesanan / jumlahKreator;
        if (ratio <= 0) return 0;
        // Non-linear power function: score = 20 * ratio^1.2
        // 0->0, 1->20, 2->46, 3->75, 4->100, 5+->100
        return Math.min(Math.round(20 * Math.pow(ratio, 1.2)), 100);
    },

    /**
     * 2. CTR - percentage
     *    Target: 10% sudah sangat bagus.
     *    score = MIN((ctr / 10) * 100, 100)
     */
    ctr: function (value) {
        var num = parseFloat(value) || 0;
        return Math.min(Math.round((num / 10) * 100), 100);
    },

    /**
     * 3. Komisi - Rupiah
     *    Target: Rp10.000 sudah sangat bagus.
     *    score = MIN((komisi / 10000) * 100, 100)
     */
    komisi: function (value) {
        var num = parseInt(value, 10) || 0;
        return Math.min(Math.round((num / 10000) * 100), 100);
    },

    /**
     * 4. Rating - skala 1-5
     *    score = (rating / 5) * 100
     */
    rating: function (value) {
        var num = parseFloat(value) || 0;
        return Math.min(Math.round((num / 5) * 100), 100);
    },

    /**
     * 5. Penjualan (pesanan) - LOGARITMA
     *    Agar produk besar tidak mendominasi.
     *    score = MIN(LOG10(pesanan+1) / 4 * 100, 100)
     *    log10(1)=0, log10(10)=1, log10(100)=2, log10(1000)=3, log10(10000)=4
     */
    penjualan: function (value) {
        var num = parseInt(value, 10) || 0;
        var logVal = Math.log10(num + 1);
        return Math.min(Math.round((logVal / 4) * 100), 100);
    },

    /**
     * 6. Keranjang (pembeli_keranjang) - LOGARITMA
     *    score = MIN(LOG10(pembeli_keranjang+1) / 4 * 100, 100)
     */
    keranjang: function (value) {
        var num = parseInt(value, 10) || 0;
        var logVal = Math.log10(num + 1);
        return Math.min(Math.round((logVal / 4) * 100), 100);
    },
};


// ================================================================
// FORMATTER NILAI ASLI (untuk tooltip & tabel)
// ================================================================

function getIndicatorData(product) {
    var peluangRatio = 0;
    if (product.jumlah_kreator && product.jumlah_kreator > 0 && product.pesanan) {
        peluangRatio = (product.pesanan || 0) / product.jumlah_kreator;
    }

    return [
        {
            key: "peluang",
            label: "Peluang",
            nilaiAsli: peluangRatio.toFixed(1) + " per creator",
            skor: NORMALIZERS.peluang(product.pesanan, product.jumlah_kreator),
        },
        {
            key: "ctr",
            label: "CTR",
            nilaiAsli: (product.ctr || 0) + "%",
            skor: NORMALIZERS.ctr(product.ctr),
        },
        {
            key: "komisi",
            label: "Komisi",
            nilaiAsli: "Rp " + ((product.komisi || 0)).toLocaleString("id-ID"),
            skor: NORMALIZERS.komisi(product.komisi),
        },
        {
            key: "rating",
            label: "Rating",
            nilaiAsli: (product.rating || 0) + " / 5",
            skor: NORMALIZERS.rating(product.rating),
        },
        {
            key: "penjualan",
            label: "Penjualan",
            nilaiAsli: (product.pesanan || 0).toLocaleString("id-ID") + " pesanan",
            skor: NORMALIZERS.penjualan(product.pesanan),
        },
        {
            key: "keranjang",
            label: "Keranjang",
            nilaiAsli: (product.pembeli_keranjang || 0).toLocaleString("id-ID") + " pembeli",
            skor: NORMALIZERS.keranjang(product.pembeli_keranjang),
        },
    ];
}


// ================================================================
// BUILD RADAR CHART
// ================================================================

function buildProductRadar(canvasId, productData) {
    if (!canvasId || !productData) return null;

    var canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    // Hitung data indikator
    var items = getIndicatorData(productData);
    var labels = items.map(function (i) { return i.label; });
    var data = items.map(function (i) { return i.skor; });

    var ctx = canvas.getContext("2d");

    var chart = new Chart(ctx, {
        type: "radar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Skor (0-100)",
                    data: data,
                    backgroundColor: "rgba(32, 107, 196, 0.20)",
                    borderColor: "rgba(32, 107, 196, 0.9)",
                    borderWidth: 3,
                    pointBackgroundColor: "rgba(32, 107, 196, 1)",
                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 1,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: "rgba(0, 0, 0, 0.88)",
                    titleColor: "#ffffff",
                    bodyColor: "#ffffff",
                    borderColor: "rgba(255,255,255,0.15)",
                    borderWidth: 1,
                    titleFont: {
                        size: 15,
                        weight: "bold",
                    },
                    bodyFont: {
                        size: 14,
                    },
                    padding: 14,
                    cornerRadius: 8,
                    callbacks: {
                        title: function (tooltipItems) {
                            return tooltipItems[0].label;
                        },
                        label: function (context) {
                            var idx = context.dataIndex;
                            var item = items[idx];
                            if (!item) return "";
                            return [
                                item.nilaiAsli,
                                "Skor : " + item.skor,
                            ];
                        },
                    },
                },
            },
            scales: {
                r: {
                    min: 0,
                    max: 100,
                    beginAtZero: true,
                    ticks: {
                        stepSize: 20,
                        color: "#6c7a91",
                        backdropColor: "transparent",
                        font: {
                            size: 16,
                            weight: "600",
                        },
                    },
                    grid: {
                        color: "rgba(108, 122, 145, 0.30)",
                        circular: true,
                    },
                    angleLines: {
                        color: "rgba(108, 122, 145, 0.30)",
                    },
                    pointLabels: {
                        color: "#232e3c",
                        font: {
                            size: 20,
                            weight: "700",
                        },
                        padding: 6,
                    },
                },
            },
        },
    });

    return chart;
}


// ================================================================
// TABEL SKOR DI BAWAH RADAR
// ================================================================

function populateScoreTable(productData) {
    var container = document.getElementById("radarScoreTable");
    if (!container) return;

    var items = getIndicatorData(productData);
    var rowsHtml = "";

    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        // Warna skor berdasarkan nilai
        var colorClass = "";
        if (item.skor >= 80) colorClass = "text-green";
        else if (item.skor >= 50) colorClass = "text-blue";
        else if (item.skor >= 30) colorClass = "text-yellow";
        else colorClass = "text-danger";

        rowsHtml +=
            "<tr>" +
            "<td class=\"text-nowrap fs-6\">" + item.label + "</td>" +
            "<td class=\"text-secondary fs-6\">" + item.nilaiAsli + "</td>" +
            "<td class=\"text-end fw-bold fs-6 " + colorClass + "\">" + item.skor + "</td>" +
            "</tr>";
    }

    container.innerHTML =
        '<div class="table-responsive mt-3">' +
        '<table class="table table-sm table-borderless mb-0" style="font-size:0.85rem;">' +
        '<thead>' +
        '<tr class="text-muted border-bottom">' +
        '<th class="fw-semibold fs-6">Indikator</th>' +
        '<th class="fw-semibold fs-6">Nilai Asli</th>' +
        '<th class="fw-semibold text-end fs-6">Skor</th>' +
        '</tr>' +
        '</thead>' +
        '<tbody>' + rowsHtml + '</tbody>' +
        '</table>' +
        '</div>';
}


// ================================================================
// MODAL ZOOM
// ================================================================

function openRadarModal(productData) {
    var modalEl = document.getElementById("radarZoomModal");
    if (!modalEl) {
        modalEl = document.createElement("div");
        modalEl.id = "radarZoomModal";
        modalEl.className = "modal modal-blur fade";
        modalEl.tabIndex = -1;
        modalEl.setAttribute("aria-hidden", "true");
        modalEl.setAttribute("data-bs-backdrop", "static");
        modalEl.innerHTML = [
            '<div class="modal-dialog modal-dialog-centered modal-xl" style="max-width: 80vw;">',
            '  <div class="modal-content">',
            '    <div class="modal-header border-0 pb-0">',
            '      <h5 class="modal-title fs-4 fw-bold">Product Radar</h5>',
            '      <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>',
            '    </div>',
            '    <div class="modal-body text-center pt-0">',
            '      <div class="radar-modal-wrapper" style="position:relative;width:100%;max-width:600px;margin:0 auto;">',
            '        <canvas id="radarZoomCanvas"></canvas>',
            '      </div>',
            '      <div id="radarZoomScoreTable"></div>',
            '    </div>',
            '    <div class="modal-footer border-0 justify-content-center pt-0">',
            '      <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">',
            '        <i class="ti ti-x me-2"></i>Tutup',
            '      </button>',
            '    </div>',
            '  </div>',
            '</div>',
        ].join("");
        document.body.appendChild(modalEl);
    }

    var existingChart = Chart.getChart("radarZoomCanvas");
    if (existingChart) {
        existingChart.destroy();
    }

    buildProductRadar("radarZoomCanvas", productData);
    populateScoreTableForModal(productData);

    var modal = new bootstrap.Modal(modalEl, {
        backdrop: true,
        keyboard: true,
    });
    modal.show();
}

function populateScoreTableForModal(productData) {
    var container = document.getElementById("radarZoomScoreTable");
    if (!container) return;

    var items = getIndicatorData(productData);
    var rowsHtml = "";

    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        var colorClass = "";
        if (item.skor >= 80) colorClass = "text-green";
        else if (item.skor >= 50) colorClass = "text-blue";
        else if (item.skor >= 30) colorClass = "text-yellow";
        else colorClass = "text-danger";

        rowsHtml +=
            "<tr>" +
            "<td class=\"text-nowrap fs-6\">" + item.label + "</td>" +
            "<td class=\"text-secondary fs-6\">" + item.nilaiAsli + "</td>" +
            "<td class=\"text-end fw-bold fs-6 " + colorClass + "\">" + item.skor + "</td>" +
            "</tr>";
    }

    container.innerHTML =
        '<div class="table-responsive" style="max-width:500px;margin:0 auto;">' +
        '<table class="table table-sm table-borderless mb-0" style="font-size:0.9rem;">' +
        '<thead>' +
        '<tr class="text-muted border-bottom">' +
        '<th class="fw-semibold fs-6">Indikator</th>' +
        '<th class="fw-semibold fs-6">Nilai Asli</th>' +
        '<th class="fw-semibold text-end fs-6">Skor</th>' +
        '</tr>' +
        '</thead>' +
        '<tbody>' + rowsHtml + '</tbody>' +
        '</table>' +
        '</div>';
}


// ================================================================
// INITIALISASI
// ================================================================

function initProductRadar(productData) {
    if (!productData) return;

    // Build radar di halaman
    buildProductRadar("productRadar", productData);

    // Isi tabel skor
    populateScoreTable(productData);

    // Klik radar → buka modal zoom
    var canvas = document.getElementById("productRadar");
    if (canvas) {
        canvas.style.cursor = "pointer";
        canvas.addEventListener("click", function () {
            openRadarModal(productData);
        });
    }
}

