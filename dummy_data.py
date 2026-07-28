def get_data():
    data = [
        # ---------- MANJA DRESS (target: Momentum #1) ----------
        # 2 video, 2 creator, growth stabil dan tinggi
        {
            "product": "Manja Dress",
            "video_id": "M1",
            "creator": "Creator A",
            "daily_views": [
                1000,      # hari 1
                3000,      # hari 2
                8000,      # hari 3
                15000,     # hari 4
                40000,     # hari 5
                80000,     # hari 6
                150000,    # hari 7
                250000,    # hari 8
                400000,    # hari 9
                600000     # hari 10
            ]
        },
        {
            "product": "Manja Dress",
            "video_id": "M2",
            "creator": "Creator B",
            "daily_views": [
                500,
                2000,
                5000,
                12000,
                30000,
                60000,
                100000,
                180000,
                250000,
                350000
            ]
        },

        # ---------- ZORA DRESS (target: Momentum #2) ----------
        # 2 video, 2 creator, growth bagus tapi tidak sekuat Manja
        {
            "product": "Zora Dress",
            "video_id": "Z1",
            "creator": "Creator C",
            "daily_views": [
                2000,
                5000,
                12000,
                25000,
                50000,
                90000,
                150000,
                240000,
                360000,
                500000
            ]
        },
        {
            "product": "Zora Dress",
            "video_id": "Z2",
            "creator": "Creator D",
            "daily_views": [
                1000,
                3000,
                7000,
                15000,
                30000,
                55000,
                90000,
                140000,
                200000,
                280000
            ]
        },

        # ---------- SAKURA SET (target: Momentum #3) ----------
        # 3 video, 3 creator, tapi growth kecil/linear
        {
            "product": "Sakura Set",
            "video_id": "S1",
            "creator": "Creator E",
            "daily_views": [
                5000,
                6000,
                8000,
                11000,
                15000,
                20000,
                26000,
                33000,
                40000,
                48000
            ]
        },
        {
            "product": "Sakura Set",
            "video_id": "S2",
            "creator": "Creator F",
            "daily_views": [
                3000,
                4000,
                6000,
                9000,
                12000,
                16000,
                21000,
                27000,
                34000,
                42000
            ]
        },
        {
            "product": "Sakura Set",
            "video_id": "S3",
            "creator": "Creator G",
            "daily_views": [
                2000,
                3000,
                5000,
                7000,
                10000,
                14000,
                18000,
                23000,
                29000,
                36000
            ]
        },

            # ---------- SPIKE PRODUCT (target: Discovery #1, Momentum #4) ----------
        # Hanya 1 video, growth besar di akhir, tapi kena penalty berat
        # Growth besar tapi tidak ekstrem sampai mengalahkan penalty 0.25
        {
            "product": "Spike Product",
            "video_id": "P1",
            "creator": "Creator H",
            "daily_views": [
                1000,
                2000,
                3000,
                5000,
                10000,
                20000,
                50000,
                100000,
                250000,
                500000
            ]
        },

        # ---------- OLD VIRAL PRODUCT (target: Momentum #5) ----------
        # Pernah viral tapi growth sudah melandai
        {
            "product": "Old Viral Product",
            "video_id": "O1",
            "creator": "Creator I",
            "daily_views": [
                50000,
                100000,
                300000,
                600000,
                900000,
                1100000,
                1200000,
                1250000,
                1280000,
                1300000
            ]
        },

        # ---------- BELLA BLOUSE (random tambahan) ----------
        # Produk kecil dengan growth stabil
        {
            "product": "Bella Blouse",
            "video_id": "B1",
            "creator": "Creator J",
            "daily_views": [
                300,
                800,
                2000,
                4000,
                8000,
                15000,
                25000,
                40000,
                60000,
                90000
            ]
        },
        {
            "product": "Bella Blouse",
            "video_id": "B2",
            "creator": "Creator K",
            "daily_views": [
                200,
                500,
                1000,
                2000,
                4000,
                8000,
                12000,
                18000,
                25000,
                35000
            ]
        },

        # ---------- GLAMOUR HEELS (random tambahan) ----------
        # Produk dengan 1 video, growth sedang
        {
            "product": "Glamour Heels",
            "video_id": "G1",
            "creator": "Creator L",
            "daily_views": [
                100,
                400,
                1500,
                5000,
                12000,
                25000,
                50000,
                80000,
                120000,
                160000
            ]
        },
    ]
    return data