from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.data.crops import CROPS, SEASONS, SOIL_TYPES, WATER_SOURCES, crop_list
from app.db.session import get_db
from app.models.user import User
from app.routers.farms import get_owned_farm
from app.schemas import AdvisoryRequest
from app.services.advisory import current_season, recommend_crops
from app.services.weather import fetch_weather

router = APIRouter(prefix="/api/advisory", tags=["advisory"])


@router.get("/crops")
def list_crops():
    return crop_list()


@router.get("/crops/{crop_key}")
def crop_detail(crop_key: str):
    crop = CROPS.get(crop_key)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    return {"key": crop_key, **crop}


@router.get("/options")
def options():
    return {
        "soil_types": SOIL_TYPES,
        "water_sources": WATER_SOURCES,
        "seasons": [{"key": k, "name": v["name"]} for k, v in SEASONS.items()],
        "current_season": current_season(),
    }


@router.post("/recommend")
def recommend(payload: AdvisoryRequest, user: User = Depends(get_current_user)):
    season = payload.season or current_season()
    if season not in SEASONS:
        raise HTTPException(status_code=400, detail="Unknown season")
    return {
        "season": season,
        "season_name": SEASONS[season]["name"],
        "recommendations": recommend_crops(
            soil_type=payload.soil_type,
            season=season,
            water_source=payload.water_source,
            altitude_m=payload.altitude_m,
            farm_size_acres=payload.farm_size_acres,
            avg_temp_c=payload.avg_temp_c,
        ),
    }


@router.get("/farm/{farm_id}")
async def recommend_for_farm(
    farm_id: int, season: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Recommendations using the farm's stored soil/water and live weather for temperature."""
    farm = get_owned_farm(farm_id, db, user)
    season = season or current_season()
    avg_temp = None
    try:
        w = await fetch_weather(farm.latitude, farm.longitude)
        temps = [(d["temp_max"] + d["temp_min"]) / 2 for d in w["forecast"] if d["temp_max"] is not None]
        avg_temp = sum(temps) / len(temps) if temps else None
    except Exception:
        pass
    return {
        "farm": {"id": farm.id, "name": farm.name, "soil_type": farm.soil_type, "water_source": farm.water_source},
        "season": season,
        "season_name": SEASONS[season]["name"],
        "avg_temp_c": round(avg_temp, 1) if avg_temp else None,
        "recommendations": recommend_crops(
            soil_type=farm.soil_type,
            season=season,
            water_source=farm.water_source,
            farm_size_acres=farm.size_acres,
            avg_temp_c=avg_temp,
        ),
    }
