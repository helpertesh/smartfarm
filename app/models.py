from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    farms = relationship("Farm", back_populates="owner", cascade="all, delete")

class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    farm_name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    soil_type = Column(String, nullable=True)
    size_acres = Column(Numeric(5, 2), nullable=False)
    water_source = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    owner = relationship("User", back_populates="farms")
    crop_plans = relationship("CropPlan", back_populates="farm", cascade="all, delete")
    financial_records = relationship("FinancialRecord", back_populates="farm", cascade="all, delete")
    harvest_records = relationship("HarvestRecord", back_populates="farm", cascade="all, delete")

class CropPlan(Base):
    __tablename__ = "crop_plans"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(50), nullable=False)
    planting_date = Column(Date, nullable=False)
    expected_harvest_date = Column(Date)
    status = Column(String(20), server_default="Active")

    farm = relationship("Farm", back_populates="crop_plans")
    activities = relationship("FarmActivity", back_populates="crop_plan", cascade="all, delete")

class FarmActivity(Base):
    __tablename__ = "farm_activities"

    id = Column(Integer, primary_key=True, index=True)
    crop_plan_id = Column(Integer, ForeignKey("crop_plans.id", ondelete="CASCADE"), nullable=False)
    activity_name = Column(String(100), nullable=False)
    due_date = Column(Date, nullable=False)
    is_completed = Column(Boolean, server_default=text("FALSE"))

    crop_plan = relationship("CropPlan", back_populates="activities")

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    crop_name = Column(String(50), nullable=False)
    price_per_kg = Column(Numeric(10, 2), nullable=False)
    market_location = Column(String(100), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    record_type = Column(String(10), nullable=False)  # 'Revenue' or 'Expense'
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String)
    date = Column(Date, server_default=text("CURRENT_DATE"))

    farm = relationship("Farm", back_populates="financial_records")

class HarvestRecord(Base):
    __tablename__ = "harvest_records"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(50), nullable=False)
    quantity_kg = Column(Numeric(10, 2), nullable=False)
    harvest_date = Column(Date, server_default=text("CURRENT_DATE"))

    farm = relationship("Farm", back_populates="harvest_records")