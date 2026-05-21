from pathlib import Path
import shutil

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

UPLOAD_DIR = Path("app/static/uploads/profile")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()


def password_too_long(password: str) -> bool:
    return len(password.encode("utf-8")) > 72


@router.get("/setup")
def setup_page(request: Request, db: Session = Depends(get_db)):
    existing_user = db.query(User).first()

    if existing_user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(request, "setup.html")


@router.post("/setup")
def create_first_user(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    profile_photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).first()

    if existing_user:
        return RedirectResponse(url="/login", status_code=302)

    if password != confirm_password:
        return templates.TemplateResponse(
            request,
            "setup.html",
            {"error": "Passwords do not match"}
        )

    if password_too_long(password):
        return templates.TemplateResponse(
            request,
            "setup.html",
            {"error": "Password is too long. Please use a shorter password."}
        )

    photo_path = None

    if profile_photo and profile_photo.filename:
        file_path = UPLOAD_DIR / profile_photo.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(profile_photo.file, buffer)

        photo_path = f"/static/uploads/profile/{profile_photo.filename}"

    hashed_password = pwd_context.hash(password)

    user = User(
        full_name=full_name.strip(),
        username=username.strip(),
        profile_photo=photo_path,
        password_hash=hashed_password
    )

    db.add(user)
    db.commit()

    return RedirectResponse(url="/login", status_code=302)


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    existing_user = db.query(User).first()

    if not existing_user:
        return RedirectResponse(url="/setup", status_code=302)

    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password_too_long(password):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid username or password"}
        )

    user = db.query(User).filter(User.username == username.strip()).first()

    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid username or password"}
        )

    if not pwd_context.verify(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid username or password"}
        )

    request.session["user_id"] = user.id

    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)