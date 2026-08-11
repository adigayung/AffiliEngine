# -*- coding: utf-8 -*-
"""Validasi menyeluruh: Chart 1 kumulatif + root cause Undefined."""
import io
import json
import os
import re
import subprocess
import tempfile
from datetime import date, datetime

# ============================================================
# 0) PY SYNTAX
# ============================================================
import py_compile
for p in ['includes/production_monitor.py',
          'routers/dashboard/index.py',
          'routers/production_monitor/index.py',
          'app.py']:
    py_compile.compile(p, doraise=True)
    print('PY COMPILE OK:', p)

# ============================================================
# 1) UNIT TEST get_creator_analytics_chart — Chart 1 KUMULATIF
#    Contoh dari task:
#      existing sebelum range = 3
#      baru: 28 Jun -> 1, 30 Jun -> 2, 5 Jul -> 1
#      hasil: 28 Jun=4, 29 Jun=4, 30 Jun=6, 1-4 Jul=6, 5 Jul=7, dst
# ============================================================
import includes.production_monitor as pm


class FakeCursor:
    def __init__(self, results):
        self._results = list(results)
        self._i = 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        pass

    def fetchone(self):
        if self._i >= len(self._results):
            return None
        r = self._results[self._i]
        self._i += 1
        return r[0] if r else None

    def fetchall(self):
        if self._i >= len(self._results):
            return []
        r = self._results[self._i]
        self._i += 1
        return r


class FakeConn:
    def __init__(self, results):
        self._results = results

    def cursor(self):
        return FakeCursor(self._results)

    def close(self):
        pass


pm.get_now = lambda: datetime(2026, 8, 11, 10, 0, 0)  # today = 2026-08-11

fake_rows = [
    [{'cnt': 3}],  # creator_before_start
    [  # daily_new
        {'tgl': date(2026, 6, 28), 'jml': 1},
        {'tgl': date(2026, 6, 30), 'jml': 2},
        {'tgl': date(2026, 7, 5), 'jml': 1},
    ],
    [  # view_rows (Chart 2)
        {'creator_id': 1, 'tgl': date(2026, 6, 28), 'total_views': 100},
        {'creator_id': 2, 'tgl': date(2026, 8, 11), 'total_views': 50},
    ],
    [  # creator_rows (Chart 2 legend)
        {'id': 1, 'username': 'a', 'display_name': 'Kang Petruk'},
        {'id': 2, 'username': 'b', 'display_name': 'Mbakyu Rara'},
    ],
]
orig_conn = pm.get_connection
pm.get_connection = lambda: FakeConn(fake_rows)

result = pm.get_creator_analytics_chart()
pm.get_connection = orig_conn  # restore

dates = result['dates']
tc = result['total_creator']
print('--- UNIT TEST CHART 1 ---')
print('len dates:', len(dates))
print('first:', dates[0], '| last:', dates[-1])
print('total_creator:', tc[:10], '...')
assert len(dates) == 45, f'FAIL len={len(dates)}'
assert dates[0] == '2026-06-28', dates[0]
assert dates[-1] == '2026-08-11', dates[-1]
assert len(tc) == 45, f'FAIL tc len={len(tc)}'
# indeks tanggal:
# 2026-06-28 -> idx 0, 2026-06-29 -> 1, 2026-06-30 -> 2,
# 2026-07-05 -> idx 7, 2026-07-06 -> 8
assert tc[0] == 4, tc[0]    # 3 + 1
assert tc[1] == 4, tc[1]    # tidak ada creator baru -> nilai sebelumnya
assert tc[2] == 6, tc[2]    # 4 + 2
assert tc[3] == 6, tc[3]    # 1 Jul
assert tc[4] == 6, tc[4]    # 2 Jul
assert tc[5] == 6, tc[5]    # 3 Jul
assert tc[6] == 6, tc[6]    # 4 Jul
assert tc[7] == 7, tc[7]    # 5 Jul -> 6 + 1
assert tc[8] == 7, tc[8]    # 6 Jul dst
assert tc[44] == 7, tc[44]  # 11 Aug -> 7
# Chart 2 tidak berubah
creators = result['creators']
assert len(creators) == 2
assert creators[0]['name'] == 'Kang Petruk'
assert creators[0]['data'][0] == 100 and creators[0]['data'][1] == 0
assert creators[1]['data'][44] == 50 and creators[1]['data'][0] == 0
print('UNIT TEST: PASS (kumulatif 4,4,6,6,6,6,6,7,...,7; Chart 2 utuh)')

# ============================================================
# 2) JSON SERIALIZATION
# ============================================================
json_str = json.dumps(result)
print('JSON SERIALIZATION: OK, length', len(json_str))
assert json_str.startswith('{')

# ============================================================
# 3) JINJA RENDER — kedua route (dashboard + production_monitor)
# ============================================================
from jinja2 import Environment, FileSystemLoader, ChainableUndefined

env = Environment(loader=FileSystemLoader('templates'), undefined=ChainableUndefined)
env.globals['url_for'] = lambda *a, **k: '/'
env.globals['session'] = {}
env.globals['config'] = {}
env.globals['get_flashed_messages'] = lambda *a, **k: []

