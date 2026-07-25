# File: includes/tiktok_uploader.py
import uiautomator2 as u2
import subprocess
import time
from datetime import datetime
import random
import ipaddress
from bs4 import BeautifulSoup

DEVICE = None
state = {
    "status": "off",
    "log": []
}
d = None

def add_log(message, level="info"):
    icons = {
        "info": "🔍",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "debug": "🐞"
    }
    log = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "device": DEVICE,
        "level": level,
        "icon": icons.get(level, "ℹ️"),
        "message": message
    }
    clean = BeautifulSoup(message, "html.parser").get_text()
    print(
        f"{clean}"
    )
    state["log"].append(
        log
    )

def is_running():
    return state["status"] == "on"

def connect_device():
    global d
    if d is None:
        add_log(
            "Connecting device...",
            "info"
        )
        d = u2.connect(
            DEVICE
        )
        add_log(
            "Device connected",
            "success"
        )
    return d

def push_file(device, local_file, remote_path):
    add_log(
        "Push file started",
        "info"
    )
    if not is_running():
        add_log(
            "Push cancelled",
            "warning"
        )
        return False
    cmd = [
        "adb",
        "-s",
        device,
        "push",
        local_file,
        remote_path
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        add_log(
            "Push file success",
            "success"
        )
        return True
    add_log(
        result.stderr,
        "error"
    )
    return False

def click_profil(timeout=30):
    add_log(
        "Searching Profil...",
        "info"
    )
    start = time.time()
    while True:
        if not is_running():
            add_log(
                "Stop requested while searching Profil",
                "warning"
            )
            return False
        if time.time() - start > timeout:
            add_log(
                "Profil timeout",
                "error"
            )
            return False
        try:
            if d(text="Profil").exists:
                d(text="Profil").click()
                add_log(
                    "Profil clicked",
                    "success"
                )
                return True
            add_log(
                "Waiting Profil...",
                "debug"
            )
        except Exception as e:
            add_log(
                f"Error Profil: {e}",
                "error"
            )
        time.sleep(1)

def is_user_exist(username, timeout=30):
    if not username.startswith("@"):
        username = "@" + username
    add_log(
        f"Searching user {username}",
        "info"
    )
    start = time.time()
    while True:
        if not is_running():
            add_log(
                "Stop requested while searching user",
                "warning"
            )
            return False
        if time.time() - start > timeout:
            add_log(
                f"User not found: {username}",
                "error"
            )
            return False
        try:
            if d(text=username).exists:
                add_log(
                    f"User found: {username}",
                    "success"
                )
                #print(d.dump_hierarchy())
                return True
            if d(textContains=username).exists:
                add_log(
                    f"User found: {username}",
                    "success"
                )
                return True
            add_log(
                f"Waiting user: {username}",
                "debug"
            )
        except Exception as e:
            add_log(
                f"Error user check: {e}",
                "error"
            )
        time.sleep(1)

def reconnect():
    global d

    d = u2.connect(DEVICE)

    return d

def d_click(x, y, min_delay=0.5, max_delay=1.0):
    global DEVICE
    global d

    while True:
        try:
            d.click(
                x,
                y
            )

            time.sleep(
                random.uniform(
                    float(min_delay),
                    float(max_delay)
                )
            )

            return d

        except Exception as e:
            add_log(
                f"Click error: {e}",
                "warning"
            )

            add_log(
                "Reconnecting device...",
                "warning"
            )

            d = u2.connect(
                DEVICE
            )

            time.sleep(1)


def adb_screenshot(
    device="192.168.100.3:5555",
    output_file="./screen.png"
):
    start = time.perf_counter()

    with open(output_file, "wb") as f:
        subprocess.run(
            [
                "adb",
                "-s",
                device,
                "exec-out",
                "screencap",
                "-p"
            ],
            stdout=f,
            stderr=subprocess.DEVNULL,
            check=True
        )

    elapsed = time.perf_counter() - start
    print(f"Screenshot saved: {output_file} ({elapsed:.3f}s)")

    return output_file

def adb_pull(
    remote_file,
    local_file,
    device="192.168.100.3:5555"
):
    subprocess.run(
        [
            "adb",
            "-s",
            device,
            "pull",
            remote_file,
            local_file
        ],
        check=True
    )

# ini adalah main function
def uploader_worker(
    device="192.168.100.3:5555",
    username="@kang.petruk4"
):
    global DEVICE
    DEVICE = device
    start_time = time.perf_counter()
    add_log("Uploader worker started", "info")
    add_log("Device : " + DEVICE, "info")
    add_log("Username : " + username, "info")

    connect_device()
    """
    if not click_profil():
        add_log(
            "Worker cancelled",
            "warning"
        )
        return
    if not is_user_exist(username):
        add_log(
            "Worker cancelled",
            "warning"
        )
        return
    time.sleep(random.randint(6, 8))
    
    # ini tombol plus
    d = d_click(
        360,     # x
        1419,    # y
        5,       # min delay (detik)
        7        # max delay (detik)
    )
    add_log("Klik Tombol Plus", "success")
    
    d = d_click(
        80,     # x
        1425,    # y
        1,       # min delay (detik)
        2        # max delay (detik)
    )
    add_log("Klik Pilih media local Video", "success")

    if d(text="Video").exists:
        d(text="Video").click()
        add_log("Video clicked", "success")
    time.sleep(random.randint(1, 2))

    d = d_click(
        114,     # x
        383,    # y
        3,       # min delay (detik)
        4        # max delay (detik)
    )
    add_log("Click Video Pilih Pertama", "success")

    d = d_click(
        516, 1400, # x, y
        8, 10      # min delay (detik), max delay (detik)
    )

    add_log("Click 'Berikutnya'", "success")
    time.sleep(random.randint(9, 12))

    d = d_click(
        516, 1400, # x, y
        10, 15      # min delay (detik), max delay (detik)
    )
    add_log("Click Berikutnya lagi...", "success")

    # d.click(44, 191)
    # add_log("Click 'Klik deskripsi Box'", "success")
    # time.sleep(random.randint(10, 15))

    deskpr = "Daster Yukensi motif melati rayon jumbo LD 120cm ini nyaman banget dipakai di rumah atau santai. Bahannya adem dan motifnya cantik! Order sekarang sebelum kehabisan di keranjang kuning! #DasterJumbo #DasterRayon #DasterMelati #DasterWanita #OOTDDaster "
    
    try:
        if d(text="Tambah deskripsi...").exists:
            d(text="Tambah deskripsi...").click()
            d.send_keys(deskpr)
            time.sleep(random.randint(1, 2))
        else:
            add_log(
                "Description box not found",
                "error"
            )
    except Exception as e:
        add_log(
            f"Reconnect: {e}",
            "warning"
        )

        reconnect()
        if d(text="Tambah deskripsi...").exists:
            d(text="Tambah deskripsi...").click()
            d.send_keys(deskpr)
            time.sleep(random.randint(1, 2))
        else:
            add_log(
                "Description box not found",
                "error"
            )
    time.sleep(random.uniform(0.8, 1.3))

    if d(textContains="Saya menerima").exists:
        d = d_click(
            47, 1270, # x, y
            0.2, 0.6      # min delay (detik), max delay (detik)
        )
        add_log("Agreement checked", "success")

    if d(text="Tambah tautan").exists:
        d(text="Tambah tautan").click()
        add_log(
            "Tambah tautan clicked",
            "success"
        )
    else:
        add_log(
            "Tambah tautan not found",
            "error"
        )
    time.sleep(random.randint(1, 2))

    if d(text="Produk").exists:
        d(text="Produk").click()
        add_log(
            "Produk clicked",
            "success"
        )
    else:
        add_log(
            "Produk not found",
            "error"
        )
    time.sleep(random.randint(8, 12))

    d = d_click(
        111, 222,
        8, 10
    )
    search_string = "NEW ARRIVAL Setelan Tangtop Yukensi PUMPKIN celana pendek hotpans Wanita Dewasa"
    d.send_keys(search_string)
    time.sleep(1)
    d.press("enter")


 """
    search_string = "gaun cantik"
   
    time.sleep(
        random.uniform(1, 2)
    )

    add_log(
        f"mulai ss",
        "info"
    )
    remote_file = "/storage/emulated/0/DCIM/screenshot.png"
    local_file = "./screenshot_13.png"

    #d.pull(remote_file, local_file)

    d.push(r"E:\tiktok\Second.ty\70\Dress 8_Lite.mp4", "/storage/emulated/0/DCIM/Dress 8_Lite.mp4")
    add_log(
        f"selesai ss",
        "info"
    )

    total_time = time.perf_counter() - start_time
    add_log(
        f"Total process: {total_time:.2f} sec",
        "success"
    )

    return False

    print("dump_hierarchy berhasil disimpan ke ./dump_hierarchy.txt")
    # for node in d.xpath("//*[@text]").all():
    #     print(node.text)
    # return False

    # Ambil 3 kata pertama
    awal_search_string = " ".join(
        search_string.split()[:3]
    )



    if d(textContains=awal_search_string).exists:
        add_log(
            f"Product ada cok: {awal_search_string}",
            "info"
        )
        d.click(573,445)
        time.sleep(1)
    else:
        add_log(
            f"Product not found: {awal_search_string}",
            "error"
        )
         
    if d(text="Tambah").exists:
        add_log(
            f"Tombol 'Tambah ada loh'",
            "success"
        )
        d(text="Tambah").click()

    time.sleep(3)

    nama_produk_string = "cobain mumpung promo"
    d.clear_text()
    time.sleep(random.uniform(0.4, 1.2))
    d.send_keys(nama_produk_string)
    time.sleep(random.uniform(1.4, 3))
    d.click(360,1397)
    time.sleep(random.uniform(5, 7))
    # proses berikutnya nanti disini
    #
    # push_file()
    # cari username
    # upload video
    total_time = time.perf_counter() - start_time
    add_log(
        f"Total process: {total_time:.2f} sec",
        "success"
    )
    add_log(
        "Uploader worker finished",
        "success"
    )