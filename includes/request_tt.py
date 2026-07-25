# File : includes\request_tt.py
import time, os, random, re, json
import requests
import traceback

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from seleniumbase import Driver
from selenium.webdriver.common.by import By
from includes.logFX import logger
from includes.image_helper_tt import download_product_images


def create_driver(profile_path=None):

    # =========================
    # ENSURE PROFILE EXISTS
    # =========================
    if profile_path:
        os.makedirs(profile_path, exist_ok=True)

    # =========================
    # USER AGENT STORAGE
    # =========================
    agent_file = None

    if profile_path:
        agent_file = os.path.join(
            profile_path,
            "agent.txt"
        )

    # =========================
    # USER AGENT LIST
    # =========================
    user_agents = [

        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36",

        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36",

        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36",

        # Edge Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
    ]

    # =========================
    # LOAD / CREATE AGENT
    # =========================
    agent = None

    try:

        # load existing agent
        if agent_file and os.path.exists(agent_file):

            with open(agent_file, "r", encoding="utf-8") as f:

                agent = f.read().strip()

                logger("info", "LOAD AGENT:" + agent)
                
        # create new random agent
        if not agent:

            agent = random.choice(user_agents)

            logger("info", "NEW AGENT:" + agent)

            if agent_file:

                with open(agent_file, "w", encoding="utf-8") as f:

                    f.write(agent)

    except Exception as e:

        logger("error", "AGENT LOAD ERROR:", e)

        # fallback
        agent = random.choice(user_agents)

    # =========================
    # CREATE UC DRIVER
    # =========================
    driver = Driver(
        uc=True,
        headless=False,
        user_data_dir=profile_path,
        agent=agent
    )

    # =========================
    # MAXIMIZE
    # =========================
    driver.maximize_window()

    # =========================
    # PAGE TIMEOUT
    # =========================
    driver.set_page_load_timeout(60)

    # =========================
    # EXTRA STEALTH PATCHES
    # =========================
    driver.execute_script("""
    
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });

        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

    """)

    # =========================
    # PRINT ACTIVE AGENT
    # =========================
    try:

        active_agent = driver.execute_script(
            "return navigator.userAgent;"
        )

        logger("info", "ACTIVE AGENT:", active_agent)

    except:
        pass

    return driver

