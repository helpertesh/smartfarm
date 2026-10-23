from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import datetime

from ..database import get_db
from ..models import FinancialRecord, HarvestRecord, Farm

router = APIRouter(prefix="/analytics", tags=["Farm Analytics"])

class FinancialRecordCreate(BaseModel):
    farm_id: int
    record_type: str  # 'Revenue' or 'Expense'
    amount: float
    description: Optional[str] = None
    date: Optional[datetime.date] = None

class FinancialRecordResponse(BaseModel):
    id: int
    farm_id: int
    record_type: str
    amount: float
    description: Optional[str] = None
    date: Optional[datetime.date] = None

    class Config:
        from_attributes = True

class HarvestRecordCreate(BaseModel):
    farm_id: int
    crop_name: str
    quantity_kg: float
    harvest_date: Optional[datetime.date] = None

class HarvestRecordResponse(BaseModel):
    id: int
    farm_id: int
    crop_name: str
    quantity_kg: float
    harvest_date: Optional[datetime.date] = None

    class Config:
        from_attributes = True

class FarmSummaryResponse(BaseModel):
    farm_id: int
    farm_name: str
    total_revenue: float
    total_expenses: float
    net_profit: float
    total_harvest_kg: float

@router.post("/financials", response_model=FinancialRecordResponse, status_code=status.HTTP_201_CREATED)
def add_financial_record(data: FinancialRecordCreate, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == data.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    record = FinancialRecord(
        farm_id=data.farm_id,
        record_type=data.record_type,
        amount=data.amount,
        description=data.description,
        date=data.date
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.post("/harvests", response_model=HarvestRecordResponse, status_code=status.HTTP_201_CREATED)
def add_harvest_record(data: HarvestRecordCreate, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == data.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    harvest = HarvestRecord(
        farm_id=data.farm_id,
        crop_name=data.crop_name,
        quantity_kg=data.quantity_kg,
        harvest_date=data.harvest_date
    )
    db.add(harvest)
    db.commit()
    db.refresh(harvest)
    return harvest

@router.get("/summary/{farm_id}", response_model=FarmSummaryResponse)
def get_farm_summary(farm_id: int, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    # Calculate financials
    financials = db.query(FinancialRecord).filter(FinancialRecord.farm_id == farm_id).all()
    total_revenue = sum(float(f.amount) for f in financials if f.record_type and f.record_type.lower() == 'revenue')
    total_expenses = sum(float(f.amount) for f in financials if f.record_type and f.record_type.lower() == 'expense')
    net_profit = total_revenue - total_expenses
    
    # Calculate harvests
    harvests = db.query(HarvestRecord).filter(HarvestRecord.farm_id == farm_id).all()
    total_harvest_kg = sum(float(h.quantity_kg) for h in harvests)
    
    return {
        "farm_id": farm.id,
        "farm_name": farm.farm_name,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "total_harvest_kg": total_harvest_kg
    }

@router.delete("/financials/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_financial_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(FinancialRecord).filter(FinancialRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Financial record not found")
    db.delete(record)
    db.commit()
    return None

@router.delete("/harvests/{harvest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_harvest_record(harvest_id: int, db: Session = Depends(get_db)):
    harvest = db.query(HarvestRecord).filter(HarvestRecord.id == harvest_id).first()
    if not harvest:
        raise HTTPException(status_code=404, detail="Harvest record not found")
    db.delete(harvest)
    db.commit()
    return None