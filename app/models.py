from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    username = Column(String(150), unique=True, index=True, nullable=False)
    profile_photo = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)

    trade_date = Column(String(20), nullable=False)
    symbol = Column(String(50), nullable=False)
    direction = Column(String(20), nullable=False)

    entry_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    lot_size = Column(Float)
    risk_amount = Column(Float)

    result = Column(String(30))
    profit_loss = Column(Float)

    strategy = Column(String(150))
    emotion = Column(String(150))
    mistake = Column(String(150))
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    images = relationship(
        "TradeImage",
        back_populates="trade",
        cascade="all, delete-orphan"
    )


class TradeImage(Base):
    __tablename__ = "trade_images"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)
    image_path = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    trade = relationship("Trade", back_populates="images")