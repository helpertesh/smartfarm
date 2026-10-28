from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.farm import Farm
from app.models.inputs import InputStock
from app.models.user import User
from app.routers.farms import get_owned_farm
from app.schemas import InputStockCreate, InputStockOut, InputStockUpdate

router = APIRouter(prefix="/api/inputs", tags=["inputs"])

CATEGORIES = ["seeds", "fertilizer", "pesticides", "animal feed", "other"]
UNITS = ["kg", "litres", "bags", "packets", "units"]


def _out(item: InputStock) -> InputStockOut:
    o = InputStockOut.model_validate(item)
    o.low = item.quantity <= item.reorder_level
    return o


def _validate(category: str | None, unit: str | None):
    if category is not None and category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"category must be one of: {', '.join(CATEGORIES)}")
    if unit is not None and unit not in UNITS:
        raise HTTPException(status_code=400, detail=f"unit must be one of: {', '.join(UNITS)}")


def _owned_item(item_id: int, db: Session, user: User) -> InputStock:
    item = db.get(InputStock, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Input not found")
    get_owned_farm(item.farm_id, db, user)
    return item


@router.get("/options")
def options():
    return {"categories": CATEGORIES, "units": UNITS}


@router.get("", response_model=list[InputStockOut])
def list_inputs(farm_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if farm_id:
        get_owned_farm(farm_id, db, user)
        ids = [farm_id]
    else:
        ids = [f.id for f in db.query(Farm.id).filter(Farm.owner_id == user.id).all()]
    if not ids:
        return []
    rows = db.query(InputStock).filter(InputStock.farm_id.in_(ids)).order_by(InputStock.category, InputStock.name).all()
    return [_out(i) for i in rows]


@router.post("", response_model=InputStockOut, status_code=status.HTTP_201_CREATED)
def add_input(payload: InputStockCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_farm(payload.farm_id, db, user)
    _validate(payload.category, payload.unit)
    item = InputStock(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return _out(item)


@router.patch("/{item_id}", response_model=InputStockOut)
def update_input(item_id: int, payload: InputStockUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = _owned_item(item_id, db, user)
    _validate(payload.category, payload.unit)
    for k, v in payload.model_dump(exclude_unset=True).items():
        if v is not None:
            setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return _out(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_input(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = _owned_item(item_id, db, user)
    db.delete(item)
    db.commit()