def get_info_tt_from_url(url, profile_path):

    driver = None

    try:

        logger("debug", "=" * 80)
        logger("debug", "CREATE DRIVER")

        driver = create_driver(profile_path=profile_path)

        logger("debug", "=" * 80)
        logger("debug", "OPEN URL")

        driver.get(url)

        # WebDriverWait(driver, 30).until(
        #     EC.presence_of_element_located((By.TAG_NAME, "body"))
        # )
        WebDriverWait(driver, 30).until(
            lambda d: '"seller_id":' in d.page_source
        )

        # ====================================================
        # TITLE
        # ====================================================

        title = ""

        try:

            elem = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        'span[data-fmp="true"]'
                    )
                )
            )

            title = elem.text.strip()

            logger("debug", "TITLE :", title)

        except Exception:

            logger("error", "TITLE NOT FOUND")

        # ====================================================
        # PRICE
        # ====================================================

        price = ""

        try:

            price = driver.find_element(
                By.XPATH,
                "//span[text()='Rp']/following-sibling::span"
            ).text.strip()
            price = price.replace(".", "")
            logger("debug", "PRICE :", price)

        except Exception:

            logger("error", "PRICE NOT FOUND")

        # ====================================================
        # RATING / VOTE / SOLD
        # ====================================================

        rating = ""
        vote = ""
        sold = ""

        try:

            sold_span = driver.find_element(
                By.XPATH,
                "//span[contains(text(),'sold')]"
            )

            info = sold_span.find_element(
                By.XPATH,
                "./ancestor::div[contains(@class,'flex-row')]"
            )

            # -------------------------------
            # SOLD
            # -------------------------------

            sold = sold_span.text.replace("sold", "").strip()

            # -------------------------------
            # RATING & VOTE
            # -------------------------------

            try:

                rating_block = info.find_element(
                    By.XPATH,
                    ".//div[contains(@class,'flex-row')][1]"
                )

                spans = rating_block.find_elements(
                    By.XPATH,
                    ".//span[normalize-space()]"
                )

                values = [s.text.strip() for s in spans]

                logger("debug", f"RATING INFO : {values}")

                if len(values) >= 1 and "sold" not in values[0].lower():
                    rating = values[0]

                if len(values) >= 2:
                    vote = values[1]

            except Exception:
                # Produk baru biasanya hanya punya sold
                pass

        except Exception as e:

            logger("error", "RATING BLOCK ERROR")
            logger("error", str(e))
        # ====================================================
        # DESCRIPTION
        # ====================================================

        description = ""

        try:

            h3 = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//h3[contains(.,'Product description')]"
                    )
                )
            )

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                h3
            )

            time.sleep(random.uniform(1.5, 2.5))

            container = h3.find_element(
                By.XPATH,
                "./ancestor::div[contains(@class,'expandableSection')]"
            )

            spans = container.find_elements(By.TAG_NAME, "span")

            texts = []

            for span in spans:

                txt = span.text.strip()

                if not txt:
                    continue

                if txt == title:
                    continue

                texts.append(txt)

            description = "\n".join(texts)

            logger("debug", "DESCRIPTION :", len(description), "chars")

        except Exception as e:

            logger("error", "DESCRIPTION ERROR")
            logger("error", e)
        
        
        # mendapatkan html doom
        html = driver.page_source

        # ====================================================
        # id produk tiktok
        # ====================================================
        tiktok_product_id = ""
        try:
            

            match = re.search(
                r'"route_product_id":"(\d+)"',
                html
            )

            if match:
                tiktok_product_id = match.group(1)
            else:
                tiktok_product_id = ""
        except Exception:
            logger("error", "GAGAL AMBIL TIKTOK ID PRODUK   ")

        # ====================================================
        # mengambil url images
        # ====================================================
        match = re.search(
            r'"images":(\[.*?\]),"sale_properties"',
            html,
            re.DOTALL
        )

        if match:

            images = json.loads(match.group(1))

            download_product_images(
                images,
                tiktok_product_id
            )

            jsonimages = match.group(1)

            with open("./images.txt", "w", encoding="utf-8") as f:
                f.write(jsonimages)

            logger("debug", "IMAGES DUMP -> ./images.txt")

        else:

            logger("error", "IMAGES NOT FOUND")

        # ====================================================
        # SAVE PAGE SOURCE
        # ====================================================

        debug_folder = os.path.join(
            "debug",
            "products",
            tiktok_product_id
        )

        os.makedirs(debug_folder, exist_ok=True)

        with open(
            os.path.join(debug_folder, "page_source.html"),
            "w",
            encoding="utf-8"
        ) as f:
            f.write(html)

        logger("debug", f"PAGE SOURCE SAVED : {debug_folder}/page_source.html")


        # ====================================================
        # RESULT
        # ====================================================

        returnx = {
            "tiktok_id_product": tiktok_product_id,

            "title": title,

            "description": description,

            "price": price,

            "rating": rating,

            "vote": vote,

            "sold": sold

        }
        logger("debug", returnx)

        success = all([
            returnx["title"],
            returnx["description"],
            returnx["price"],
            returnx["rating"],
            returnx["vote"],
            returnx["sold"]
        ])
    
        if success:
            logger("debug", "=" * 80)
            logger("debug", "SEMUA DATA BERHASIL DIAMBIL")
            driver.quit()
            driver = None

        return returnx
    
    except Exception:

        traceback.print_exc()

        return None

    finally:

        if driver:
            driver.quit()

if __name__ == "__main__":
    URL = "https://vt.tokopedia.com/t/ZS963QwDASepA-RsAQY/"

    profile_path = r"J:\Tiktok_Affiliate_Analyse\chromium"
    hasil = get_info_tt_from_url(URL, profile_path)

    logger("debug", hasil)