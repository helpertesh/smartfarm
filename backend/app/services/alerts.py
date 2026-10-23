"""Builds the farmer's alert feed from weather, calendar and crop status."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.data.crops import CROPS
from app.models.crop_plan import CropPlan, FarmActivity
from app.models.farm import Farm
from app.services.weather import weather_recommendations


def build_alerts(db: Session, farm: Farm, weather: dict | None, today: date | None = None) -> list[dict]:
    today = today or date.today()
    alerts: list[dict] = []

    # Weather-driven alerts
    if weather:
        for rec in weather_recommendations(weather):
            if rec["level"] in ("warning", "danger"):
                alerts.append({"type": "weather", **rec, "date": today.isoformat()})

    # Activity alerts: overdue and upcoming within 7 days
    plans = db.query(CropPlan).filter(CropPlan.farm_id == farm.id, CropPlan.status == "active").all()
    plan_ids = [p.id for p in plans]
    if plan_ids:
        window_end = today + timedelta(days=7)
        acts = (
            db.query(FarmActivity)
            .filter(FarmActivity.crop_plan_id.in_(plan_ids), FarmActivity.completed.is_(False))
            .filter(FarmActivity.due_date <= window_end)
            .order_by(FarmActivity.due_date)
            .all()
        )
        plan_map = {p.id: p for p in plans}
        for a in acts:
            plan = plan_map[a.crop_plan_id]
            crop_name = CROPS.get(plan.crop_key, {}).get("name", plan.crop_key)
            delta = (a.due_date - today).days
            if delta < 0:
                alerts.append(
                    {
                        "type": "activity",
                        "level": "danger",
                        "title": f"Overdue: {a.title} ({crop_name})",
                        "message": f"Was due {-delta} day(s) ago. {a.description or ''}".strip(),
                        "date": a.due_date.isoformat(),
                        "activity_id": a.id,
                    }
                )
            else:
                when = "today" if delta == 0 else f"in {delta} day(s)"
                is_harvest = "harvest" in a.title.lower()
                alerts.append(
                    {
                        "type": "harvest" if is_harvest else "activity",
                        "level": "info" if delta > 2 else "warning",
                        "title": f"{a.title} ({crop_name}) due {when}",
                        "message": a.description or "",
                        "date": a.due_date.isoformat(),
                        "activity_id": a.id,
                    }
                )

    # Disease risk by crop under humid conditions
    if weather and plans:
        cur = weather["current"]
        humid = (cur.get("humidity") or 0) >= 80
        rainy = (cur.get("rain_probability_24h") or 0) >= 50
        if humid and rainy:
            risky = {p.crop_key for p in plans if p.crop_key in ("tomato", "irish_potato", "beans", "onion")}
            for key in risky:
                alerts.append(
                    {
                        "type": "disease",
                        "level": "warning",
                        "title": f"Blight / leaf disease risk for {CROPS[key]['name']}",
                        "message": "Wet, humid weather favours fungal disease. Scout the field and consider a preventive spray.",
                        "date": today.isoformat(),
                    }
                )

    order = {"danger": 0, "warning": 1, "info": 2, "success": 3}
    alerts.sort(key=lambda a: (order.get(a["level"], 9), a["date"]))
    return alerts
