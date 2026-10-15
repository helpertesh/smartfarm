"""Crop calendar generator."""

from datetime import date, timedelta

from app.data.crops import CROPS
from app.models.crop_plan import CropPlan, FarmActivity


def build_activities(plan: CropPlan) -> list[FarmActivity]:
    crop = CROPS.get(plan.crop_key)
    if not crop:
        return []
    activities = []
    for day_offset, title, description in crop["calendar"]:
        activities.append(
            FarmActivity(
                crop_plan_id=plan.id,
                title=title,
                description=description,
                day_offset=day_offset,
                due_date=plan.planting_date + timedelta(days=day_offset),
            )
        )
    return activities


def preview_calendar(crop_key: str, planting_date: date) -> list[dict]:
    crop = CROPS.get(crop_key)
    if not crop:
        return []
    return [
        {
            "day_offset": d,
            "title": t,
            "description": desc,
            "due_date": (planting_date + timedelta(days=d)).isoformat(),
        }
        for d, t, desc in crop["calendar"]
    ]
