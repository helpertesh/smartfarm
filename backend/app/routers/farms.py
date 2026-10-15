from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.farm import Farm
from app.models.user import User
from app.schemas import FarmCreate, FarmOut, FarmUpdate
from app.services.weather import geocode

router = APIRouter(prefix="/api/farms", tags=["farms"])


def get_owned_farm(farm_id: int, db: Session, user: User) -> Farm:
    farm = db.get(Farm, farm_id)
    if not farm or (farm.owner_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.get("/geocode")
async def geocode_place(q: str, user: User = Depends(get_current_user)):
    """Find coordinates for a place name (e.g. 'Nyeri')."""
    if len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query too short")
    try:
        return await geocode(q.strip())
    except Exception:
        raise HTTPException(status_code=502, detail="Geocoding service unavailable")


@router.get("", response_model=list[FarmOut])
def list_farms(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Farm).filter(Farm.owner_id == user.id).order_by(Farm.id).all()


@router.post("", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
def create_farm(payload: FarmCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    farm = Farm(owner_id=user.id, **payload.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(farm_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_owned_farm(farm_id, db, user)


@router.patch("/{farm_id}", response_model=FarmOut)
def update_farm(farm_id: int, payload: FarmUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    farm = get_owned_farm(farm_id, db, user)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(farm, k, v)
    db.commit()
    db.refresh(farm)
    return farm


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(farm_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    farm = get_owned_farm(farm_id, db, user)
    db.delete(farm)
    db.commit()
