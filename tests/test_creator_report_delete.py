"""
Test untuk fitur hapus (delete) product berstatus 'scheduled' pada halaman
/creator/<creator_id>/report.

Fokus:
- Product 'scheduled' dapat dihapus (record DB terhapus).
- Penghapusan 'scheduled' TIDAK PERNAH menyentuh file/folder di storage.
- Perilaku hapus 'pending' TIDAK berubah (regression guard).

File ini menggunakan fake connection (tanpa MySQL asli) dengan
monkeypatching `routers.creator.report.get_connection`.

Jalankan:
    python -m unittest discover -s tests -v
"""

import datetime
import os
import tempfile
import unittest

from flask import Flask

import routers.creator.report as report


# ==============================================================
# FAKE DATABASE
# ==============================================================
class FakeCursor:
    def __init__(self, store):
        self.store = store
        self._rows = []
        self._single = None

    def execute(self, sql, params=None):
        norm = " ".join(sql.split())
        self.store["calls"].append((norm, params))

        if norm.startswith("SELECT id, batch_id, status"):
            creator_id = params[0]
            ids = set(params[1:])
            self._rows = [
                dict(j)
                for j in self.store["jobs"]
                if j["creator_id"] == creator_id and j["id"] in ids
            ]
        elif norm.startswith("SELECT id, folder, status, schedule_datetime"):
            job_id, creator_id = params
            match = [
                dict(j)
                for j in self.store["jobs"]
                if j["id"] == job_id and j["creator_id"] == creator_id
            ]
            self._single = match[0] if match else None
        elif norm.startswith("DELETE FROM upload_jobs"):
            creator_id = params[0]
            if "status = 'pending'" in norm:
                ids = set(params[1:])
                self.store["jobs"] = [
                    j
                    for j in self.store["jobs"]
                    if not (
                        j["creator_id"] == creator_id
                        and j["status"] == "pending"
                        and j["id"] in ids
                    )
                ]
            elif "status = 'uploaded'" in norm and "schedule_datetime > %s" in norm:
                now = params[1]
                ids = set(params[2:])
                self.store["jobs"] = [
                    j
                    for j in self.store["jobs"]
                    if not (
                        j["creator_id"] == creator_id
                        and j["status"] == "uploaded"
                        and j["schedule_datetime"] > now
                        and j["id"] in ids
                    )
                ]
            else:
                raise AssertionError("Unexpected DELETE: " + norm)
        elif norm.startswith("SELECT COUNT(*) AS cnt FROM upload_jobs WHERE batch_id"):
            batch_id = params[0]
            self._single = {
                "cnt": sum(
                    1 for j in self.store["jobs"] if j.get("batch_id") == batch_id
                )
            }
        elif norm.startswith("DELETE FROM schedule_batches"):
            self.store["deleted_batches"].append(params[0])
        else:
            raise AssertionError("Unexpected SQL: " + norm)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._single

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConnection:
    def __init__(self, store):
        self.store = store

    def cursor(self):
        return FakeCursor(self.store)

    def commit(self):
        self.store["commits"] += 1

    def rollback(self):
        self.store["rollbacks"] += 1

    def close(self):
        pass


class FakeShutil:
    """Shutil palsu: HANYA mencatat pemanggilan rmtree (tidak menghapus)."""

    def __init__(self):
        self.rmtree_calls = []

    def rmtree(self, path):
        self.rmtree_calls.append(path)


def _client():
    app = Flask(__name__)
    app.register_blueprint(report.creator_report_bp)
    return app.test_client()


