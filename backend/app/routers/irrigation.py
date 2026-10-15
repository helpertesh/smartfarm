from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.crop_plan import CropPlan
from app.models.farm import Farm
from app.models.user import User
from app.routers.farms import get_owned_farm
from app.schemas import IrrigationRequest
from app.services.irrigation import irrigation_advice
from app.services.weather import fetch_weather

router = APIRouter(prefix="/api/irrigation", tags=["irrigation"])


@router.post("/advice")
async def advice(payload: IrrigationRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = db.get(CropPlan, payload.crop_plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Crop plan not found")
    farm = get_owned_farm(plan.farm_id, db, user)
    try:
        weather = await fetch_weather(farm.latitude, farm.longitude)
    except Exception:
        raise HTTPException(status_code=502, detail="Weather service unavailable")
    return irrigation_advice(
        crop_key=plan.crop_key,
        planting_date=plan.planting_date,
        weather=weather,
        soil_moisture_pct=payload.soil_moisture_pct,
        last_irrigation_days_ago=payload.last_irrigation_days_ago,
    )


@router.get("/farm/{farm_id}")
async def advice_for_farm(farm_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Irrigation advice for every active crop plan on a farm."""
    farm: Farm = get_owned_farm(farm_id, db, user)
    plans = db.query(CropPlan).filter(CropPlan.farm_id == farm.id, CropPlan.status == "active").all()
    if not plans:
        return []
    try:
        weather = await fetch_weather(farm.latitude, farm.longitude)
    except Exception:
        raise HTTPException(status_code=502, detail="Weather service unavailable")
    return [
        {"crop_plan_id": p.id, **irrigation_advice(p.crop_key, p.planting_date, weather)}
        for p in plans
    ]
