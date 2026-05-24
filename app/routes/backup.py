import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from tkinter import Tk, filedialog

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.paths import TEMPLATES_DIR, DATA_DIR, UPLOADS_DIR, BACKUP_DIR


router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "journal.db"


def require_login(request: Request):
    return bool(request.session.get("user_id"))


def clean_old_backups():
    for item in BACKUP_DIR.iterdir():
        try:
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception:
            pass


def is_valid_backup_zip(zip_path: Path) -> bool:
    try:
        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()
            return "journal.db" in names
    except Exception:
        return False


def ask_save_location(default_name: str):
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path = filedialog.asksaveasfilename(
        defaultextension=".zip",
        initialfile=default_name,
        filetypes=[("ZIP files", "*.zip")]
    )

    root.destroy()
    return file_path


@router.get("/backup")
def backup_page(request: Request):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    return templates.TemplateResponse(request, "backup.html")


@router.get("/backup/download")
def download_backup(request: Request):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    clean_old_backups()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = BACKUP_DIR / f"TradingJournal_Backup_{timestamp}.zip"

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        if DB_PATH.exists():
            zipf.write(DB_PATH, arcname="journal.db")

        if UPLOADS_DIR.exists():
            for file in UPLOADS_DIR.rglob("*"):
                if file.is_file():
                    zipf.write(file, arcname=f"uploads/{file.relative_to(UPLOADS_DIR)}")

    save_path = ask_save_location(backup_path.name)

    if save_path:
        shutil.copy2(backup_path, save_path)

    return RedirectResponse("/backup", status_code=302)


@router.post("/backup/restore")
def restore_backup(request: Request, backup_file: UploadFile = File(...)):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    if not backup_file.filename.endswith(".zip"):
        return templates.TemplateResponse(
            request,
            "backup.html",
            {"error": "Invalid file type. Please upload a ZIP backup file."}
        )

    temp_restore = BACKUP_DIR / "restore_temp"

    if temp_restore.exists():
        shutil.rmtree(temp_restore)

    temp_restore.mkdir(parents=True, exist_ok=True)

    uploaded_zip = temp_restore / backup_file.filename

    with open(uploaded_zip, "wb") as buffer:
        shutil.copyfileobj(backup_file.file, buffer)

    if not is_valid_backup_zip(uploaded_zip):
        shutil.rmtree(temp_restore)
        return templates.TemplateResponse(
            request,
            "backup.html",
            {"error": "Invalid backup file. journal.db was not found."}
        )

    try:
        with zipfile.ZipFile(uploaded_zip, "r") as zipf:
            zipf.extractall(temp_restore)

        restored_db = temp_restore / "journal.db"

        if restored_db.exists():
            shutil.copy2(restored_db, DB_PATH)

        restored_uploads = temp_restore / "uploads"

        if restored_uploads.exists():
            if UPLOADS_DIR.exists():
                shutil.rmtree(UPLOADS_DIR)

            shutil.copytree(restored_uploads, UPLOADS_DIR)

        shutil.rmtree(temp_restore)

        request.session.clear()
        return RedirectResponse(url="/login", status_code=302)

    except Exception:
        if temp_restore.exists():
            shutil.rmtree(temp_restore)

        return templates.TemplateResponse(
            request,
            "backup.html",
            {"error": "Restore failed. Please close the app, restart it, and try again."}
        )