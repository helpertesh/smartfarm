from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.security import get_current_user
from app.data.crops import CROPS
from app.db.session import get_db
from app.models.crop_plan import CropPlan, FarmActivity
from app.models.farm import Farm
from app.models.user import User
from app.routers.farms import get_owned_farm
from app.schemas import ActivityOut, CropPlanCreate, CropPlanOut, CropPlanStatusUpdate
from app.services.calendar import build_activities, preview_calendar

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


def _plan_out(plan: CropPlan) -> CropPlanOut:
    out = CropPlanOut.model_validate(plan)
    crop = CROPS.get(plan.crop_key, {})
    out.crop_name = crop.get("name", plan.crop_key)
    out.crop_icon = crop.get("icon", "🌱")
    return out


def _get_owned_plan(plan_id: int, db: Session, user: User) -> CropPlan:
    plan = db.query(CropPlan).options(selectinload(CropPlan.activities)).filter(CropPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Crop plan not found")
    get_owned_farm(plan.farm_id, db, user)
    return plan


@router.get("/preview")
def preview(crop_key: str, planting_date: date):
    if crop_key not in CROPS:
        raise HTTPException(status_code=404, detail="Crop not found")
    return {"crop": CROPS[crop_key]["name"], "activities": preview_calendar(crop_key, planting_date)}


@router.get("/plans", response_model=list[CropPlanOut])
def list_plans(farm_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = (
        db.query(CropPlan)
        .options(selectinload(CropPlan.activities))
        .join(Farm, Farm.id == CropPlan.farm_id)
        .filter(Farm.owner_id == user.id)
    )
    if farm_id:
        q = q.filter(CropPlan.farm_id == farm_id)
    plans = q.order_by(CropPlan.planting_date.desc()).all()
    return [_plan_out(p) for p in plans]


@router.post("/plans", response_model=CropPlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(payload: CropPlanCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_farm(payload.farm_id, db, user)
    if payload.crop_key not in CROPS:
        raise HTTPException(status_code=400, detail="Unknown crop")
    plan = CropPlan(**payload.model_dump())
    db.add(plan)
    db.flush()
    db.add_all(build_activities(plan))
    db.commit()
    plan = _get_owned_plan(plan.id, db, user)
    return _plan_out(plan)


@router.get("/plans/{plan_id}", response_model=CropPlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _plan_out(_get_owned_plan(plan_id, db, user))


@router.patch("/plans/{plan_id}", response_model=CropPlanOut)
def update_plan_status(
    plan_id: int, payload: CropPlanStatusUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    if payload.status not in ("active", "harvested", "abandoned"):
        raise HTTPException(status_code=400, detail="Invalid status")
    plan = _get_owned_plan(plan_id, db, user)
    plan.status = payload.status
    db.commit()
    db.refresh(plan)
    return _plan_out(plan)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = _get_owned_plan(plan_id, db, user)
    db.delete(plan)
    db.commit()


@router.get("/activities/upcoming", response_model=list[ActivityOut])
def upcoming_activities(days: int = 14, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from datetime import timedelta

    today = date.today()
    acts = (
        db.query(FarmActivity)
        .join(CropPlan, CropPlan.id == FarmActivity.crop_plan_id)
        .join(Farm, Farm.id == CropPlan.farm_id)
        .filter(Farm.owner_id == user.id, CropPlan.status == "active", FarmActivity.completed.is_(False))
        .filter(FarmActivity.due_date <= today + timedelta(days=days))
        .order_by(FarmActivity.due_date)
        .all()
    )
    return acts


@router.patch("/activities/{activity_id}/toggle", response_model=ActivityOut)
def toggle_activity(activity_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    act = db.get(FarmActivity, activity_id)
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
    _get_owned_plan(act.crop_plan_id, db, user)
    act.completed = not act.completed
    act.completed_at = datetime.now(timezone.utc) if act.completed else None
    db.commit()
    db.refresh(act)
    return act
