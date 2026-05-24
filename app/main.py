from datetime import date
import secrets
import calendar
from collections import defaultdict, Counter

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine, SessionLocal
from app import models  # noqa: F401
from app.models import User, Trade
from app.routes import auth, trades, profile, export, backup
from app.paths import STATIC_DIR, TEMPLATES_DIR


app = FastAPI(title="Trading Journal")

SESSION_SECRET = secrets.token_hex(32)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET
)

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.include_router(auth.router)
app.include_router(trades.router)
app.include_router(profile.router)
app.include_router(export.router)
app.include_router(backup.router)


@app.get("/")
def home():
    db = SessionLocal()
    user = db.query(User).first()
    db.close()

    if not user:
        return RedirectResponse(url="/setup")

    return RedirectResponse(url="/login")


@app.get("/dashboard")
def dashboard(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    db = SessionLocal()
    all_trades = db.query(Trade).all()
    db.close()

    total_trades = len(all_trades)

    winning_trades = [t for t in all_trades if t.result == "TP"]
    losing_trades = [t for t in all_trades if t.result == "SL"]

    total_wins = len(winning_trades)
    total_losses = len(losing_trades)

    win_rate = round((total_wins / total_trades) * 100, 2) if total_trades > 0 else 0
    total_pl = round(sum(t.profit_loss or 0 for t in all_trades), 2)

    profits = [t.profit_loss for t in all_trades if t.profit_loss is not None]
    winning_profits = [p for p in profits if p > 0]
    losing_profits = [p for p in profits if p < 0]

    best_trade = max(winning_profits) if winning_profits else 0
    worst_trade = min(losing_profits) if losing_profits else 0

    symbols = [t.symbol for t in all_trades if t.symbol]
    most_traded_symbol = Counter(symbols).most_common(1)[0][0] if symbols else "N/A"

    mistake_stats = {}

    for t in all_trades:
        if t.mistake:
            if t.mistake not in mistake_stats:
                mistake_stats[t.mistake] = {"count": 0, "loss": 0}

            mistake_stats[t.mistake]["count"] += 1

            if (t.profit_loss or 0) < 0:
                mistake_stats[t.mistake]["loss"] += abs(t.profit_loss)

    biggest_mistake = max(
        mistake_stats.items(),
        key=lambda x: x[1]["count"],
        default=("N/A", {})
    )[0]

    rr_values = []

    for t in all_trades:
        try:
            if t.direction == "Buy":
                risk = abs(t.entry_price - t.stop_loss)
                reward = abs(t.take_profit - t.entry_price)
            else:
                risk = abs(t.stop_loss - t.entry_price)
                reward = abs(t.entry_price - t.take_profit)

            if risk > 0:
                rr_values.append(reward / risk)
        except Exception:
            pass

    average_rr = round(sum(rr_values) / len(rr_values), 2) if rr_values else 0

    strategy_data = {}

    for t in all_trades:
        strategy = t.strategy or "No Strategy"

        if strategy not in strategy_data:
            strategy_data[strategy] = {
                "trades": 0,
                "profit_loss": 0,
                "wins": 0
            }

        strategy_data[strategy]["trades"] += 1
        strategy_data[strategy]["profit_loss"] += t.profit_loss or 0

        if t.result == "TP":
            strategy_data[strategy]["wins"] += 1

    for strategy in strategy_data:
        trades_count = strategy_data[strategy]["trades"]
        wins = strategy_data[strategy]["wins"]

        strategy_data[strategy]["profit_loss"] = round(
            strategy_data[strategy]["profit_loss"], 2
        )

        strategy_data[strategy]["win_rate"] = round(
            (wins / trades_count) * 100, 2
        ) if trades_count > 0 else 0

    recent_trades = sorted(all_trades, key=lambda x: x.id, reverse=True)[:5]

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "total_trades": total_trades,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "win_rate": win_rate,
            "total_pl": total_pl,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "most_traded_symbol": most_traded_symbol,
            "biggest_mistake": biggest_mistake,
            "average_rr": average_rr,
            "strategy_data": strategy_data,
            "mistake_stats": mistake_stats,
            "recent_trades": recent_trades
        }
    )


@app.get("/calendar")
def calendar_page(request: Request, year: int = None, month: int = None):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    today = date.today()

    if year is None:
        year = today.year

    if month is None:
        month = today.month

    db = SessionLocal()
    all_trades = db.query(Trade).all()
    db.close()

    trades_by_date = defaultdict(list)

    for trade in all_trades:
        trades_by_date[trade.trade_date].append(trade)

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdatescalendar(year, month)

    prev_month = month - 1
    prev_year = year

    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year

    if next_month == 13:
        next_month = 1
        next_year += 1

    return templates.TemplateResponse(
        request,
        "calendar.html",
        {
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "month_days": month_days,
            "trades_by_date": trades_by_date,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "today": today.isoformat()
        }
    )


@app.get("/calendar/day/{trade_date}")
def calendar_day_view(trade_date: str, request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)

    db = SessionLocal()
    trades_for_day = db.query(Trade).filter(Trade.trade_date == trade_date).all()
    db.close()

    return templates.TemplateResponse(
        request,
        "calendar_day.html",
        {
            "trade_date": trade_date,
            "trades": trades_for_day
        }
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected"}