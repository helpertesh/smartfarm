from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    location_name: Mapped[str] = mapped_column(String(120))  # e.g. "Nyeri"
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    size_acres: Mapped[float] = mapped_column(Float, default=1.0)
    soil_type: Mapped[str] = mapped_column(String(40), default="loam")  # loam|clay|sandy|black cotton|volcanic
    water_source: Mapped[str] = mapped_column(String(40), default="rainfed")  # rainfed|irrigation|both
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="farms")
    crop_plans = relationship("CropPlan", back_populates="farm", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="farm", cascade="all, delete-orphan")
    harvests = relationship("Harvest", back_populates="farm", cascade="all, delete-orphan")
