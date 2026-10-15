from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.data.crops import CROPS
from app.db.session import get_db
from app.models.market import MarketPrice
from app.models.user import User
from app.schemas import MarketPriceCreate, MarketPriceOut

router = APIRouter(prefix="/api/market", tags=["market"])


def _out(p: MarketPrice) -> MarketPriceOut:
    o = MarketPriceOut.model_validate(p)
    o.crop_name = CROPS.get(p.crop_key, {}).get("name", p.crop_key)
    return o


@router.get("/markets")
def list_markets(db: Session = Depends(get_db)):
    rows = db.query(MarketPrice.market).distinct().order_by(MarketPrice.market).all()
    return [r[0] for r in rows]


@router.get("/latest", response_model=list[MarketPriceOut])
def latest_prices(market: str | None = None, crop_key: str | None = None, db: Session = Depends(get_db)):
    """Most recent price per (crop, market)."""
    sub = (
        db.query(MarketPrice.crop_key, MarketPrice.market, func.max(MarketPrice.date).label("max_date"))
        .group_by(MarketPrice.crop_key, MarketPrice.market)
        .subquery()
    )
    q = db.query(MarketPrice).join(
        sub,
        (MarketPrice.crop_key == sub.c.crop_key)
        & (MarketPrice.market == sub.c.market)
        & (MarketPrice.date == sub.c.max_date),
    )
    if market:
        q = q.filter(MarketPrice.market == market)
    if crop_key:
        q = q.filter(MarketPrice.crop_key == crop_key)
    return [_out(p) for p in q.order_by(MarketPrice.crop_key, MarketPrice.market).all()]


@router.get("/compare/{crop_key}")
def compare_markets(crop_key: str, db: Session = Depends(get_db)):
    """Latest price of one crop across all markets, best price first."""
    rows = latest_prices(crop_key=crop_key, db=db)
    rows.sort(key=lambda r: -r.price_per_kg)
    return rows


@router.get("/history/{crop_key}", response_model=list[MarketPriceOut])
def price_history(crop_key: str, market: str | None = None, days: int = 90, db: Session = Depends(get_db)):
    from datetime import timedelta

    q = db.query(MarketPrice).filter(MarketPrice.crop_key == crop_key, MarketPrice.date >= date.today() - timedelta(days=days))
    if market:
        q = q.filter(MarketPrice.market == market)
    return [_out(p) for p in q.order_by(MarketPrice.date).all()]


# ---------- Admin ----------
@router.post("", response_model=MarketPriceOut, status_code=status.HTTP_201_CREATED)
def add_price(payload: MarketPriceCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if payload.crop_key not in CROPS:
        raise HTTPException(status_code=400, detail="Unknown crop")
    data = payload.model_dump()
    data["date"] = data["date"] or date.today()
    price = MarketPrice(**data)
    db.add(price)
    db.commit()
    db.refresh(price)
    return _out(price)


@router.delete("/{price_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_price(price_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    price = db.get(MarketPrice, price_id)
    if not price:
        raise HTTPException(status_code=404, detail="Price not found")
    db.delete(price)
    db.commit()
