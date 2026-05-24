import os
from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Trade, TradeImage
from app.paths import TEMPLATES_DIR, TRADE_UPLOAD_DIR


router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

TRADE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def require_login(request: Request):
    return bool(request.session.get("user_id"))


def get_file_extension(file: UploadFile):
    return Path(file.filename).suffix.lower()


def is_valid_image(file: UploadFile):
    return get_file_extension(file) in ALLOWED_IMAGE_EXTENSIONS


def is_valid_size(file: UploadFile):
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    return size <= MAX_IMAGE_SIZE


def make_safe_image_name(file: UploadFile):
    ext = get_file_extension(file)
    if ext == ".jpeg":
        ext = ".jpg"
    return f"{uuid.uuid4().hex}{ext}"


def local_file_from_static_path(static_path: str):
    return TRADE_UPLOAD_DIR.parent.parent / static_path.replace("/static/", "")


def validate_trade_numbers(entry_price, stop_loss, take_profit, lot_size, risk_amount):
    if entry_price <= 0:
        return "Entry price must be greater than zero."
    if stop_loss <= 0:
        return "Stop loss must be greater than zero."
    if take_profit <= 0:
        return "Take profit must be greater than zero."
    if lot_size <= 0:
        return "Lot size must be greater than zero."
    if risk_amount < 0:
        return "Risk amount cannot be negative."
    return None


def save_trade_images(trade_id: int, screenshots: list[UploadFile], db: Session):
    errors = []

    for screenshot in screenshots:
        if not screenshot.filename:
            continue

        if not is_valid_image(screenshot):
            errors.append(f"{screenshot.filename} is not a supported image.")
            continue

        if not is_valid_size(screenshot):
            errors.append(f"{screenshot.filename} is larger than 5MB.")
            continue

        safe_name = make_safe_image_name(screenshot)
        file_path = TRADE_UPLOAD_DIR / safe_name

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(screenshot.file, buffer)

        image = TradeImage(
            trade_id=trade_id,
            image_path=f"/static/uploads/trades/{safe_name}"
        )

        db.add(image)

    db.commit()
    return errors


@router.get("/trades/add")
def add_trade_page(request: Request):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    return templates.TemplateResponse(request, "add_trade.html")


