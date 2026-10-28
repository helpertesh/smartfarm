from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class InputStock(Base):
    """Farm inputs on hand (seed, fertilizer, chemicals) with a reorder level for low-stock alerts."""

    __tablename__ = "input_stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))  # e.g. "DAP fertilizer"
    category: Mapped[str] = mapped_column(String(40))  # seeds | fertilizer | pesticides | animal feed | other
    quantity: Mapped[float] = mapped_column(Float, default=0)
    unit: Mapped[str] = mapped_column(String(20), default="kg")  # kg | litres | bags | packets | units
    reorder_level: Mapped[float] = mapped_column(Float, default=10)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    farm = relationship("Farm", back_populates="inputs")
