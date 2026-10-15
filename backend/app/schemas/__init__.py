import datetime as dt

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth / users ----------
class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    phone: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    role: str
    created_at: dt.datetime | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Farms ----------
class FarmCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    location_name: str
    latitude: float
    longitude: float
    size_acres: float = Field(gt=0, default=1.0)
    soil_type: str = "loam"
    water_source: str = "rainfed"


class FarmUpdate(BaseModel):
    name: str | None = None
    location_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    size_acres: float | None = Field(default=None, gt=0)
    soil_type: str | None = None
    water_source: str | None = None


class FarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    location_name: str
    latitude: float
    longitude: float
    size_acres: float
    soil_type: str
    water_source: str
    created_at: dt.datetime | None = None


# ---------- Advisory ----------
class AdvisoryRequest(BaseModel):
    soil_type: str
    season: str | None = None  # long_rains | short_rains | dry; defaults to current month
    water_source: str = "rainfed"
    altitude_m: float | None = None
    farm_size_acres: float | None = None
    avg_temp_c: float | None = None


# ---------- Crop plans / calendar ----------
class CropPlanCreate(BaseModel):
    farm_id: int
    crop_key: str
    planting_date: dt.date
    area_acres: float = Field(gt=0, default=1.0)


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    crop_plan_id: int
    title: str
    description: str | None
    day_offset: int
    due_date: dt.date
    completed: bool
    completed_at: dt.datetime | None


class CropPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    farm_id: int
    crop_key: str
    crop_name: str | None = None
    crop_icon: str | None = None
    planting_date: dt.date
    area_acres: float
    status: str
    activities: list[ActivityOut] = []


class CropPlanStatusUpdate(BaseModel):
    status: str  # active | harvested | abandoned


# ---------- Diseases ----------
class DiagnoseRequest(BaseModel):
    crop_key: str
    symptoms: list[str] = Field(min_length=1)


# ---------- Irrigation ----------
class IrrigationRequest(BaseModel):
    crop_plan_id: int
    soil_moisture_pct: float | None = Field(default=None, ge=0, le=100)
    last_irrigation_days_ago: int | None = Field(default=None, ge=0)


# ---------- Market ----------
class MarketPriceCreate(BaseModel):
    crop_key: str
    market: str
    price_per_kg: float = Field(gt=0)
    currency: str = "KES"
    date: dt.date | None = None


class MarketPriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    crop_key: str
    crop_name: str | None = None
    market: str
    price_per_kg: float
    currency: str
    date: dt.date


# ---------- Finance / analytics ----------
class TransactionCreate(BaseModel):
    farm_id: int
    kind: str  # income | expense
    category: str
    amount: float = Field(gt=0)
    description: str | None = None
    date: dt.date | None = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    farm_id: int
    kind: str
    category: str
    amount: float
    description: str | None
    date: dt.date


class HarvestCreate(BaseModel):
    farm_id: int
    crop_key: str
    quantity_kg: float = Field(gt=0)
    date: dt.date | None = None
    notes: str | None = None


class HarvestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    farm_id: int
    crop_key: str
    crop_name: str | None = None
    quantity_kg: float
    date: dt.date
    notes: str | None
