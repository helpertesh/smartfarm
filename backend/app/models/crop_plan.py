import datetime as dt

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CropPlan(Base):
    """A crop planted on a farm on a given date. Generates calendar activities."""

    __tablename__ = "crop_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), index=True)
    crop_key: Mapped[str] = mapped_column(String(40))  # e.g. "maize"
    planting_date: Mapped[dt.date] = mapped_column(Date)
    area_acres: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|harvested|abandoned
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farm = relationship("Farm", back_populates="crop_plans")
    activities = relationship(
        "FarmActivity", back_populates="crop_plan", cascade="all, delete-orphan", order_by="FarmActivity.due_date"
    )


class FarmActivity(Base):
    __tablename__ = "farm_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    crop_plan_id: Mapped[int] = mapped_column(ForeignKey("crop_plans.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    day_offset: Mapped[int] = mapped_column(Integer)
    due_date: Mapped[dt.date] = mapped_column(Date, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    crop_plan = relationship("CropPlan", back_populates="activities")
