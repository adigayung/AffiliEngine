# -*- coding: utf-8 -*-
"""Coba koneksi DB nyata untuk uji SQL (non-destruktif)."""
import sys
from datetime import date, timedelta

try:
    from includes.config_loader import get_app_config
    cfg = get_app_config()
except Exception as e:
    print('config load FAIL:', type(e).__name__, e)
    sys.exit(0)

try:
    import pymysql
except Exception as e:
    print('pymysql not available:', e)
    sys.exit(0)

host = cfg.get('db_host') or cfg.get('mysql_host') or '127.0.0.1'
port = int(cfg.get('db_port') or cfg.get('mysql_port') or 3306)
user = cfg.get('db_user') or cfg.get('mysql_user') or 'root'
password = cfg.get('db_password') or cfg.get('mysql_password') or ''
db = cfg.get('db_name') or cfg.get('mysql_db') or ''

print('trying DB:', host, port, db)
try:
    conn = pymysql.connect(
        host=host, port=port, user=user, password=password, database=db,
        connect_timeout=4, read_timeout=6, cursorclass=pymysql.cursors.DictCursor,
    )
except Exception as e:
    print('DB CONNECT FAIL:', type(e).__name__, e)
    sys.exit(0)

try:
    with conn.cursor() as cur:
        today = date(2026, 8, 11)
        start = today - timedelta(days=44)
        end_plus = today + timedelta(days=1)

        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM creators
            WHERE created_at IS NOT NULL
              AND created_at < %s
        """, (start,))
        before = cur.fetchone()['cnt']
        print('creator_before_start:', before)

        cur.execute("""
            SELECT DATE(c.created_at) AS tgl, COUNT(*) AS jml
            FROM creators c
            WHERE c.created_at IS NOT NULL
              AND c.created_at >= %s AND c.created_at < %s
            GROUP BY DATE(c.created_at)
        """, (start, end_plus))
        daily = cur.fetchall()
        print('daily_new rows:', len(daily), '->', [(r['tgl'].strftime('%Y-%m-%d'), r['jml']) for r in daily][:5])

        cur.execute("""
            SELECT
                v.creator_id,
                DATE(s.snapshot_time) AS tgl,
                SUM(s.views) AS total_views
            FROM tiktok_video_stats s
            INNER JOIN tiktok_videos v ON s.video_id = v.id
            WHERE s.snapshot_time >= %s AND s.snapshot_time < %s
            GROUP BY v.creator_id, DATE(s.snapshot_time)
        """, (start, end_plus))
        views = cur.fetchall()
        print('views rows:', len(views), '->', [(r['creator_id'], r['tgl'].strftime('%Y-%m-%d'), r['total_views']) for r in views][:5])

        cur.execute("""
            SELECT id, username, display_name
            FROM creators
            WHERE is_active = 1
            ORDER BY id ASC
        """)
        creators = cur.fetchall()
        print('active creators:', len(creators), [c['username'] for c in creators])

        print('DB QUERY TEST: PASS')
    conn.close()
except Exception as e:
    print('DB QUERY TEST FAIL:', type(e).__name__, e)
    import traceback
    traceback.print_exc()
    try:
        conn.close()
    except Exception:
        pass
