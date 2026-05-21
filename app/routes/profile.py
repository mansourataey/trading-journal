from pathlib import Path
import shutil
import os
import uuid

from fastapi import APIRouter, Request, Form, UploadFile, File, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PROFILE_UPLOAD_DIR = Path("app/static/uploads/profile")
PROFILE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def require_login(request: Request):
    return bool(request.session.get("user_id"))


def password_too_long(password: str) -> bool:
    return len(password.encode("utf-8")) > 72


def password_is_weak(password: str) -> bool:
    return len(password) < 8


def unique_filename(original_name: str) -> str:
    ext = Path(original_name).suffix
    return f"{uuid.uuid4().hex}{ext}"


@router.get("/profile")
def profile_page(request: Request, db: Session = Depends(get_db)):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    user_id = request.session.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    return templates.TemplateResponse(request, "profile.html", {"user": user})


@router.post("/profile/update")
def update_profile(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    profile_photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    user_id = request.session.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    full_name = full_name.strip()
    username = username.strip()

    if not full_name or not username:
        return templates.TemplateResponse(
            request,
            "profile.html",
            {"user": user, "profile_error": "Full name and username cannot be empty."}
        )

    username_exists = (
        db.query(User)
        .filter(User.username == username, User.id != user.id)
        .first()
    )

    if username_exists:
        return templates.TemplateResponse(
            request,
            "profile.html",
            {"user": user, "profile_error": "This username is already used."}
        )

    user.full_name = full_name
    user.username = username

    if profile_photo and profile_photo.filename:
        if user.profile_photo:
            old_path = "app" + user.profile_photo
            if os.path.exists(old_path):
                os.remove(old_path)

        safe_name = unique_filename(profile_photo.filename)
        file_path = PROFILE_UPLOAD_DIR / safe_name

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(profile_photo.file, buffer)

        user.profile_photo = f"/static/uploads/profile/{safe_name}"

    db.commit()

    return templates.TemplateResponse(
        request,
        "profile.html",
        {"user": user, "profile_success": "Profile updated successfully."}
    )


@router.post("/profile/change-password")
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    user_id = request.session.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not pwd_context.verify(current_password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "profile.html",
            {"user": user, "password_error": "Current password is incorrect."}
        )

    if new_password != confirm_password:
        return templates.TemplateResponse(
            request,
            "profile.html",
            {"user": user, "password_error": "New passwords do not match."}
        )

    if password_too_long(new_password):
        return templates.TemplateResponse(
            request,
            "profile.html",
            {"user": user, "password_error": "New password is too long."}
        )

    if password_is_weak(new_password):
        return templates.TemplateResponse(
            request,
            "profile.html",
            {"user": user, "password_error": "Password must be at least 8 characters."}
        )

    user.password_hash = pwd_context.hash(new_password)
    db.commit()

    return templates.TemplateResponse(
        request,
        "profile.html",
        {"user": user, "password_success": "Password updated successfully."}
    )