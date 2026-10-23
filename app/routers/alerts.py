from fastapi import APIRouter
from datetime import datetime
from app.schemas import AlertRequest, AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts and Notifications"])

@router.post("/check", response_model=AlertResponse)
def evaluate_farm_alerts(payload: AlertRequest):
    triggered_alerts = []
    priority = "Low"

    # 1. Heavy rainfall check (> 50mm)
    if payload.rainfall_forecast_mm > 50.0:
        triggered_alerts.append(f"Heavy rainfall alert: {payload.rainfall_forecast_mm}mm expected in {payload.location}. Secure vulnerable crops and ensure drainage.")
        priority = "High"

    # 2. Very high temperatures check (> 35°C)
    if payload.current_temperature_c > 35.0:
        triggered_alerts.append(f"High temperature alert: Current temperature is {payload.current_temperature_c}°C. Increase irrigation frequency to prevent heat stress.")
        if priority != "High":
            priority = "Medium"

    # 3. Pest/disease risk (triggered by high heat + rain humidity combo)
    if payload.current_temperature_c > 28.0 and payload.rainfall_forecast_mm > 20.0:
        triggered_alerts.append(f"Pest/Disease risk warning for {payload.crop_name}: High humidity and warmth favor fungal outbreaks. Consider preventive spraying.")
        priority = "High"

    # 4. Upcoming farm activities (due in <= 2 days)
    if payload.upcoming_activity_days <= 2:
        triggered_alerts.append(f"Upcoming activity reminder: You have scheduled tasks for your {payload.crop_name} due in {payload.upcoming_activity_days} day(s).")

    # 5. Low stock of farm inputs (< 10kg/units)
    if payload.input_stock_level_kg < 10.0:
        triggered_alerts.append(f"Low input stock alert: Your remaining supply ({payload.input_stock_level_kg} kg) is running low. Restock soon to avoid delays.")
        if priority != "High":
            priority = "Medium"

    # Default if everything is fine
    if not triggered_alerts:
        triggered_alerts.append("All farm conditions are optimal. No immediate alerts at this time.")

    return AlertResponse(
        farmer_id=payload.farmer_id,
        alerts=triggered_alerts,
        notification_priority=priority,
        generated_at=datetime.utcnow()
    )