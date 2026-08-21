# File : includes\jobs\workflows_facebook.py
"""
workflows_facebook.py — Workflow Facebook HP (Android).

SEJAJAR dengan workflows_KangPetruk.py / workflows_second_ty.py (TikTok HP).
Pola SAMA PERSIS dengan workflow TikTok:
    jobs_json = [...]
    def WorkflowsFacebook():
        return copy.deepcopy(jobs_json)

Setiap langkah adalah command konkret berformat sama dengan TikTok:
    {
        "id": ...,
        "cmd": ...,
        "delay": ...,
        "status": "pending",
        "keterangan": ...,
        "data": { ... }
    }

Command yang dipakai HANYA command Android existing (TIDAK ada command baru):
    push_file, click, input_text

Untuk "click" struktur target SAMA PERSIS dengan TikTok:
    "data": { "target": { "type": "point", "x": ..., "y": ... } }

CATATAN — KOORDINAT FACEBOOK:
    Semua koordinat (x/y) di bawah adalah PLACEHOLDER (0, 0) karena
    koordinat Facebook Android diisi MANUAL satu per satu oleh pengguna.
    Jangan menebak / mencari koordinat Facebook.

URUTAN BISNIS:
    1. push video ke Android
    2. buka/create Reel
    3. pilih video
    4. Next
    5. Next
    6. isi caption
    7. AI label
    8. Add product
    9. isi affiliate URL
    10. isi Link name
    11. Save
    12. buka scheduling
    13. isi tanggal
    14. isi waktu
    15. Schedule for later
    16. Final Schedule

Nilai dinamis (video path/remote, caption, affiliate URL, link name,
tanggal, waktu) di-inject oleh facebook_job_runner.py melalui id —
mekanisme SAMA dengan get_workflow TikTok (workflow.py).
"""

import copy

jobs_json = [
#####################################################
#		1. Kirim file pc -> android
#####################################################
{
    "id": 1,
    "cmd": "push_file",
    "delay": 200,
    "status": "pending",
    "keterangan": "Transfer video Pc ke Android",
    "data": {
        "remote": "/sdcard/Download/<nama_video>.mp4",
        "file_name": r"C:\path\ke\video\di\inject\runner.mp4",
        "mime": "video/mp4"
    }
},
#####################################################
#		2. Buka / create Reel
#####################################################
{
    "id": 2,
    "cmd": "click",
    "delay": 1500,
    "status": "pending",
    "keterangan": "Buka Create reel di Facebook",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
#####################################################
#		3. Pilih video
#####################################################
{
    "id": 3,
    "cmd": "click",
    "delay": 1500,
    "status": "pending",
    "keterangan": "Pilih video dari galeri/media picker",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
#####################################################
#		4. Next 1
#####################################################
{
    "id": 4,
    "cmd": "click",
    "delay": 2000,
    "status": "pending",
    "keterangan": "Next 1 (Create reel -> Edit reel)",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
#####################################################
#		5. Next 2
#####################################################
{
    "id": 5,
    "cmd": "click",
    "delay": 4000,
    "status": "pending",
    "keterangan": "Next 2 (Edit reel -> caption) — menunggu proses video",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
#####################################################
#		6. Isi caption
#####################################################
{
    "id": 6,
    "cmd": "click",
    "delay": 800,
    "status": "pending",
    "keterangan": "Klik textbox caption",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
# ini mengisi caption dari schedule.json (di-inject runner by id=7)
{
    "id": 7,
    "cmd": "input_text",
    "delay": 1000,
    "status": "pending",
    "keterangan": "Isi caption dari schedule.json",
    "data": {
        "target": {
            "type": "class",
            "value": "android.widget.EditText"
        },
        "text": "isi caption disini"
    }
},
#####################################################
#		7. AI label
#####################################################
{
    "id": 8,
    "cmd": "click",
    "delay": 800,
    "status": "pending",
    "keterangan": "AI label aktif (toggle Add AI label)",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
#####################################################
#		8. Add product
#####################################################
{
    "id": 9,
    "cmd": "click",
    "delay": 1500,
    "status": "pending",
    "keterangan": "Add a product to your reel",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
#####################################################
#		9. Isi affiliate URL
#####################################################
{
    "id": 10,
    "cmd": "click",
    "delay": 800,
    "status": "pending",
    "keterangan": "Klik field URL di dialog affiliate",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
# ini mengisi affiliate URL dari schedule.json (di-inject runner by id=11)
{
    "id": 11,
    "cmd": "input_text",
    "delay": 1000,
    "status": "pending",
    "keterangan": "Isi URL affiliate (shopee)",
    "data": {
        "target": {
            "type": "class",
            "value": "android.widget.EditText"
        },
        "text": "https://s.shopee.co.id/isi_affiliate"
    }
},
#####################################################
#		10. Isi Link name
#####################################################
{
    "id": 12,
    "cmd": "click",
    "delay": 500,
    "status": "pending",
    "keterangan": "Klik field Link name",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
# ini mengisi Link name (di-inject runner by id=13)
{
    "id": 13,
    "cmd": "input_text",
    "delay": 1000,
    "status": "pending",
    "keterangan": "Isi Link name",
    "data": {
        "target": {
            "type": "class",
            "value": "android.widget.EditText"
        },
        "text": "Cobain Mumpung PROMO!"
    }
},
#####################################################
#		11. Save
#####################################################
{
    "id": 14,
    "cmd": "click",
    "delay": 1500,
    "status": "pending",
    "keterangan": "Save affiliate",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
#####################################################
#		12. Buka scheduling
#####################################################
{
    "id": 15,
    "cmd": "click",
    "delay": 1000,
    "status": "pending",
    "keterangan": "Buka Scheduling options",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
#####################################################
#		13. Isi tanggal
#####################################################
{
    "id": 16,
    "cmd": "click",
    "delay": 500,
    "status": "pending",
    "keterangan": "Klik field tanggal",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
# ini mengisi tanggal jadwal (di-inject runner by id=17)
{
    "id": 17,
    "cmd": "input_text",
    "delay": 800,
    "status": "pending",
    "keterangan": "Isi tanggal jadwal",
    "data": {
        "target": {
            "type": "class",
            "value": "android.widget.EditText"
        },
        "text": "15 Sep 2026"
    }
},
#####################################################
#		14. Isi waktu
#####################################################
{
    "id": 18,
    "cmd": "click",
    "delay": 500,
    "status": "pending",
    "keterangan": "Klik field waktu",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
# ini mengisi waktu jadwal (di-inject runner by id=19)
{
    "id": 19,
    "cmd": "input_text",
    "delay": 800,
    "status": "pending",
    "keterangan": "Isi waktu jadwal",
    "data": {
        "target": {
            "type": "class",
            "value": "android.widget.EditText"
        },
        "text": "10:30"
    }
},
#####################################################
#		15. Schedule for later
#####################################################
{
    "id": 20,
    "cmd": "click",
    "delay": 1000,
    "status": "pending",
    "keterangan": "Schedule for later",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
#####################################################
#		16. Final Schedule
#####################################################
{
    "id": 21,
    "cmd": "click",
    "delay": 1500,
    "status": "pending",
    "keterangan": "Final Schedule (jadwalkan reel)",
    "data": {
        "target": {
            "type": "point",
            "x": 0,   # TODO device: isi koordinat manual
            "y": 0    # TODO device: isi koordinat manual
        }
    }
},
]


def WorkflowsFacebook():
    return copy.deepcopy(jobs_json)
