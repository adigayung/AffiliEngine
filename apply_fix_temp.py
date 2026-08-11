# -*- coding: utf-8 -*-
"""Patch: Chart 1 kumulatif + perbaiki root cause chart_45_hari Undefined."""
import io


def read(path):
    with io.open(path, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def write(path, content):
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)


def nl_of(path):
    raw = open(path, 'rb').read()
    return '\r\n' if b'\r\n' in raw else '\n'


def apply(path, old, new, label):
    nl = nl_of(path)
    content = read(path)
    old = old.replace('\n', nl)
    new = new.replace('\n', nl)
    n = content.count(old)
    print(f'{label}: occurrences={n}')
    assert n == 1, f'{label} anchor not unique/found ({n})'
    content = content.replace(old, new)
    write(path, content)
    print(f'{label}: OK')


EM = '\u2014'  # em dash

# ============================================================
# 1) includes/production_monitor.py — Chart 1 KUMULATIF
# ============================================================
PM = 'includes/production_monitor.py'

# 1a. Update docstring
apply(PM, '''    1. Grafik 1 ''' + EM + ''' Total Creator per hari:
       Jumlah creator yang terdaftar per hari (creators.created_at).''',
'''    1. Grafik 1 ''' + EM + ''' Total Creator (kumulatif) per hari:
       TOTAL creator yang sudah terdaftar sampai akhir tanggal tersebut
       (jumlah creator dengan created_at <= tanggal), termasuk creator
       yang sudah ada sebelum awal rentang 45 hari.''',
'pm: docstring chart 1')

# 1b. Query: tambah creator_before_start, ganti creator_counts -> daily_new
apply(PM, '''    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1) Total creator per hari (registrasi harian)
            cursor.execute("""
                SELECT DATE(c.created_at) AS tgl, COUNT(*) AS jml
                FROM creators c
                WHERE c.created_at IS NOT NULL
                  AND c.created_at >= %s AND c.created_at < %s
                GROUP BY DATE(c.created_at)
            """, (start_date, end_plus))
            creator_counts = {row["tgl"]: row["jml"] for row in cursor.fetchall()}''',
'''    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1a) Total creator yang SUDAH ADA sebelum start (created_at < start).
            #     Creator lama HARUS tetap dihitung pada setiap tanggal.
            cursor.execute("""
                SELECT COUNT(*) AS cnt
                FROM creators
                WHERE created_at IS NOT NULL
                  AND created_at < %s
            """, (start_date,))
            creator_before_start = int(cursor.fetchone()["cnt"] or 0)

            # 1b) Creator BARU per tanggal dalam range 45 hari
            cursor.execute("""
                SELECT DATE(c.created_at) AS tgl, COUNT(*) AS jml
                FROM creators c
                WHERE c.created_at IS NOT NULL
                  AND c.created_at >= %s AND c.created_at < %s
                GROUP BY DATE(c.created_at)
            """, (start_date, end_plus))
            daily_new = {row["tgl"]: row["jml"] for row in cursor.fetchall()}''',
'pm: query creator_before_start + daily_new')

# 1c. Series kumulatif
apply(PM, '''    # Series total creator (45 nilai, tanggal tanpa data = 0)
    total_creator_series = [int(creator_counts.get(d, 0)) for d in dates]''',
'''    # Series total creator KUMULATIF (45 nilai):
    # total_creator(tanggal) = jumlah creator dengan created_at <= akhir tanggal tsb.
    # Tanggal tanpa creator baru mempertahankan nilai hari sebelumnya.
    total_creator_series = []
    running = creator_before_start
    for d in dates:
        running += int(daily_new.get(d, 0))
        total_creator_series.append(running)''',
'pm: series kumulatif')

# ============================================================
# 2) routers/dashboard/index.py — kirim chart_45_hari
# ============================================================
D = 'routers/dashboard/index.py'

apply(D, '''    get_active_batches,
    get_failed_uploads,
)''',
'''    get_active_batches,
    get_failed_uploads,
    get_creator_analytics_chart,
)''',
'dashboard: import get_creator_analytics_chart')

apply(D, '''    active_batches = get_active_batches()
    failed_uploads = get_failed_uploads()

    return render_template(''',
'''    active_batches = get_active_batches()
    failed_uploads = get_failed_uploads()
    chart_45_hari = get_creator_analytics_chart()

    return render_template(''',
'dashboard: panggil get_creator_analytics_chart')

apply(D, '''        all_creators=all_creators,
        active_batches=active_batches,
        failed_uploads=failed_uploads,
    )''',
'''        all_creators=all_creators,
        active_batches=active_batches,
        failed_uploads=failed_uploads,
        chart_45_hari=chart_45_hari,
    )''',
'dashboard: kirim chart_45_hari ke template')

# ============================================================
# 3) templates/production_monitor/index.html — fallback defensif
# ============================================================
T = 'templates/production_monitor/index.html'

apply(T, '''      var chartData = {{ chart_45_hari | tojson | safe }};''',
'''      var chartData = {{ chart_45_hari | tojson | safe if chart_45_hari is defined else '{}' }};''',
'template: fallback defensif chart_45_hari')

print('ALL EDITS APPLIED')
