from pathlib import Path
import sys


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "app"
    return Path(__file__).resolve().parent


APP_DIR = app_dir()

TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"
DATA_DIR = APP_DIR / "data"

UPLOADS_DIR = STATIC_DIR / "uploads"
TRADE_UPLOAD_DIR = UPLOADS_DIR / "trades"
PROFILE_UPLOAD_DIR = UPLOADS_DIR / "profile"
EXPORT_DIR = STATIC_DIR / "exports"
BACKUP_DIR = STATIC_DIR / "backups"