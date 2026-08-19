"""
selectors.py — Selector/XPath dan konstanta lokator Facebook.

Diambil PERSIS dari main.py golden version tanpa mengubah nilai apa pun.
JANGAN mengubah selector ini tanpa regression test penuh.
"""

import re

# --- Halaman utama Reels / composer ---
XPATH_CREATE_REEL = "//*[normalize-space(.)='Create reel']"
XPATH_VIDEO_INPUT = "//input[@type='file' and contains(@accept, 'video')]"
XPATH_SAFE_PUBLISH = "//*[normalize-space(.)='Your reel is safe to publish!']"
XPATH_NEXT = "//*[@role='button' and @aria-label='Next']"
XPATH_EDIT_STEP = "//*[normalize-space(.)='Edit reel']"
XPATH_CAPTION = "//div[@contenteditable='true' and @role='textbox' and @aria-placeholder='Describe your reel...']"

# --- Affiliate ---
XPATH_AI_LABEL = "//input[@aria-label='Add AI label']"
XPATH_ADD_PRODUCT = "//*[normalize-space(.)='Add a product to your reel so people can shop for what they see.']"
XPATH_AFFILIATE_DIALOG = "//div[@role='dialog' and .//*[normalize-space(.)='Add affiliate product']]"
XPATH_DIALOG_PRODUCT_LINK = "//*[normalize-space(.)='Add a product link']"
XPATH_URL_INPUT = "//label[.//span[normalize-space(.)='URL']]//input[@type='text']"
XPATH_LINK_NAME_INPUT = "//label[.//span[contains(normalize-space(.), 'Link name')]]//input[@type='text']"
# Save affiliate HARUS role=button + visible + enabled. Jangan pakai teks global.
XPATH_SAVE = "//*[@role='button' and @aria-label='Save']"

# --- Scheduling ---
XPATH_SCHED_OPT = "//*[@role='button' and contains(normalize-space(.), 'Scheduling options')]"
XPATH_SCHED_DLG = "//*[@role='dialog' and .//*[@aria-label='Schedule for later']]"
XPATH_SCHED_LATER = "//*[@role='dialog' and .//*[@aria-label='Schedule for later']]//*[@aria-label='Schedule for later']"
XPATH_FINAL_SCHEDULE = "//*[@role='button' and @aria-label='Schedule']"

# Pola value input Date (mis. "20 Aug 2026") dan Time (mis. "11:00").
_DATE_VALUE_RE = re.compile(r"^\d{1,2} [A-Za-z]{3} \d{4}$")
_TIME_VALUE_RE = re.compile(r"^\d{1,2}:\d{2}$")

_UPLOAD_KEYWORDS = (
    "select video",
    "add video",
    "upload video",
    "choose video",
    "drag and drop",
)

_PLACEHOLDER_PREVIEW = "upload your video in order to see a preview here"
