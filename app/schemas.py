from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class UserCreate(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    password: str

class UserLogin(BaseModel):
    phone_number: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    name: str
    phone_number: str
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CropAdvisoryRequest(BaseModel):
    location: str
    soil_type: str
    season: str

class CropPlanCreate(BaseModel):
    farm_id: int
    crop_name: str
    planting_date: date

class ActivityResponse(BaseModel):
    activity_name: str
    due_date: date
    is_completed: bool

    class Config:
        from_attributes = True

class CropPlanResponse(BaseModel):
    id: int
    crop_name: str
    planting_date: date
    expected_harvest_date: Optional[date]
    status: str
    activities: List[ActivityResponse] = []

    class Config:
        from_attributes = True

class CropPlanBulkCreate(BaseModel):
    plans: List[CropPlanCreate]

class FarmCreate(BaseModel):
    user_id: int
    farm_name: str
    location: str
    size_acres: float

class FarmResponse(BaseModel):
    id: int
    user_id: int
    farm_name: str
    location: str
    size_acres: float

    class Config:
        from_attributes = True

class FarmBulkCreate(BaseModel):
    farms: List[FarmCreate]

class MarketPriceCreate(BaseModel):
    crop_name: str
    price_per_kg: float
    market_location: str

class MarketPriceResponse(BaseModel):
    id: int
    crop_name: str
    price_per_kg: float
    market_location: str
    updated_at: datetime

    class Config:
        from_attributes = True

class MarketPriceBulkCreate(BaseModel):
    prices: List[MarketPriceCreate]

class DiseaseDiagnosisRequest(BaseModel):
    crop_name: str
    symptom: str

class DiseaseDiagnosisResponse(BaseModel):
    crop_name: str
    symptom: str
    possible_disease: str
    symptoms_description: str
    recommended_action: List[str]

class AlertRequest(BaseModel):
    farmer_id: int
    location: str
    crop_name: str
    current_temperature_c: float
    rainfall_forecast_mm: float
    input_stock_level_kg: float
    upcoming_activity_days: int

class AlertResponse(BaseModel):
    farmer_id: int
    alerts: List[str]
    notification_priority: str
    generated_at: datetime = datetime.now()

    class Config:
        from_attributes = True