@router.post("/trades/add")
def create_trade(
    request: Request,
    trade_date: str = Form(...),
    symbol: str = Form(...),
    direction: str = Form(...),
    entry_price: float = Form(...),
    stop_loss: float = Form(...),
    take_profit: float = Form(...),
    lot_size: float = Form(...),
    risk_amount: float = Form(...),
    result: str = Form(...),
    profit_loss: float = Form(...),
    strategy: str = Form(""),
    emotion: str = Form(""),
    mistake: str = Form(""),
    notes: str = Form(""),
    screenshots: list[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    error = validate_trade_numbers(entry_price, stop_loss, take_profit, lot_size, risk_amount)

    if error:
        return templates.TemplateResponse(
            request,
            "add_trade.html",
            {"error": error}
        )

    trade = Trade(
        trade_date=trade_date,
        symbol=symbol.strip().upper(),
        direction=direction,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        lot_size=lot_size,
        risk_amount=risk_amount,
        result=result,
        profit_loss=profit_loss,
        strategy=strategy.strip(),
        emotion=emotion.strip(),
        mistake=mistake.strip(),
        notes=notes
    )

    db.add(trade)
    db.commit()
    db.refresh(trade)

    image_errors = save_trade_images(trade.id, screenshots, db)

    if image_errors:
        return templates.TemplateResponse(
            request,
            "trade_detail.html",
            {"trade": trade, "image_error": "Some images were rejected: " + ", ".join(image_errors)}
        )

    return RedirectResponse("/dashboard", status_code=302)


@router.get("/trades/history")
def trade_history(
    request: Request,
    symbol: str = "",
    result: str = "",
    direction: str = "",
    db: Session = Depends(get_db)
):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    query = db.query(Trade)

    if symbol:
        query = query.filter(Trade.symbol.ilike(f"%{symbol.strip()}%"))

    if result:
        query = query.filter(Trade.result == result)

    if direction:
        query = query.filter(Trade.direction == direction)

    trades = query.order_by(Trade.id.desc()).all()

    return templates.TemplateResponse(
        request,
        "history.html",
        {
            "trades": trades,
            "symbol": symbol,
            "result": result,
            "direction": direction
        }
    )


@router.get("/trades/{trade_id}")
def trade_detail(trade_id: int, request: Request, db: Session = Depends(get_db)):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    trade = db.query(Trade).filter(Trade.id == trade_id).first()

    if not trade:
        return RedirectResponse("/trades/history", status_code=302)

    return templates.TemplateResponse(request, "trade_detail.html", {"trade": trade})


@router.post("/trades/{trade_id}/delete")
def delete_trade(trade_id: int, request: Request, db: Session = Depends(get_db)):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    trade = db.query(Trade).filter(Trade.id == trade_id).first()

    if not trade:
        return RedirectResponse("/trades/history", status_code=302)

    for image in trade.images:
        if image.image_path:
            local_path = local_file_from_static_path(image.image_path)
            if os.path.exists(local_path):
                os.remove(local_path)

    db.delete(trade)
    db.commit()

    return RedirectResponse("/trades/history", status_code=302)


@router.get("/trades/{trade_id}/edit")
def edit_trade_page(trade_id: int, request: Request, db: Session = Depends(get_db)):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    trade = db.query(Trade).filter(Trade.id == trade_id).first()

    if not trade:
        return RedirectResponse("/trades/history", status_code=302)

    return templates.TemplateResponse(request, "edit_trade.html", {"trade": trade})


@router.post("/trades/{trade_id}/edit")
def update_trade(
    trade_id: int,
    request: Request,
    trade_date: str = Form(...),
    symbol: str = Form(...),
    direction: str = Form(...),
    entry_price: float = Form(...),
    stop_loss: float = Form(...),
    take_profit: float = Form(...),
    lot_size: float = Form(...),
    risk_amount: float = Form(...),
    result: str = Form(...),
    profit_loss: float = Form(...),
    strategy: str = Form(""),
    emotion: str = Form(""),
    mistake: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    trade = db.query(Trade).filter(Trade.id == trade_id).first()

    if not trade:
        return RedirectResponse("/trades/history", status_code=302)

    error = validate_trade_numbers(entry_price, stop_loss, take_profit, lot_size, risk_amount)

    if error:
        return templates.TemplateResponse(
            request,
            "edit_trade.html",
            {"trade": trade, "error": error}
        )

    trade.trade_date = trade_date
    trade.symbol = symbol.strip().upper()
    trade.direction = direction
    trade.entry_price = entry_price
    trade.stop_loss = stop_loss
    trade.take_profit = take_profit
    trade.lot_size = lot_size
    trade.risk_amount = risk_amount
    trade.result = result
    trade.profit_loss = profit_loss
    trade.strategy = strategy.strip()
    trade.emotion = emotion.strip()
    trade.mistake = mistake.strip()
    trade.notes = notes

    db.commit()

    return RedirectResponse(f"/trades/{trade.id}", status_code=302)


@router.post("/trades/{trade_id}/images/add")
def add_trade_images(
    trade_id: int,
    request: Request,
    screenshots: list[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    trade = db.query(Trade).filter(Trade.id == trade_id).first()

    if not trade:
        return RedirectResponse("/trades/history", status_code=302)

    image_errors = save_trade_images(trade.id, screenshots, db)

    if image_errors:
        return templates.TemplateResponse(
            request,
            "trade_detail.html",
            {"trade": trade, "image_error": "Some images were rejected: " + ", ".join(image_errors)}
        )

    return RedirectResponse(f"/trades/{trade.id}", status_code=302)


@router.post("/trades/images/{image_id}/delete")
def delete_trade_image(
    image_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    if not require_login(request):
        return RedirectResponse("/login", status_code=302)

    image = db.query(TradeImage).filter(TradeImage.id == image_id).first()

    if not image:
        return RedirectResponse("/trades/history", status_code=302)

    trade_id = image.trade_id

    if image.image_path:
        local_path = local_file_from_static_path(image.image_path)
        if os.path.exists(local_path):
            os.remove(local_path)

    db.delete(image)
    db.commit()

    return RedirectResponse(f"/trades/{trade_id}", status_code=302)