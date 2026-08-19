# File: includes/browser.py

from includes.tiktok_scrape_videos.driver import create_driver


DEFAULT_PROFILE_PATH = "./chromium"


def open_browser(
    profile_path: str = DEFAULT_PROFILE_PATH,
    url: str | None = None
):
    """
    Membuka Chromium menggunakan profile yang diberikan.

    Args:
        profile_path:
            Lokasi profile Chromium.

        url:
            URL yang langsung dibuka setelah browser berjalan.
            Jika None, browser tidak membuka URL apa pun.

    Returns:
        Selenium WebDriver
    """

    print("Membuka Chromium...")

    driver = create_driver(
        profile_path=profile_path
    )

    print("Chromium berhasil dibuka.")

    if url:
        driver.get(url)

    return driver


def close_browser(driver):
    """
    Menutup browser.
    """

    if driver is None:
        return

    try:
        driver.quit()
        print("Browser ditutup.")
    except Exception as e:
        print(f"Gagal menutup browser: {e}")


def wait_for_manual_action(
    message: str = "Tekan ENTER setelah selesai..."
):
    """
    Menunggu user melakukan sesuatu secara manual
    di browser.
    """

    print()
    print("=" * 60)
    print(message)
    print("=" * 60)
    print()

    input(">>> ")


def open_browser_manual(
    profile_path: str = DEFAULT_PROFILE_PATH,
    url: str | None = None,
    message: str = "Silakan lakukan proses secara manual, lalu tekan ENTER."
):
    """
    Membuka browser dan menunggu proses manual user selesai.

    Returns:
        Selenium WebDriver
    """

    driver = open_browser(
        profile_path=profile_path,
        url=url
    )

    wait_for_manual_action(message)

    return driver


if __name__ == "__main__":

    driver = open_browser()

    print()
    print("=" * 60)
    print("BROWSER BERHASIL DIBUKA")
    print("=" * 60)
    print()
    print("Browser tetap terbuka.")
    print("Tekan CTRL+C untuk menutup.")

    try:
        while True:
            input()

    except KeyboardInterrupt:
        print("\nMenutup browser...")
        close_browser(driver)