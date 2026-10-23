import datetime as dt

from sqlalchemy import Date, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    crop_key: Mapped[str] = mapped_column(String(40), index=True)
    market: Mapped[str] = mapped_column(String(80), index=True)  # e.g. "Nairobi - Wakulima"
    price_per_kg: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(5), default="KES")
    date: Mapped[dt.date] = mapped_column(Date, index=True)
