# FILE : includes\ocr_img_to_text_ss.py
import os
import cv2
import easyocr
import numpy as np
from includes.logFX import logger
import warnings

warnings.filterwarnings(
    "ignore",
    message=".*pin_memory.*"
)

class OCRProcessor:

    def __init__(self, product_link, gpu=False):

        logger("debug", "Loading EasyOCR ...")
        self.reader = easyocr.Reader(['id', 'en'], gpu=gpu)
        logger("debug", "EasyOCR Ready.")

        self.product_link = product_link
        self.temp_dir = "./temp/" + product_link

        os.makedirs(self.temp_dir, exist_ok=True)

    # ==========================================================
    # OCR gambar utama (HANYA SEKALI)
    # ==========================================================
    def ocr_image(self, img):

        logger("debug", "Running OCR ...")
        return self.reader.readtext(img)

    # ==========================================================
    # OCR hasil crop
    # ==========================================================
    def read_crop(self, img_path):

        result = self.reader.readtext(img_path)

        text = []

        for bbox, t, conf in result:
            if conf > 0.30:
                text.append(t)

        return " ".join(text)

    # ==========================================================
    # Save crop
    # ==========================================================
    def save_crop(self, crop, index):

        filename = os.path.join(
            self.temp_dir,
            f"text_{index}.jpg"
        )

        cv2.imwrite(filename, crop)

        logger("debug", f"Saved : {filename}")

    # ==========================================================
    # Scan folder temp
    # ==========================================================
    def scan_images(self):

        ext = (".jpg", ".jpeg", ".png")

        files = []

        for file in sorted(os.listdir(self.temp_dir)):

            if file.lower().endswith(ext):
                files.append(
                    os.path.join(
                        self.temp_dir,
                        file
                    )
                )

        return files

    # ==========================================================
    # Crop berdasarkan keyword
    # ==========================================================
    def crop_per_img_per_line(
            self,
            img,
            results,
            kata_list,
            start_index=1
    ):

        h, w = img.shape[:2]

        idx = start_index

        target_lines = []

        # ------------------------------------------
        # Cari semua keyword
        # ------------------------------------------
        for bbox, text, conf in results:

            txt = text.lower()

            if any(k.lower() in txt for k in kata_list):

                pts = np.array(bbox).astype(int)

                target_lines.append({

                    "x_min": np.min(pts[:, 0]),
                    "x_max": np.max(pts[:, 0]),

                    "y_min": np.min(pts[:, 1]),
                    "y_max": np.max(pts[:, 1])

                })

        # ------------------------------------------
        # Gabungkan satu baris
        # ------------------------------------------
        for target in target_lines:

            line_x_min = target["x_min"]
            line_x_max = target["x_max"]

            line_y_min = target["y_min"]
            line_y_max = target["y_max"]

            center_y = (
                line_y_min +
                line_y_max
            ) / 2

            for bbox, text, conf in results:

                pts = np.array(bbox).astype(int)

                x_min = np.min(pts[:, 0])
                x_max = np.max(pts[:, 0])

                y_min = np.min(pts[:, 1])
                y_max = np.max(pts[:, 1])

                if y_min <= center_y <= y_max:

                    line_x_min = min(line_x_min, x_min)
                    line_x_max = max(line_x_max, x_max)

                    line_y_min = min(line_y_min, y_min)
                    line_y_max = max(line_y_max, y_max)

            pad_x = 15
            pad_y = 8

            x1 = max(0, line_x_min - pad_x)
            y1 = max(0, line_y_min - pad_y)

            x2 = min(w, line_x_max + pad_x)
            y2 = min(h, line_y_max + pad_y)

            crop = img[y1:y2, x1:x2]

            self.save_crop(
                crop,
                idx
            )

            idx += 1

        return idx
    
    # ==========================================================
    # Crop bagian kedua
    # ==========================================================
    def crop_kedua_img(
                self,
                img,
                results,
                start_index=3
        ):

            h, w = img.shape[:2]

            idx = start_index

            # value_char dihapus agar pencarian angka bersifat universal (bebas untuk ribuan 'k', persen '%', atau angka satuan biasa)
            targets = [
                {"label": "pesanan"},
                {"label": "ctr"},
                {"label": "jumlah kreator"},
                {"label": "pembeli"},
                {"label": "stok tersedia"},
            ]

            for target in targets:

                label_boxes = []
                value_box = None

                # -------------------------------------
                # Cari label
                # -------------------------------------
                for bbox, text, conf in results:

                    txt = text.lower()

                    if target["label"] in txt:

                        label_boxes.append(bbox)

                        if target["label"] == "pembeli":

                            for bbox2, text2, conf2 in results:

                                txt2 = text2.lower()

                                if (
                                    "menambahkan" in txt2
                                    or
                                    "keranjang" in txt2
                                ):
                                    label_boxes.append(bbox2)

                if not label_boxes:
                    logger("debug", f"{target['label']} tidak ditemukan.")
                    continue

                # -------------------------------------
                # Gabung semua bbox label
                # -------------------------------------
                all_pts = []

                for box in label_boxes:
                    all_pts.extend(box)

                all_pts = np.array(all_pts).astype(int)

                l_x_min = np.min(all_pts[:, 0])
                l_x_max = np.max(all_pts[:, 0])

                l_y_min = np.min(all_pts[:, 1])
                l_y_max = np.max(all_pts[:, 1])

                # -------------------------------------
                # Cari value (Menggunakan Validasi Overlap Jalur Kolom X)
                # -------------------------------------
                min_dist = 999999

                for bbox, text, conf in results:

                    txt = text.lower()

                    # Cek agar box ini tidak berbenturan dengan box label yang sudah diambil
                    is_already_label = any(np.array_equal(bbox, lb) for lb in label_boxes)

                    # Kondisi: wajib mengandung angka dan bukan bagian dari label
                    if any(c.isdigit() for c in txt) and not is_already_label:

                        pts = np.array(bbox).astype(int)

                        v_x_min = np.min(pts[:, 0])
                        v_x_max = np.max(pts[:, 0])

                        v_y_min = np.min(pts[:, 1])
                        v_y_max = np.max(pts[:, 1])

                        # Logika Overlap: Memastikan koordinat X angka berada di dalam
                        # jangkauan kolom X milik label teks
                        horizontal_overlap = (
                            (v_x_min < l_x_max)
                            and
                            (v_x_max > l_x_min)
                        )

                        if not horizontal_overlap:
                            continue

                        # ==========================================
                        # Khusus stok tersedia -> value di atas label
                        # ==========================================
                        if target["label"] == "stok tersedia":

                            if v_y_max < l_y_min:

                                dist = l_y_min - v_y_max

                                if dist < min_dist:

                                    min_dist = dist
                                    value_box = bbox

                        # ==========================================
                        # Label lainnya -> value di bawah label
                        # ==========================================
                        else:

                            if v_y_min > l_y_max:

                                dist = v_y_min - l_y_max

                                if dist < min_dist:

                                    min_dist = dist
                                    value_box = bbox

                # -------------------------------------
                # Gabung value
                # -------------------------------------
                if value_box is not None:

                    pts = np.array(value_box).astype(int)

                    final_pts = np.vstack((
                        all_pts,
                        pts
                    ))

                else:

                    final_pts = all_pts

                x_min = np.min(final_pts[:, 0])
                x_max = np.max(final_pts[:, 0])

                y_min = np.min(final_pts[:, 1])
                y_max = np.max(final_pts[:, 1])

                pad_x = 25
                pad_y = 15

                x1 = max(0, x_min - pad_x)
                y1 = max(0, y_min - pad_y)

                x2 = min(w, x_max + pad_x)
                y2 = min(h, y_max + pad_y)

                crop = img[y1:y2, x1:x2]

                self.save_crop(
                    crop,
                    idx
                )

                idx += 1

            return idx
    
    # ==========================================================
    # Bersihkan folder temp
    # ==========================================================
    def clear_temp(self):

        for file in os.listdir(self.temp_dir):

            path = os.path.join(
                self.temp_dir,
                file
            )

            #if os.path.isfile(path):
            #    os.remove(path)

    # ==========================================================
    # Jalankan proses
    # ==========================================================
    def run(self, image_path):

        self.clear_temp()
        hasilnya = []
        img = cv2.imread(image_path)

        if img is None:
            raise Exception("Image tidak ditemukan.")

        # ==========================================
        # OCR HANYA SEKALI
        # ==========================================
        results = self.ocr_image(img)

        # ==========================================
        # Crop Pertama
        # ==========================================
        next_index = self.crop_per_img_per_line(

            img,
            results,

            [
                "dapatkan",
                "ulasan",
                "komisi"
            ],

            start_index=1
        )

        # ==========================================
        # Crop Kedua
        # ==========================================
        self.crop_kedua_img(

            img,
            results,

            start_index=next_index
        )

        for file in self.scan_images():

            logger("debug", file)

            text = self.read_crop(file)
            hasilnya.append(text)
            logger("debug", "isinya : " + text)

        return hasilnya 

if __name__ == "__main__":

    processor = OCRProcessor(
        gpu=False
    )

    data = processor.run("d.jpeg")
    logger("debug", data)
