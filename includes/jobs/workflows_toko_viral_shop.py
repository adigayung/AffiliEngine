
import copy

jobs_json = [
#####################################################
#		Kirim file pc -> android
#####################################################
{
    "id": 1,
    "cmd": "push_file",
    "delay": 200,
    "status": "pending",
    "keterangan": "Transfer file Pc ke Hp Android",
    "data": {
        "remote": "/sdcard/Download/Dress_1_Lite.mp4",
        "file_name": r"E:\tiktok\Second.ty\38\Dress_1_Lite.mp4",
        "mime": "video/mp4"
    }
},
# #####################################################
# #		Mulai klik Home
# #####################################################
{
    "id": 2,
    "cmd": "click",
    "delay": 1000,
    "status": "pending",
    "keterangan": "Klik Profile ( Home )",
    "data": {
        "target": {
            "type": "point",
            "x": 973,
            "y": 2200
        }
    }
},
{
    "id": 3,
    "cmd": "click",
    "delay": 2000,
    "status": "pending",
    "keterangan": "Klik + ( tombol upload video )",
    "data": {
        "target": {
            "type": "point",
            "x": 542,
            "y": 2200
        }
    }
},
{
    "id": 4,
    "cmd": "click",
    "delay": 3000,
    "status": "pending",
    "keterangan": "Pilih Gallery",
    "data": {
        "target": {
            "type": "point",
            "x": 108,
            "y": 2171
        }
    }
},
{
    "id": 5,
    "cmd": "click",
    "delay": 1000,
    "status": "pending",
    "keterangan": "Pilih Tab video",
    "data": {
        "target": {
            "type": "point",
            "x": 412,
            "y": 291
        }
    }
},
{
    "id": 6,
    "cmd": "click",
    "delay": 1000,
    "status": "pending",
    "keterangan": "Pilih video yang akan di upload",
    "data": {
        "target": {
            "type": "point",
            "x": 170,
            "y": 540
        }
    }
},
{
    "id": 7,
    "cmd": "click",
    "delay": 3000,
    "status": "pending",
    "keterangan": "sudah select video tekan 'Berikutnya'",
    "data": {
        "target": {
            "type": "point",
            "x": 779,
            "y": 2159
        }
    }
},
{
    "id": 8,
    "cmd": "click",
    "delay": 3000,
    "status": "pending",
    "keterangan": "back dulu, anti bug",
    "data": {
        "target": {
            "type": "point",
            "x": 776,
            "y": 2336
        }
    }
},
{
    "id": 8,
    "cmd": "click",
    "delay": 3000,
    "status": "pending",
    "keterangan": "back dulu, anti bug",
    "data": {
        "target": {
            "type": "point",
            "x": 776,
            "y": 2336
        }
    }
},
{
    "id": 6,
    "cmd": "click",
    "delay": 1000,
    "status": "pending",
    "keterangan": "Pilih video yang akan di upload",
    "data": {
        "target": {
            "type": "point",
            "x": 170,
            "y": 540
        }
    }
},
{
    "id": 7,
    "cmd": "click",
    "delay": 3000,
    "status": "pending",
    "keterangan": "sudah select video tekan 'Berikutnya'",
    "data": {
        "target": {
            "type": "point",
            "x": 779,
            "y": 2159
        }
    }
},
{
    "id": 8,
    "cmd": "click",
    "delay": 2500,
    "status": "pending",
    "keterangan": "tekan 'Berikutnya' Lagi",
    "data": {
        "target": {
            "type": "point",
            "x": 779,
            "y": 2159
        }
    }
},
{
    "id": 9,
    "cmd": "click",
    "delay": 3000,
    "status": "pending",
    "keterangan": "Checked 'Konfirmasi Penggunaan Music'",
    "data": {
        "target": {
            "type": "point",
            "x": 65,
            "y": 2040
        }
    }
},
{
    "id": 9,
    "cmd": "click",
    "delay": 2000,
    "status": "pending",
    "keterangan": "Select textbox Deskripsi",
    "data": {
        "target": {
            "type": "point",
            "x": 217,
            "y": 283
        }
    }
},
############################################################
#       Sudah masuk ke panel pahe setting upload vt
############################################################
# ini mengisi deskripsi video tiktok
{
    "id": 10,
    "cmd": "input_text",
    "delay": 1000,
    "status": "pending",
    "keterangan": "mengisi deskripsi tiktok",
    "data": {
        "target": {
            "type": "class",
            "value": "android.widget.EditText"
        },
        "text": "mengisi deskripsi tiktok"
    }
},
{
    "id": 11,
    "cmd": "click",
    "delay": 500,
    "status": "pending",
    "keterangan": "Clear Focus, menghilangkan keyboard ui",
    "data": {
        "target": {
            "type": "point",
            "x": 589,
            "y": 746
        }
    }
},
# #######################################################
# #    Start | mulai tambah tautan
# #######################################################
# # {
# #     "id": 12,
# #     "cmd": "click",
# #     "delay": 1000,
# #     "status": "pending",
# #     "keterangan": "+ Tambah tautan",
# #     "data": {
# #         "target": {
# #             "type": "point",
# #             "x": 254,
# #             "y": 1336
# #         }
# #     }
# # },
# # {
# #     "id": 13,
# #     "cmd": "click",
# #     "delay": 1000,
# #     "status": "pending",
# #     "keterangan": "Klik keranjang kuning",
# #     "data": {
# #         "target": {
# #             "type": "point",
# #             "x": 218,
# #             "y": 1735
# #         }
# #     }
# # },
# # {
# #     "id": 14,
# #     "cmd": "click",
# #     "delay": 5000,
# #     "status": "pending",
# #     "keterangan": "Klik search box",
# #     "data": {
# #         "target": {
# #             "type": "point",
# #             "x": 154,
# #             "y": 306
# #         }
# #     }
# # },
# # # ini mengisi text pencarian
# # {
# #     "id": 15,
# #     "cmd": "input_text",
# #     "delay": 6000,
# #     "status": "pending",
# #     "keterangan": "mengisi Pencarian product",
# #     "data": {
# #         "target": {
# #             "type": "class",
# #             "value": "android.widget.EditText"
# #         },
# #         "text": "isi product disini"
# #     }
# # },
# # {
# #     "id": 16,
# #     "cmd": "input_text",
# #     "delay": 6000,
# #     "status": "pending",
# #     "keterangan": "mengisi Pencarian product",
# #     "data": {
# #         "target": {
# #             "type": "class",
# #             "value": "android.widget.EditText"
# #         },
# #         "text": "isi product disini"
# #     }
# # },
# # {
# #     "id": 17,
# #     "cmd": "click",
# #     "delay": 800,
# #     "status": "pending",
# #     "keterangan": "Klik cari",
# #     "data": {
# #         "target": {
# #             "type": "point",
# #             "x": 1002,
# #             "y": 2174
# #         }
# #     }
# # },
# # {
# #     "id": 18,
# #     "cmd": "click",
# #     "delay": 6000,
# #     "status": "pending",
# #     "keterangan": "Klik 'tambah'",
# #     "data": {
# #         "target": {
# #             "type": "point",
# #             "x": 882,
# #             "y": 613
# #         }
# #     }
# # },
# # {
# #     "id": 19,
# #     "cmd": "click",
# #     "delay": 1200,
# #     "status": "pending",
# #     "keterangan": "Klik 'tambah' lagi",
# #     "data": {
# #         "target": {
# #             "type": "point",
# #             "x": 536,
# #             "y": 1258
# #         }
# #     }
# # },

# # # mengisi atau ganti text keranjang

# # {   # membaca text dari keranjang, di pastikan produknya sama
# #     "id": 20,
# #     "cmd": "read_text",
# #     "delay": 200,
# #     "status": "pending",
# #     "keterangan": "membaca title produk di textbox",
# #     "data": {
# #         "target": {
# #             "type": "class",
# #             "value": "android.widget.EditText"
# #         }
# #     }
# # },
# # {
# #     "id": 21,
# #     "cmd": "input_text",
# #     "delay": 200,
# #     "status": "pending",
# #     "keterangan": "mengganti title keranjang",
# #     "data": {
# #         "target": {
# #             "type": "class",
# #             "value": "android.widget.EditText"
# #         },
# #         "text": "Cobain mumpung promo"
# #     }
# # },
# # {
# #     "id": 22,
# #     "cmd": "click",
# #     "delay": 800,
# #     "status": "pending",
# #     "keterangan": "Klik ok Keyboard",
# #     "data": {
# #         "target": {
# #             "type": "point",
# #             "x": 986,
# #             "y": 2192
# #         }
# #     }
# # },
# # {
# #     "id": 23,
# #     "cmd": "click",
# #     "delay": 800,
# #     "status": "pending",
# #     "keterangan": "Klik 'Tambah'",
# #     "data": {
# #         "target": {
# #             "type": "point",
# #             "x": 540,
# #             "y": 2160
# #         }
# #     }
# # },
# #######################################################
# #    End  tambah tautan
# #######################################################

# mulai jadwal
{
    "id": 24,
    "cmd": "click",
    "delay": 800,
    "status": "pending",
    "keterangan": "klik 'Opsi lainya'",
    "data": {
        "target": {
            "type": "desc",
            "value": "Opsi lainnya"
        }
    }
},
{
    "id": 25,
    "cmd": "click",
    "delay": 1800,
    "status": "pending",
    "keterangan": "klik 'Jadwalkan posting'",
    "data": {
        "target": {
            "type": "point",
            "x": 346,
            "y": 1713
        }
    }
},
{
    "id": 26,
    "cmd": "set_schedule_time",
    "status": "pending",
    "keterangan": "Setting taggal upload",
    "delay": 1000,
    "data": {
        "day": 10,
        "hour": 10,
        "minute": 10
    }
},
{
    "id": 27,
    "cmd": "click",
    "delay": 800,
    "status": "pending",
    "keterangan": "klik 'selesai' di jadwal",
    "data": {
        "target": {
            "type": "point",
            "x": 529,
            "y": 2164
        }
    }
},
{
    "id": 27,
    "cmd": "click",
    "delay": 1000,
    "status": "pending",
    "keterangan": "klik Close UI jadwal",
    "data": {
        "target": {
            "type": "point",
            "x": 827,
            "y": 441
        }
    }
},

###############################################
#       Klik Posting ( BERES !!!!)
###############################################
{ # ini klik draft
    "id": 28,
    "cmd": "click",
    "delay": 1200,
    "status": "pending",
    "keterangan": "Klik Draft ( KELAR ! )'",
    "data": {
        "target": {
            "type": "point",
            "x": 271,
            "y": 2170
        }
    }
},
# { # ini klik posting
#     "id": 28,
#     "cmd": "click",
#     "delay": 800,
#     "status": "done",
#     "keterangan": "Posting video ( KELAR ! )'",
#     "data": {
#         "target": {
#             "type": "point",
#             "x": 811,
#             "y": 2176
#         }
#     }
# },
#####################################################
#		Hapus File video
#####################################################
# {
#     "id": 29,
#     "cmd": "delete_file",
#     "delay": 5000,
#     "status": "pending",
#     "keterangan": "Hapus file xxxx di hape",
#     "data": {
#         "remote": "/sdcard/Download/Dress_1_Lite.mp4"
#     }
# },
]

def WorkflowsTokoViralShop():
    return copy.deepcopy(jobs_json)