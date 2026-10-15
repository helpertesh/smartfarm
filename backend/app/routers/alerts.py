from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.farm import Farm
from app.models.user import User
from app.routers.farms import get_owned_farm
from app.services.alerts import build_alerts
from app.services.weather import fetch_weather

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
async def my_alerts(farm_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    farms = [get_owned_farm(farm_id, db, user)] if farm_id else db.query(Farm).filter(Farm.owner_id == user.id).all()
    alerts = []
    for farm in farms:
        try:
            weather = await fetch_weather(farm.latitude, farm.longitude)
        except Exception:
            weather = None
        for a in build_alerts(db, farm, weather):
            alerts.append({"farm_id": farm.id, "farm_name": farm.name, **a})
    order = {"danger": 0, "warning": 1, "info": 2, "success": 3}
    alerts.sort(key=lambda a: (order.get(a["level"], 9), a["date"]))
    return alerts
