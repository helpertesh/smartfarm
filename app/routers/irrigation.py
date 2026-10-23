from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import Farm, CropPlan

router = APIRouter(prefix="/irrigation", tags=["Smart Irrigation"])

class IrrigationCheckRequest(BaseModel):
    farm_id: int
    crop_name: str

class IrrigationResponse(BaseModel):
    farm_id: int
    farm_name: str
    location: str
    crop_name: str
    recommended_action: str
    water_volume_liters_per_acre: float
    reason: str

@router.post("/schedule", response_model=IrrigationResponse)
def get_irrigation_recommendation(data: IrrigationCheckRequest, db: Session = Depends(get_db)):
    # 1. Fetch farm details
    farm = db.query(Farm).filter(Farm.id == data.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    location = farm.location.lower().strip()
    
    # 2. Determine base water needs per acre based on crop type
    crop_lower = data.crop_name.lower()
    base_water = 4000.0  # default liters per acre
    if "tomato" in crop_lower:
        base_water = 5500.0
    elif "maize" in crop_lower:
        base_water = 4500.0
    elif "sorghum" in crop_lower or "millet" in crop_lower:
        base_water = 2500.0
    elif "rice" in crop_lower:
        base_water = 8000.0
        
    # 3. Simulate or fetch weather forecast for the location
    # (In a full weather integration, this calls your weather service endpoint)
    rainy_locations = ["kisumu", "kakamega", " nyeri"] # Simulated rainy regions
    is_raining_forecast = location in rainy_locations
    
    if is_raining_forecast:
        action = "Skip Irrigation"
        reason = f"Rainfall is forecasted in {farm.location.capitalize()}. Natural precipitation is sufficient for your {data.crop_name}."
        adjusted_water = 0.0
    else:
        action = "Proceed with Irrigation"
        reason = f"Dry conditions expected in {farm.location.capitalize()}. Standard irrigation recommended."
        adjusted_water = base_water * farm.size_acres
        
    return {
        "farm_id": farm.id,
        "farm_name": farm.farm_name,
        "location": farm.location,
        "crop_name": data.crop_name,
        "recommended_action": action,
        "water_volume_liters_per_acre": adjusted_water,
        "reason": reason
    }