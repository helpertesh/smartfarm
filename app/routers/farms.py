from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Farm, User
from ..schemas import FarmCreate, FarmResponse, FarmBulkCreate

router = APIRouter(prefix="/farms", tags=["Farm Management"])

@router.post("/", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def register_farm(farm_data: FarmCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == farm_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    new_farm = Farm(
        user_id=farm_data.user_id,
        farm_name=farm_data.farm_name,
        location=farm_data.location,
        size_acres=farm_data.size_acres
    )
    db.add(new_farm)
    db.commit()
    db.refresh(new_farm)
    return new_farm

@router.post("/bulk", response_model=List[FarmResponse], status_code=status.HTTP_201_CREATED)
def register_farms_bulk(data: FarmBulkCreate, db: Session = Depends(get_db)):
    created_farms = []
    for farm_data in data.farms:
        user = db.query(User).filter(User.id == farm_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {farm_data.user_id} not found")
            
        new_farm = Farm(
            user_id=farm_data.user_id,
            farm_name=farm_data.farm_name,
            location=farm_data.location,
            size_acres=farm_data.size_acres
        )
        db.add(new_farm)
        created_farms.append(new_farm)
        
    db.commit()
    for farm in created_farms:
        db.refresh(farm)
    return created_farms

@router.get("/user/{user_id}", response_model=List[FarmResponse])
def get_user_farms(user_id: int, db: Session = Depends(get_db)):
    farms = db.query(Farm).filter(Farm.user_id == user_id).all()
    return farms

@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(farm_id: int, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    db.delete(farm)
    db.commit()
    return None