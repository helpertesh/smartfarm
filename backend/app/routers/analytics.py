from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.data.crops import CROPS
from app.db.session import get_db
from app.models.farm import Farm
from app.models.finance import Harvest, Transaction
from app.models.market import MarketPrice
from app.models.user import User
from app.routers.farms import get_owned_farm
from app.schemas import HarvestCreate, HarvestOut, TransactionCreate, TransactionOut

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

EXPENSE_CATEGORIES = ["seeds", "fertilizer", "pesticides", "labour", "irrigation", "equipment", "transport", "other"]
INCOME_CATEGORIES = ["crop sales", "livestock", "subsidy", "other"]


def _owned_farm_ids(db: Session, user: User, farm_id: int | None) -> list[int]:
    if farm_id:
        get_owned_farm(farm_id, db, user)
        return [farm_id]
    return [f.id for f in db.query(Farm.id).filter(Farm.owner_id == user.id).all()]


@router.get("/categories")
def categories():
    return {"expense": EXPENSE_CATEGORIES, "income": INCOME_CATEGORIES}


# ---------- Transactions ----------
@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(farm_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ids = _owned_farm_ids(db, user, farm_id)
    if not ids:
        return []
    return db.query(Transaction).filter(Transaction.farm_id.in_(ids)).order_by(Transaction.date.desc(), Transaction.id.desc()).all()


@router.post("/transactions", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def add_transaction(payload: TransactionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_farm(payload.farm_id, db, user)
    if payload.kind not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="kind must be income or expense")
    data = payload.model_dump()
    data["date"] = data["date"] or date.today()
    t = Transaction(**data)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/transactions/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(tx_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.get(Transaction, tx_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    get_owned_farm(t.farm_id, db, user)
    db.delete(t)
    db.commit()


# ---------- Harvests ----------
@router.get("/harvests", response_model=list[HarvestOut])
def list_harvests(farm_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ids = _owned_farm_ids(db, user, farm_id)
    if not ids:
        return []
    rows = db.query(Harvest).filter(Harvest.farm_id.in_(ids)).order_by(Harvest.date.desc()).all()
    out = []
    for h in rows:
        o = HarvestOut.model_validate(h)
        o.crop_name = CROPS.get(h.crop_key, {}).get("name", h.crop_key)
        out.append(o)
    return out


@router.post("/harvests", response_model=HarvestOut, status_code=status.HTTP_201_CREATED)
def add_harvest(payload: HarvestCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_farm(payload.farm_id, db, user)
    if payload.crop_key not in CROPS:
        raise HTTPException(status_code=400, detail="Unknown crop")
    data = payload.model_dump()
    data["date"] = data["date"] or date.today()
    h = Harvest(**data)
    db.add(h)
    db.commit()
    db.refresh(h)
    o = HarvestOut.model_validate(h)
    o.crop_name = CROPS[h.crop_key]["name"]
    return o


@router.delete("/harvests/{harvest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_harvest(harvest_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    h = db.get(Harvest, harvest_id)
    if not h:
        raise HTTPException(status_code=404, detail="Harvest not found")
    get_owned_farm(h.farm_id, db, user)
    db.delete(h)
    db.commit()


# ---------- Summary ----------
@router.get("/summary")
def summary(farm_id: int | None = None, year: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ids = _owned_farm_ids(db, user, farm_id)
    year = year or date.today().year
    empty = {
        "year": year,
        "revenue": 0,
        "expenses": 0,
        "profit": 0,
        "expenses_by_category": [],
        "monthly": [],
        "harvest_by_crop": [],
        "estimated_harvest_value": 0,
    }
    if not ids:
        return empty

    tx = db.query(Transaction).filter(Transaction.farm_id.in_(ids), func.extract("year", Transaction.date) == year).all()
    revenue = sum(t.amount for t in tx if t.kind == "income")
    expenses = sum(t.amount for t in tx if t.kind == "expense")

    by_cat: dict[str, float] = {}
    monthly = {m: {"month": m, "income": 0.0, "expense": 0.0} for m in range(1, 13)}
    for t in tx:
        if t.kind == "expense":
            by_cat[t.category] = by_cat.get(t.category, 0) + t.amount
        monthly[t.date.month]["income" if t.kind == "income" else "expense"] += t.amount

    harvests = db.query(Harvest).filter(Harvest.farm_id.in_(ids), func.extract("year", Harvest.date) == year).all()
    by_crop: dict[str, float] = {}
    for h in harvests:
        by_crop[h.crop_key] = by_crop.get(h.crop_key, 0) + h.quantity_kg

    # Estimated value at latest average market price
    latest_price: dict[str, float] = {}
    for key in by_crop:
        rows = db.query(MarketPrice.price_per_kg).filter(MarketPrice.crop_key == key).order_by(MarketPrice.date.desc()).limit(5).all()
        if rows:
            latest_price[key] = sum(r[0] for r in rows) / len(rows)

    harvest_by_crop = [
        {
            "crop_key": k,
            "crop_name": CROPS.get(k, {}).get("name", k),
            "icon": CROPS.get(k, {}).get("icon", "🌱"),
            "quantity_kg": round(v, 1),
            "est_value": round(v * latest_price.get(k, 0)),
        }
        for k, v in sorted(by_crop.items(), key=lambda kv: -kv[1])
    ]

    return {
        "year": year,
        "revenue": round(revenue),
        "expenses": round(expenses),
        "profit": round(revenue - expenses),
        "expenses_by_category": [{"category": k, "amount": round(v)} for k, v in sorted(by_cat.items(), key=lambda kv: -kv[1])],
        "monthly": list(monthly.values()),
        "harvest_by_crop": harvest_by_crop,
        "estimated_harvest_value": round(sum(h["est_value"] for h in harvest_by_crop)),
    }
