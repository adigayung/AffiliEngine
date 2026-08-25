# File : includes\jobs\workflows_facebook.py
import copy

jobs_json = [
####################################################
#		1. Kirim file pc -> android
####################################################
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
    "id": 4,
    "cmd": "click",
    "delay": 2000,
    "status": "pending",
    "keterangan": "klik 'Buat reel'",
    "data": {
        "target": {
            "type": "point",
            "x": 361,
            "y": 930
        }
    }
},
{
    "id": 3,
    "cmd": "click",
    "delay": 1500,
    "status": "pending",
    "keterangan": "Pilih Video pada 'Gallery'",
    "data": {
        "target": {
            "type": "point",
            "x": 113,
            "y": 514
        }
    }
},
{
    "id": 4,
    "cmd": "click",
    "delay": 2000,
    "status": "pending",
    "keterangan": "klik '-> Selanjutnya'",
    "data": {
        "target": {
            "type": "point",
            "x": 555,
            "y": 1341
        }
    }
},
{
    "id": 5,
    "cmd": "click",
    "delay": 2000,
    "status": "pending",
    "keterangan": "klik desk textbox",
    "data": {
        "target": {
            "type": "point",
            "x": 470,
            "y": 326
        }
    }
},
############### [ mengisi deskripsi Video ] ################
{
    "id": 6,
    "cmd": "input_text",
    "delay": 4000,
    "status": "pending",
    "keterangan": "mengisi deskripsi Video",
    "data": {
        "target": {
            "type": "class",
            "value": "android.widget.AutoCompleteTextView"
        },
        "text": "mengisi deskripsi tiktok"
    }
}, ## stop mulai sini
{
    "id": 7,
    "cmd": "click",
    "delay": 1500,
    "status": "pending",
    "keterangan": "klik 'Tambahkan produk'",
    "data": {
        "target": {
            "type": "point",
            "x": 360,
            "y": 822
        }
    }
},
{
    "id": 7,
    "cmd": "click",
    "delay": 1500,
    "status": "pending",
    "keterangan": "klik 'Buat tautan kustom'",
    "data": {
        "target": {
            "type": "point",
            "x": 329,
            "y": 539
        }
    }
},
{
    "id": 7,
    "cmd": "click",
    "delay": 1500,
    "status": "pending",
    "keterangan": "klik 'Buat tautan kustom'",
    "data": {
        "target": {
            "type": "point",
            "x": 136,
            "y": 510
        }
    }
},
{
    "id": 8,
    "cmd": "input_text",
    "delay": 4000,
    "status": "pending",
    "keterangan": "mengisi Url Affiliatess",
    "data": {
        "target": {
            "type": "desc",
            "value": "URL,,"
        },
        "text": "https://s.shopee.co.id/3B6inFdnZg"
    }
},
################ end delay ##############
{
    "id": 5,
    "cmd": "click",
    "delay": 90000,
    "status": "pending",
    "keterangan": "klik desk textbox",
    "data": {
        "target": {
            "type": "point",
            "x": 470,
            "y": 326
        }
    }
},
]

def WorkflowsFacebook():
    return copy.deepcopy(jobs_json)