class ReportDeleteTestCase(unittest.TestCase):
    def setUp(self):
        self.store = {
            "jobs": [],
            "deleted_batches": [],
            "calls": [],
            "commits": 0,
            "rollbacks": 0,
        }
        self.fake_shutil = FakeShutil()

        self._orig_conn = report.get_connection
        self._orig_shutil = report.shutil
        self._orig_delete_upload_job = report.delete_upload_job

        report.get_connection = lambda: FakeConnection(self.store)
        report.shutil = self.fake_shutil
        report.delete_upload_job = self._fake_delete_upload_job

    def tearDown(self):
        report.get_connection = self._orig_conn
        report.shutil = self._orig_shutil
        report.delete_upload_job = self._orig_delete_upload_job

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _fake_delete_upload_job(self, job_id):
        before = len(self.store["jobs"])
        self.store["jobs"] = [j for j in self.store["jobs"] if j["id"] != job_id]
        return len(self.store["jobs"]) < before

    def _make_schedule_dir(self, tmp):
        parent = os.path.join(tmp, "2024_01_01_10_00")
        child = os.path.join(parent, "2024_01_01_10_30")
        os.makedirs(child)
        return child

    # ------------------------------------------------------------------
    # unit: definisi status scheduled
    # ------------------------------------------------------------------
    def test_compute_display_status_definition(self):
        now = datetime.datetime.now()
        future = now + datetime.timedelta(days=1)
        past = now - datetime.timedelta(days=1)

        self.assertEqual(
            report._compute_display_status("uploaded", future, now), "scheduled"
        )
        self.assertEqual(
            report._compute_display_status("uploaded", past, now), "uploaded"
        )
        self.assertEqual(
            report._compute_display_status("pending", future, now), "pending"
        )

    def test_parse_datetime_variants(self):
        dt = datetime.datetime(2024, 5, 6, 7, 8, 9)
        self.assertEqual(report._parse_datetime(dt), dt)
        self.assertEqual(
            report._parse_datetime("2024-05-06 07:08:09"), dt
        )
        self.assertIsNone(report._parse_datetime(None))
        self.assertIsNone(report._parse_datetime("bukan-tanggal"))

    # ------------------------------------------------------------------
    # helper backend: scheduled
    # ------------------------------------------------------------------
    def test_bulk_delete_scheduled_only_deletes_scheduled(self):
        now = datetime.datetime.now()
        future = now + datetime.timedelta(days=1)
        past = now - datetime.timedelta(days=1)

        self.store["jobs"] = [
            # scheduled -> boleh dihapus
            {"id": 1, "creator_id": 7, "batch_id": 100, "status": "uploaded",
             "schedule_datetime": future, "folder": "F1"},
            # sudah tayang -> TIDAK boleh dihapus
            {"id": 2, "creator_id": 7, "batch_id": 100, "status": "uploaded",
             "schedule_datetime": past, "folder": "F2"},
            # pending -> bukan ranah worker scheduled
            {"id": 3, "creator_id": 7, "batch_id": 101, "status": "pending",
             "schedule_datetime": future, "folder": "F3"},
            # failed -> TIDAK boleh dihapus
            {"id": 4, "creator_id": 7, "batch_id": 101, "status": "failed",
             "schedule_datetime": future, "folder": "F4"},
        ]

        result = report._bulk_delete_scheduled_jobs(7, [1, 2, 3, 4])

        self.assertEqual(result["deleted_ids"], [1])
        self.assertEqual(set(result["skipped_ids"]), {2, 3, 4})
        self.assertEqual([j["id"] for j in self.store["jobs"]], [2, 3, 4])

        # Tidak boleh ada operasi filesystem.
        self.assertEqual(self.fake_shutil.rmtree_calls, [])

        # DELETE harus memakai guard status='uploaded' + schedule_datetime > now.
        delete_calls = [c for c in self.store["calls"] if c[0].startswith("DELETE FROM upload_jobs")]
        self.assertEqual(len(delete_calls), 1)
        self.assertIn("status = 'uploaded'", delete_calls[0][0])
        self.assertIn("schedule_datetime > %s", delete_calls[0][0])

    def test_bulk_delete_pending_unchanged(self):
        now = datetime.datetime.now()
        future = now + datetime.timedelta(days=1)

        self.store["jobs"] = [
            {"id": 10, "creator_id": 7, "batch_id": 200, "status": "pending",
             "schedule_datetime": future, "folder": "P"},
            {"id": 11, "creator_id": 7, "batch_id": 200, "status": "uploaded",
             "schedule_datetime": future, "folder": "S"},
        ]

        result = report._bulk_delete_pending_jobs(7, [10, 11])

        self.assertEqual(result["deleted_ids"], [10])
        self.assertEqual([j["id"] for j in self.store["jobs"]], [11])

    # ------------------------------------------------------------------
    # endpoint: bulk_delete
    # ------------------------------------------------------------------
    def test_route_scheduled_delete_never_touches_files(self):
        now = datetime.datetime.now()
        future = now + datetime.timedelta(days=2)

        self.store["jobs"] = [
            {"id": 21, "creator_id": 7, "batch_id": 300, "status": "uploaded",
             "schedule_datetime": future, "folder": "some/scheduled/folder"},
        ]

        resp = _client().post(
            "/creator/7/report/bulk_delete",
            json={"job_ids": [21], "delete_folders": True},
        )
        data = resp.get_json()

        self.assertTrue(data["success"], data)
        self.assertEqual(data["deleted_ids"], [21])
        self.assertEqual(self.store["jobs"], [])
        # Meski delete_folders=True, file scheduled TIDAK dihapus.
        self.assertEqual(self.fake_shutil.rmtree_calls, [])

    def test_route_mixed_pending_and_scheduled(self):
        now = datetime.datetime.now()
        future = now + datetime.timedelta(days=2)

        self.store["jobs"] = [
            {"id": 31, "creator_id": 7, "batch_id": 400, "status": "pending",
             "schedule_datetime": future, "folder": ""},
            {"id": 32, "creator_id": 7, "batch_id": 400, "status": "uploaded",
             "schedule_datetime": future, "folder": ""},
        ]

        resp = _client().post(
            "/creator/7/report/bulk_delete",
            json={"job_ids": [31, 32], "delete_folders": False},
        )
        data = resp.get_json()

        self.assertTrue(data["success"], data)
        self.assertEqual(set(data["deleted_ids"]), {31, 32})
        self.assertEqual(self.store["jobs"], [])
        self.assertEqual(self.fake_shutil.rmtree_calls, [])

    def test_route_pending_bulk_delete_still_deletes_folder(self):
        """Regression: opsi delete_folders untuk pending harus tetap jalan."""
        now = datetime.datetime.now()
        future = now + datetime.timedelta(days=2)

        with tempfile.TemporaryDirectory() as tmp:
            child = self._make_schedule_dir(tmp)
            self.store["jobs"] = [
                {"id": 61, "creator_id": 7, "batch_id": 500, "status": "pending",
                 "schedule_datetime": future, "folder": child},
            ]

            resp = _client().post(
                "/creator/7/report/bulk_delete",
                json={"job_ids": [61], "delete_folders": True},
            )
            data = resp.get_json()

            self.assertTrue(data["success"], data)
            self.assertEqual(data["deleted_ids"], [61])
            self.assertEqual(self.fake_shutil.rmtree_calls, [child])

    # ------------------------------------------------------------------
    # endpoint: remove_schedule (single)
    # ------------------------------------------------------------------
    def test_remove_schedule_scheduled_does_not_delete_folder(self):
        now = datetime.datetime.now()
        future = now + datetime.timedelta(days=2)

        with tempfile.TemporaryDirectory() as tmp:
            child = self._make_schedule_dir(tmp)
            self.store["jobs"] = [
                {"id": 41, "creator_id": 7, "status": "uploaded",
                 "schedule_datetime": future, "folder": child},
            ]

            resp = _client().post(
                "/creator/7/report/remove_schedule", json={"job_id": 41}
            )
            data = resp.get_json()

            self.assertTrue(data["success"], data)
            self.assertEqual(self.store["jobs"], [])
            self.assertEqual(self.fake_shutil.rmtree_calls, [])
            self.assertTrue(os.path.isdir(child))

    def test_remove_schedule_pending_still_deletes_folder(self):
        now = datetime.datetime.now()
        future = now + datetime.timedelta(days=2)

        with tempfile.TemporaryDirectory() as tmp:
            child = self._make_schedule_dir(tmp)
            self.store["jobs"] = [
                {"id": 51, "creator_id": 7, "status": "pending",
                 "schedule_datetime": future, "folder": child},
            ]

            resp = _client().post(
                "/creator/7/report/remove_schedule", json={"job_id": 51}
            )
            data = resp.get_json()

            self.assertTrue(data["success"], data)
            self.assertEqual(self.store["jobs"], [])
            self.assertEqual(self.fake_shutil.rmtree_calls, [child])


if __name__ == "__main__":
    unittest.main()
