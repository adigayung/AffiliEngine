from includes.tiktok_scrape_videos.driver import create_driver

PROFILE_PATH = "./chromium"

print("Membuka Chromium...")

driver = create_driver(
    profile_path=PROFILE_PATH
)

print("Chromium berhasil dibuka.")

driver.get("https://shopee.co.id/")

print()
print("=" * 60)
print("SILAKAN LOGIN SHOPEE")
print("=" * 60)
print()
print("Login secara manual.")
print("Setelah selesai, tekan ENTER di terminal.")
print()

input(">>> ")

print()
print("Login selesai.")
print("Profile:", PROFILE_PATH)
print()
print("Browser tetap terbuka.")
print("Tekan CTRL+C untuk menutup.")

try:
    while True:
        input()
except KeyboardInterrupt:
    print("\nMenutup browser...")
    driver.quit()