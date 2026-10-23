from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import MarketPrice

router = APIRouter(prefix="/market", tags=["Market Prices"])

class MarketPriceCreate(BaseModel):
    crop_name: str
    price_per_kg: float
    market_location: str

class MarketPriceBulkCreate(BaseModel):
    prices: List[MarketPriceCreate]

class MarketPriceResponse(BaseModel):
    id: int
    crop_name: str
    price_per_kg: float
    market_location: str
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[MarketPriceResponse])
def get_market_prices(
    crop_name: Optional[str] = None, 
    market_location: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    query = db.query(MarketPrice)
    if crop_name:
        query = query.filter(MarketPrice.crop_name.ilike(f"%{crop_name}%"))
    if market_location:
        query = query.filter(MarketPrice.market_location.ilike(f"%{market_location}%"))
    return query.all()

@router.post("/", response_model=MarketPriceResponse, status_code=status.HTTP_201_CREATED)
def add_market_price(data: MarketPriceCreate, db: Session = Depends(get_db)):
    new_price = MarketPrice(
        crop_name=data.crop_name,
        price_per_kg=data.price_per_kg,
        market_location=data.market_location
    )
    db.add(new_price)
    db.commit()
    db.refresh(new_price)
    return new_price

@router.post("/bulk", response_model=List[MarketPriceResponse], status_code=status.HTTP_201_CREATED)
def add_market_prices_bulk(data: MarketPriceBulkCreate, db: Session = Depends(get_db)):
    created_prices = []
    for item in data.prices:
        new_price = MarketPrice(
            crop_name=item.crop_name,
            price_per_kg=item.price_per_kg,
            market_location=item.market_location
        )
        db.add(new_price)
        created_prices.append(new_price)
    db.commit()
    for price in created_prices:
        db.refresh(price)
    return created_prices

@router.put("/{price_id}", response_model=MarketPriceResponse)
def update_market_price(price_id: int, data: MarketPriceCreate, db: Session = Depends(get_db)):
    price_record = db.query(MarketPrice).filter(MarketPrice.id == price_id).first()
    if not price_record:
        raise HTTPException(status_code=404, detail="Market price record not found")
        
    price_record.crop_name = data.crop_name
    price_record.price_per_kg = data.price_per_kg
    price_record.market_location = data.market_location
    
    db.commit()
    db.refresh(price_record)
    return price_record

@router.delete("/{price_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_market_price(price_id: int, db: Session = Depends(get_db)):
    price_record = db.query(MarketPrice).filter(MarketPrice.id == price_id).first()
    if not price_record:
        raise HTTPException(status_code=404, detail="Market price record not found")
    db.delete(price_record)
    db.commit()
    return None