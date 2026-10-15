from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.models.crop_plan import CropPlan
from app.models.farm import Farm
from app.models.market import MarketPrice
from app.models.user import User
from app.schemas import UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
def stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    crops = (
        db.query(CropPlan.crop_key, func.count(CropPlan.id))
        .filter(CropPlan.status == "active")
        .group_by(CropPlan.crop_key)
        .order_by(func.count(CropPlan.id).desc())
        .all()
    )
    return {
        "users": db.query(User).count(),
        "farms": db.query(Farm).count(),
        "active_crop_plans": db.query(CropPlan).filter(CropPlan.status == "active").count(),
        "market_prices": db.query(MarketPrice).count(),
        "popular_crops": [{"crop_key": c, "count": n} for c, n in crops],
    }


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(User).order_by(User.id).all()


@router.patch("/users/{user_id}/role", response_model=UserOut)
def set_role(user_id: int, role: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if role not in ("farmer", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.role = role
    db.commit()
    db.refresh(u)
    return u


@router.patch("/users/{user_id}/active", response_model=UserOut)
def set_active(user_id: int, active: bool, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if u.id == admin.id and not active:
        raise HTTPException(status_code=400, detail="You cannot deactivate yourself")
    u.is_active = active
    db.commit()
    db.refresh(u)
    return u
