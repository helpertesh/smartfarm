from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.routers.farms import get_owned_farm
from app.services.weather import fetch_weather, weather_recommendations

router = APIRouter(prefix="/api/weather", tags=["weather"])


async def _weather_or_502(lat: float, lon: float) -> dict:
    try:
        return await fetch_weather(lat, lon)
    except Exception:
        raise HTTPException(status_code=502, detail="Weather service unavailable")


@router.get("")
async def weather_by_coords(lat: float, lon: float, user: User = Depends(get_current_user)):
    data = await _weather_or_502(lat, lon)
    return {**data, "recommendations": weather_recommendations(data)}


@router.get("/farm/{farm_id}")
async def weather_for_farm(farm_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    farm = get_owned_farm(farm_id, db, user)
    data = await _weather_or_502(farm.latitude, farm.longitude)
    return {
        "farm": {"id": farm.id, "name": farm.name, "location_name": farm.location_name},
        **data,
        "recommendations": weather_recommendations(data),
    }