creator_sample = {
    'id': 1, 'username': 'kangpetruk', 'display_name': 'Kang Petruk',
    'profile_image': None, 'video_belum_upload': 0, 'video_terjadwal': 0,
    'upload_berikutnya': None, 'jadwal_terakhir': None, 'sisa_hari': 30,
    'upload_gagal': 0, 'status_label': 'AMAN', 'status_color': 'bg-green',
    'priority_score': 0, 'rentang_hari': 0, 'progress_persen': 0, 'avg_view': 0,
}
base_ctx = {
    'page_title': 'Monitor Produksi',
    'summary': {'total_creators': 5, 'total_belum_upload': 0,
                'total_video_terjadwal': 0, 'sisa_hari_global': 30,
                'persediaan_sampai': None},
    'fokus': None,
    'tugas_list': [],
    'tugas_ada_lebih': False,
    'tugas_total_semua': 0,
    'all_creators': [dict(creator_sample)],
    'active_batches': [],
    'failed_uploads': [],
}

# Context dashboard TANPA chart (untuk membuktikan fallback tetap aman)
html_dash_without = env.get_template('production_monitor/index.html').render(**base_ctx)
assert 'Undefined is not JSON serializable' not in html_dash_without
assert 'var chartData = {}' in html_dash_without, 'fallback harus menghasilkan {}'
print('JINJA (dashboard context tanpa chart): OK — fallback {} dipakai')

# Context production monitor DENGAN chart
ctx_pm = dict(base_ctx, chart_45_hari=result)
html_pm = env.get_template('production_monitor/index.html').render(**ctx_pm)
assert 'Undefined is not JSON serializable' not in html_pm
assert '"total_creator": [4, 4, 6' in html_pm
print('JINJA (production monitor context dengan chart): OK')

# ============================================================
# 4) FLASK TEST CLIENT — route / dan /production_monitor/
# ============================================================
import app as app_module
import routers.dashboard.index as dash_mod
import routers.production_monitor.index as pmi_mod

# Fungsi lain di-patch (hindari DB); get_creator_analytics_chart = fungsi ASLI
# dengan koneksi fake agar logika kumulatif benar-benar dieksekusi lewat route.
dash_mod.get_summary = lambda: base_ctx['summary']
dash_mod.get_fokus_hari_ini = lambda: None
dash_mod.get_tugas_hari_ini = lambda: {'tugas': [], 'ada_lebih': False, 'total_semua': 0}
dash_mod.get_creator_status = lambda: [dict(creator_sample)]
dash_mod.get_active_batches = lambda: []
dash_mod.get_failed_uploads = lambda: []
dash_mod.get_creator_analytics_chart = pm.get_creator_analytics_chart

pmi_mod.get_summary = lambda: base_ctx['summary']
pmi_mod.get_fokus_hari_ini = lambda: None
pmi_mod.get_tugas_hari_ini = lambda: {'tugas': [], 'ada_lebih': False, 'total_semua': 0}
pmi_mod.get_creator_status = lambda: [dict(creator_sample)]
pmi_mod.get_active_batches = lambda: []
pmi_mod.get_failed_uploads = lambda: []
pmi_mod.get_creator_analytics_chart = pm.get_creator_analytics_chart

# context processor inject_creator memanggil get_creator_list / get_creator
app_module.get_creator_list = lambda: []
app_module.get_creator = lambda creator_id: None

pm.get_connection = lambda: FakeConn(fake_rows)  # untuk fungsi chart asli
pm.get_now = lambda: datetime(2026, 8, 11, 10, 0, 0)

client = app_module.app.test_client()

for path in ['/', '/production_monitor/']:
    r = client.get(path)
    text = r.get_data(as_text=True)
    print(f'--- ROUTE {path} status={r.status_code} len={len(text)} ---')
    assert r.status_code == 200, f'{path} -> {r.status_code}'
    assert 'Undefined is not JSON serializable' not in text
    assert 'chartTotalCreator' in text and 'chartCreatorViews' in text
    assert '"total_creator": [4, 4, 6' in text, 'nilai kumulatif harus ada di HTML'
    assert '"2026-06-28"' in text and '"2026-08-11"' in text
    # JS syntax
    scripts = re.findall(r'<script>(.*?)</script>', text, re.S)
    for i, js in enumerate(scripts):
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(js)
            tmp = f.name
        rn = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        print(f'  JS block {i}:', 'OK' if rn.returncode == 0 else 'SYNTAX ERROR')
        if rn.returncode != 0:
            print(rn.stderr)
            raise AssertionError('JS SYNTAX FAILED')
        os.unlink(tmp)
    print(f'ROUTE {path}: PASS')

# context existing masih ada? (cek panel/elemen yang dirender dari context)
text_dash = client.get('/').get_data(as_text=True)
for token in ['PANEL 1: FOKUS HARI INI', 'PANEL 2: TUGAS HARI INI',
              'PANEL 3: INFO CEPAT', 'PANEL 4: KONDISI SEMUA CREATOR',
              'PANEL 5: BATCH AKTIF', 'PANEL 6: UPLOAD GAGAL',
              'Total Creator', 'Total Views per Creator']:
    assert token in text_dash, f'missing token: {token}'
print('CONTEXT EXISTING (summary/fokus/tugas/all_creators/active_batches/failed_uploads + charts): OK')

# line endings
for p in ['templates/production_monitor/index.html', 'includes/production_monitor.py',
          'routers/dashboard/index.py']:
    d = open(p, 'rb').read()
    crlf = d.count(b'\r\n'); lf = d.count(b'\n')
    print(p, '| CRLF:', crlf, '| LF-only:', lf - crlf)

print('ALL VALIDATIONS PASS')
