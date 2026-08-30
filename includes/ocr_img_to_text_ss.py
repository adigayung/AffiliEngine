# FILE : includes\ocr_img_to_text_ss.py
import os
import re
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
    # Cari box label dengan word boundary + preferensi terpendek
    # ==========================================================
    def _find_label_boxes(self, results, keyword):
        """
        Temukan box label untuk sebuah keyword.

        Menggunakan word boundary agar keyword tidak tertukar dengan
        potongan kata lain, lalu memprioritaskan box dengan sisa teks
        terpendek (label yang berdiri sendiri).

        Contoh penting:
            keyword "pesanan" -> box 'Pesanan' (bukan
            'Penghasilan menurut sumber pesanan').
        """
        pattern = re.compile(
            r'\b' + re.escape(keyword) + r'\b',
            re.IGNORECASE
        )

        candidates = []

        for bbox, text, conf in results:

            txt = text.lower()

            if pattern.search(txt):

                remainder = pattern.sub('', txt).strip()

                candidates.append({
                    "bbox": bbox,
                    "remainder_len": len(remainder),
                })

        if not candidates:
            return []

        min_remainder = min(
            c["remainder_len"]
            for c in candidates
        )

        return [
            c["bbox"]
            for c in candidates
            if c["remainder_len"] == min_remainder
        ]

    # ==========================================================
    # Cari value kedua di bawah value pertama (kolom yang sama)
    # ==========================================================
    def _find_second_value_below(
            self,
            results,
            value_box,
            label_boxes=None
    ):
        """
        Cari nilai kedua yang berada di bawah `value_box` dalam
        kolom yang sama. Dipakai untuk mengambil value sekunder pada
        kartu metrik UI TikTok terbaru (contoh: 'ulasan' tampil tepat
        di bawah value 'pesanan' tanpa label teks).
        """
        vpts = np.array(value_box).astype(int)

        v_x_min = np.min(vpts[:, 0])
        v_x_max = np.max(vpts[:, 0])
        v_y_max = np.max(vpts[:, 1])

        excluded = label_boxes or []

        best_box = None
        best_score = 999999

        for bbox, text, conf in results:

            txt = text.lower()

            # Wajib mengandung angka dan bukan label / value utama
            if not any(c.isdigit() for c in txt):
                continue

            if any(np.array_equal(bbox, lb) for lb in excluded):
                continue

            if np.array_equal(bbox, value_box):
                continue

            pts = np.array(bbox).astype(int)

            x_min = np.min(pts[:, 0])
            x_max = np.max(pts[:, 0])

            y_min = np.min(pts[:, 1])

            # Harus berada di bawah value pertama
            if y_min <= v_y_max:
                continue

            v_dist = y_min - v_y_max

            # Jarak horizontal: 0 jika overlap kolom, jika tidak gap
            h_overlap = (
                min(x_max, v_x_max)
                - max(x_min, v_x_min)
            )

            if h_overlap > 0:
                h_penalty = 0
            else:
                h_penalty = max(
                    x_min - v_x_max,
                    v_x_min - x_max,
                    0
                )

            score = v_dist + 0.6 * h_penalty

            if score < best_score:
                best_score = score
                best_box = bbox

        return best_box

    # ==========================================================
    # Cari box rating "X/5.0" yang sebaris dengan label
    # ==========================================================
    def _find_rating_box(self, results, label_boxes):
        """
        Cari rating "X/5.0" (mis. "4.0/5.0") yang berdekatan secara
        spasial dengan label "Skor produk ...".

        Label dan rating bisa berada pada OCR box yang berbeda,
        jadi gunakan kedekatan bounding box:
        - rating harus sebaris (overlap vertikal) dengan label;
        - rating adalah box terdekat secara horizontal.
        """
        all_pts = []

        for box in label_boxes:
            all_pts.extend(box)

        all_pts = np.array(all_pts).astype(int)

        l_x_min = np.min(all_pts[:, 0])
        l_x_max = np.max(all_pts[:, 0])

        l_y_min = np.min(all_pts[:, 1])
        l_y_max = np.max(all_pts[:, 1])

        l_cy = (l_y_min + l_y_max) / 2

        pattern = re.compile(
            r'[\d.,Oo]+\s*/\s*5(?:[.Oo]0)?'
        )

        best_box = None
        best_score = 999999

        for bbox, text, conf in results:

            if not pattern.search(text):
                continue

            if any(
                np.array_equal(bbox, lb)
                for lb in label_boxes
            ):
                continue

            pts = np.array(bbox).astype(int)

            x_min = np.min(pts[:, 0])
            x_max = np.max(pts[:, 0])

            y_min = np.min(pts[:, 1])
            y_max = np.max(pts[:, 1])

            # Harus sebaris dengan label (overlap vertikal)
            row_overlap = (
                (y_min < l_y_max)
                and
                (y_max > l_y_min)
            )

            if not row_overlap:
                continue

            # Jarak horizontal: kanan label (umum), kiri dipenalti
            if x_min >= l_x_max:
                h_gap = x_min - l_x_max
            elif x_max <= l_x_min:
                h_gap = (l_x_min - x_max) + 50
            else:
                h_gap = 0  # overlap horizontal (rating menyatu label)

            v_off = abs(
                ((y_min + y_max) / 2) - l_cy
            )

            score = h_gap + 2 * v_off

            if score < best_score:
                best_score = score
                best_box = bbox

        return best_box

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

            # Menyimpan index crop -> label teks yang harus disisipkan
            # di depan hasil OCR crop tersebut.
            labeled = {}

            # ==================================================
            # PRIORITAS 1 — "Skor produk" -> rating X/5.0 -> ulasan
            # UI terbaru menampilkan rating produk (mis. "4.0/5.0")
            # sebagai box terpisah di samping label "Skor produk ...".
            # ==================================================
            skor_rating_found = False

            skor_label_boxes = self._find_label_boxes(
                results,
                "skor produk"
            )

            # Fallback: bila OCR memecah label menjadi box terpisah
            if not skor_label_boxes:
                skor_label_boxes = self._find_label_boxes(
                    results,
                    "skor"
                )

            rating_box = None

            if skor_label_boxes:

                rating_box = self._find_rating_box(
                    results,
                    skor_label_boxes
                )

                # Bila rating menyatu dalam box label itu sendiri
                if rating_box is None:

                    for lb in skor_label_boxes:

                        for bbox, text, conf in results:

                            if (
                                np.array_equal(bbox, lb)
                                and re.search(
                                    r'[\d.,Oo]+\s*/\s*5(?:[.Oo]0)?',
                                    text
                                )
                            ):
                                rating_box = bbox
                                break

                        if rating_box is not None:
                            break

            if rating_box is not None:

                skor_rating_found = True

                rpts = np.array(rating_box).astype(int)

                rx1 = max(0, np.min(rpts[:, 0]) - 12)
                ry1 = max(0, np.min(rpts[:, 1]) - 6)

                rx2 = min(w, np.max(rpts[:, 0]) + 12)
                ry2 = min(h, np.max(rpts[:, 1]) + 6)

                self.save_crop(
                    img[ry1:ry2, rx1:rx2],
                    idx
                )

                # Label "ulasan" disisipkan di depan hasil OCR crop
                labeled[idx] = "ulasan"

                idx += 1

            else:
                logger(
                    "debug",
                    "skor produk tidak ditemukan (fallback ulasan aktif)."
                )

            # value_char dihapus agar pencarian angka bersifat universal
            # (bebas untuk ribuan 'k', persen '%', atau angka satuan biasa)
            targets = [
                {"label": "pesanan", "secondary": "ulasan"},
                {"label": "ctr"},
                {"label": "jumlah kreator"},
                {"label": "pembeli"},
                {"label": "stok tersedia"},
            ]

            for target in targets:

                # -------------------------------------
                # Cari label (word boundary + preferensi terpendek)
                # -------------------------------------
                label_boxes = self._find_label_boxes(
                    results,
                    target["label"]
                )

                # Khusus pembeli: label berlanjut pada box
                # "menambahkan ke keranjang"
                if target["label"] == "pembeli":

                    for bbox2, text2, conf2 in results:

                        txt2 = text2.lower()

                        if (
                            "menambahkan" in txt2
                            or
                            "keranjang" in txt2
                        ):

                            if not any(
                                np.array_equal(bbox2, lb)
                                for lb in label_boxes
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

                l_cx = (l_x_min + l_x_max) / 2

                # -------------------------------------
                # Cari value dengan skor gabungan
                # (jarak vertikal + penalti gap horizontal +
                #  penalti selisih center X)
                # -------------------------------------
                value_box = None
                best_score = 999999

                for bbox, text, conf in results:

                    txt = text.lower()

                    # Cek agar box ini tidak berbenturan dengan box label
                    is_already_label = any(
                        np.array_equal(bbox, lb)
                        for lb in label_boxes
                    )

                    # Kondisi: wajib mengandung angka & bukan bagian label
                    if (
                        any(c.isdigit() for c in txt)
                        and not is_already_label
                    ):

                        pts = np.array(bbox).astype(int)

                        v_x_min = np.min(pts[:, 0])
                        v_x_max = np.max(pts[:, 0])

                        v_y_min = np.min(pts[:, 1])
                        v_y_max = np.max(pts[:, 1])

                        # ==================================
                        # Khusus stok tersedia -> value di atas label
                        # ==================================
                        if target["label"] == "stok tersedia":

                            if v_y_max >= l_y_min:
                                continue

                            v_dist = l_y_min - v_y_max

                        # ==================================
                        # Label lainnya -> value di bawah label
                        # ==================================
                        else:

                            if v_y_min <= l_y_max:
                                continue

                            v_dist = v_y_min - l_y_max

                        # Jarak horizontal: 0 jika overlap kolom,
                        # jika tidak berupa gap antar kolom
                        h_overlap = (
                            min(v_x_max, l_x_max)
                            - max(v_x_min, l_x_min)
                        )

                        if h_overlap > 0:
                            h_penalty = 0
                        else:
                            h_penalty = max(
                                v_x_min - l_x_max,
                                l_x_min - v_x_max,
                                0
                            )

                        # Penalti kecil untuk selisih center X
                        v_cx = (v_x_min + v_x_max) / 2
                        align_penalty = abs(v_cx - l_cx)

                        score = (
                            v_dist
                            + 0.6 * h_penalty
                            + 0.05 * align_penalty
                        )

                        if score < best_score:
                            best_score = score
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

                # -------------------------------------
                # Cari value sekunder (mis. ulasan di bawah pesanan)
                # -------------------------------------
                secondary_box = None
                secondary_label = target.get("secondary")

                if (
                    secondary_label
                    and value_box is not None
                ):

                    # Jika label sekunder sudah terdeteksi OCR
                    # (UI lama), jangan generate ulang -> parser lama
                    # sudah menangani lewat crop_per_img_per_line.
                    has_secondary_text = any(
                        secondary_label in t.lower()
                        for _, t, _ in results
                    )

                    # PRIORITAS 3 — hanya fallback bila rating
                    # "Skor produk" (PRIORITAS 1) tidak ditemukan
                    if (
                        not has_secondary_text
                        and not skor_rating_found
                    ):

                        secondary_box = self._find_second_value_below(
                            results,
                            value_box,
                            label_boxes
                        )

                        if secondary_box is not None:

                            spts = np.array(
                                secondary_box
                            ).astype(int)

                            s_y_min = np.min(spts[:, 1])

                            # Batasi crop utama agar tidak ikut
                            # memotong value sekunder
                            y2 = min(y2, max(y1, s_y_min - 3))

                crop = img[y1:y2, x1:x2]

                self.save_crop(
                    crop,
                    idx
                )

                idx += 1

                # -------------------------------------
                # Simpan crop value sekunder (ulasan)
                # -------------------------------------
                if secondary_box is not None:

                    spts = np.array(secondary_box).astype(int)

                    sx_min = np.min(spts[:, 0])
                    sx_max = np.max(spts[:, 0])

                    sy_min = np.min(spts[:, 1])
                    sy_max = np.max(spts[:, 1])

                    s_pad_x = 12
                    s_pad_y = 6

                    sx1 = max(0, sx_min - s_pad_x)
                    sy1 = max(0, sy_min - s_pad_y)

                    sx2 = min(w, sx_max + s_pad_x)
                    sy2 = min(h, sy_max + s_pad_y)

                    crop2 = img[sy1:sy2, sx1:sx2]

                    self.save_crop(
                        crop2,
                        idx
                    )

                    # Label disisipkan di depan hasil OCR crop ini
                    labeled[idx] = secondary_label

                    idx += 1

            return idx, labeled
    
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
        next_index, labeled = self.crop_kedua_img(

            img,
            results,

            start_index=next_index
        )

        for file in self.scan_images():

            logger("debug", file)

            text = self.read_crop(file)

            # Sisipkan label di depan hasil OCR crop value sekunder
            # (contoh: crop '3,0K' di bawah pesanan -> 'ulasan 3,0K')
            m = re.search(
                r"text_(\d+)\.jpg$",
                os.path.basename(file)
            )

            if m and int(m.group(1)) in labeled:

                text = labeled[int(m.group(1))] + " " + text

            hasilnya.append(text)
            logger("debug", "isinya : " + text)

        return hasilnya  

if __name__ == "__main__":

    processor = OCRProcessor(
        gpu=False
    )

    data = processor.run("d.jpeg")
    logger("debug", data)
