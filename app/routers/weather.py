from fastapi import APIRouter, HTTPException
from ..services.weather_client import get_weather_data

router = APIRouter(prefix="/weather", tags=["Weather Intelligence"])

@router.get("/{location}")
def get_location_weather(location: str):
    data = get_weather_data(location)
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    return data