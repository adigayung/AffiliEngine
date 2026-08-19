"""
exceptions.py — Exception khusus untuk Facebook uploader.
"""


class FacebookUploaderError(Exception):
    """Base error untuk seluruh alur Facebook uploader."""


class AffiliateSaveError(FacebookUploaderError):
    """Gagal pada alur affiliate (dialog/URL/Link name/Save)."""


class WrongSaveError(AffiliateSaveError):
    """Save yang diklik ternyata Save form utama (accidental publish/draft)."""


class SchedulingError(FacebookUploaderError):
    """Gagal pada alur scheduling (Date/Time/Schedule for later/final Schedule)."""
