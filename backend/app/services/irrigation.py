"""Irrigation recommendation engine.

Combines crop stage water demand (crop coefficient x reference
evapotranspiration), recent rainfall, forecast rain and optional soil
moisture to advise whether to irrigate and how much.
"""

from datetime import date

from app.data.crops import CROPS, crop_stage


def irrigation_advice(
    crop_key: str,
    planting_date: date,
    weather: dict,
    soil_moisture_pct: float | None = None,
    last_irrigation_days_ago: int | None = None,
    today: date | None = None,
) -> dict:
    today = today or date.today()
    crop = CROPS.get(crop_key)
    if not crop:
        return {"recommend": False, "message": "Unknown crop."}

    days = (today - planting_date).days
    stage = crop_stage(crop_key, max(days, 0)) or crop["stages"][0]
    forecast = weather.get("forecast", [])
    today_fc = forecast[0] if forecast else {}
    et0 = today_fc.get("et0_mm") or 4.0
    demand_mm = round(stage["kc"] * et0, 1)  # crop water need today

    past_rain = weather.get("past_rain_mm_3d") or 0
    rain_prob = weather["current"].get("rain_probability_24h") or 0
    rain_24h = weather["current"].get("rain_mm_24h") or 0
    next2 = sum((d.get("rain_mm") or 0) for d in forecast[:2])

    reasons = []
    recommend = True
    amount_mm = demand_mm

    if days < 0:
        return {
            "recommend": False,
            "crop": crop["name"],
            "stage": "Not yet planted",
            "message": "Planting date is in the future.",
            "reasons": [],
            "water_demand_mm": demand_mm,
        }

    if rain_prob >= 60 or rain_24h >= demand_mm:
        recommend = False
        reasons.append(f"Rain is expected within 24 hours ({rain_prob:.0f}% chance, ~{rain_24h:.0f} mm).")
    if past_rain >= demand_mm * 3:
        recommend = False
        reasons.append(f"{past_rain:.0f} mm of rain fell in the last 3 days, enough to cover crop needs.")
    if soil_moisture_pct is not None:
        if soil_moisture_pct >= 60:
            recommend = False
            reasons.append(f"Soil moisture is {soil_moisture_pct:.0f}%, which is adequate.")
        elif soil_moisture_pct < 30:
            recommend = True
            amount_mm = round(demand_mm * 1.5, 1)
            reasons.append(f"Soil moisture is low ({soil_moisture_pct:.0f}%). Apply a deeper watering.")
    if last_irrigation_days_ago is not None and last_irrigation_days_ago == 0 and recommend:
        recommend = False
        reasons.append("Already irrigated today.")

    if recommend:
        reasons.append(
            f"{crop['name']} is in the {stage['name'].lower()} stage with a water need of about {demand_mm} mm/day "
            f"and little rain in the forecast ({next2:.0f} mm over the next 2 days)."
        )
        litres_per_sqm = amount_mm  # 1 mm over 1 m² = 1 litre
        message = f"Irrigate today: apply about {amount_mm} mm ({litres_per_sqm:.0f} litres per square metre). Water early morning or evening."
    else:
        message = "Do not irrigate today."

    return {
        "recommend": recommend,
        "crop": crop["name"],
        "stage": stage["name"],
        "days_since_planting": days,
        "water_demand_mm": demand_mm,
        "recommended_mm": amount_mm if recommend else 0,
        "message": message,
        "reasons": reasons,
    }
