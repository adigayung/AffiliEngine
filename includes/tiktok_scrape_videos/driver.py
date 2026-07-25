"""
Modul driver untuk membuat seleniumbase Driver dengan:
- uc=True (undetected-chromedriver)
- persistent user_data_dir
- random/persistent user agent
- stealth patch
- window maximize
"""

import os
import random
import logging
from seleniumbase import Driver

logger = logging.getLogger(__name__)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
]


def create_driver(profile_path=None):
    """
    Membuat seleniumbase Driver dengan persistent profile.

    Args:
        profile_path: Path ke folder profile Chromium.
                      Jika None, temporary profile.

    Returns:
        seleniumbase Driver instance
    """
    if profile_path:
        os.makedirs(profile_path, exist_ok=True)

    agent_file = os.path.join(profile_path, "agent.txt") if profile_path else None

    # Load atau buat agent
    agent = None
    try:
        if agent_file and os.path.exists(agent_file):
            with open(agent_file, "r", encoding="utf-8") as f:
                agent = f.read().strip()
            logger.info("LOAD AGENT: %s", agent)

        if not agent:
            agent = random.choice(_USER_AGENTS)
            logger.info("NEW AGENT: %s", agent)
            if agent_file:
                with open(agent_file, "w", encoding="utf-8") as f:
                    f.write(agent)
    except Exception as e:
        logger.error("AGENT ERROR: %s", e)
        agent = random.choice(_USER_AGENTS)

    driver = Driver(
        uc=True,
        headless=False,
        user_data_dir=profile_path,
        agent=agent,
    )
    driver.maximize_window()
    driver.set_page_load_timeout(60)

    # Stealth patches
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    """)

    try:
        active = driver.execute_script("return navigator.userAgent;")
        logger.info("ACTIVE AGENT: %s", active)
    except Exception:
        pass

    return driver
