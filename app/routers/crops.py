from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from ..database import get_db
from ..models import CropPlan, FarmActivity, Farm
from ..schemas import CropAdvisoryRequest, CropPlanCreate, CropPlanResponse, CropPlanBulkCreate

router = APIRouter(prefix="/crops", tags=["Crop Advisory & Calendar"])

@router.post("/advisory")
def get_crop_advisory(data: CropAdvisoryRequest):
    soil = data.soil_type.lower().strip()
    location = data.location.lower().strip()
    
    recommendations = ["Maize", "Beans"]
    if soil in ["loam", "clay loam"]:
        recommendations = ["Maize", "Beans", "Irish Potatoes", "Tomatoes"]
    elif soil in ["sandy", "sandy loam"]:
        recommendations = ["Sorghum", "Millet", "Cassava", "Green Grams"]
    elif soil in ["clay"]:
        recommendations = ["Rice", "Wheat", "Sugarcane"]
        
    return {
        "location": data.location.capitalize(),
        "soil_type": data.soil_type.capitalize(),
        "season": data.season.capitalize(),
        "recommended_crops": recommendations,
        "advisory_note": f"Conditions in {data.location.capitalize()} with {data.soil_type} soil are favorable for the listed crops."
    }

@router.post("/calendar", response_model=CropPlanResponse, status_code=status.HTTP_201_CREATED)
def create_crop_calendar(plan_data: CropPlanCreate, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == plan_data.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    maturity_days = 120
    crop_lower = plan_data.crop_name.lower()
    if "potato" in crop_lower:
        maturity_days = 90
    elif "tomato" in crop_lower:
        maturity_days = 110
    elif "bean" in crop_lower:
        maturity_days = 75
        
    expected_harvest = plan_data.planting_date + timedelta(days=maturity_days)
    
    new_plan = CropPlan(
        farm_id=plan_data.farm_id,
        crop_name=plan_data.crop_name,
        planting_date=plan_data.planting_date,
        expected_harvest_date=expected_harvest,
        status="Active"
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    
    schedule_templates = [
        ("First inspection", 14),
        ("Weeding", 21),
        ("Fertilizer application", 30),
        ("Pest and disease monitoring", 60),
        ("Pre-harvest check", maturity_days - 10)
    ]
    
    for act_name, day_offset in schedule_templates:
        due_dt = plan_data.planting_date + timedelta(days=day_offset)
        activity = FarmActivity(
            crop_plan_id=new_plan.id,
            activity_name=act_name,
            due_date=due_dt,
            is_completed=False
        )
        db.add(activity)
        
    db.commit()
    db.refresh(new_plan)
    return new_plan

@router.post("/calendar/bulk", response_model=List[CropPlanResponse], status_code=status.HTTP_201_CREATED)
def create_crop_calendars_bulk(data: CropPlanBulkCreate, db: Session = Depends(get_db)):
    created_plans = []
    
    for plan_data in data.plans:
        farm = db.query(Farm).filter(Farm.id == plan_data.farm_id).first()
        if not farm:
            raise HTTPException(status_code=404, detail=f"Farm with ID {plan_data.farm_id} not found")
            
        maturity_days = 120
        crop_lower = plan_data.crop_name.lower()
        if "potato" in crop_lower:
            maturity_days = 90
        elif "tomato" in crop_lower:
            maturity_days = 110
        elif "bean" in crop_lower:
            maturity_days = 75
            
        expected_harvest = plan_data.planting_date + timedelta(days=maturity_days)
        
        new_plan = CropPlan(
            farm_id=plan_data.farm_id,
            crop_name=plan_data.crop_name,
            planting_date=plan_data.planting_date,
            expected_harvest_date=expected_harvest,
            status="Active"
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        
        schedule_templates = [
            ("First inspection", 14),
            ("Weeding", 21),
            ("Fertilizer application", 30),
            ("Pest and disease monitoring", 60),
            ("Pre-harvest check", maturity_days - 10)
        ]
        
        for act_name, day_offset in schedule_templates:
            due_dt = plan_data.planting_date + timedelta(days=day_offset)
            activity = FarmActivity(
                crop_plan_id=new_plan.id,
                activity_name=act_name,
                due_date=due_dt,
                is_completed=False
            )
            db.add(activity)
            
        db.commit()
        db.refresh(new_plan)
        created_plans.append(new_plan)
        
    return created_plans

@router.delete("/calendar/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop_calendar(plan_id: int, db: Session = Depends(get_db)):
    crop_plan = db.query(CropPlan).filter(CropPlan.id == plan_id).first()
    if not crop_plan:
        raise HTTPException(status_code=404, detail="Crop plan not found")
        
    db.delete(crop_plan)
    db.commit()
    return None