"""Rule-based crop advisory engine.

Scores every crop in the knowledge base against the farmer's conditions and
returns ranked recommendations with reasons.
"""

from datetime import date

from app.data.crops import CROPS, SEASONS


def current_season(today: date | None = None) -> str:
    month = (today or date.today()).month
    for key, s in SEASONS.items():
        if month in s["months"]:
            return key
    return "dry"


def recommend_crops(
    soil_type: str,
    season: str,
    water_source: str,
    altitude_m: float | None = None,
    farm_size_acres: float | None = None,
    avg_temp_c: float | None = None,
) -> list[dict]:
    soil_type = soil_type.lower().strip()
    results = []

    for key, crop in CROPS.items():
        score = 0
        reasons: list[str] = []
        warnings: list[str] = []

        # Soil (weight 30)
        if soil_type in crop["soils"]:
            score += 30
            reasons.append(f"Grows well in {soil_type} soil")
        else:
            warnings.append(f"Prefers {', '.join(crop['soils'][:3])} soil rather than {soil_type}")

        # Season (weight 30)
        if season in crop["seasons"]:
            score += 30
            reasons.append(f"Suited to the {SEASONS[season]['name'].split(' (')[0].lower()}")
        elif season == "dry" and water_source in ("irrigation", "both"):
            score += 18
            reasons.append("Can be grown in the dry season with your irrigation")
        else:
            warnings.append("Not ideal for planting this season")

        # Water (weight 25)
        need = crop["water_need"]
        if water_source == "rainfed":
            if need == "low":
                score += 25
                reasons.append("Low water requirement; fine under rainfed conditions")
            elif need == "medium":
                score += 18 if season != "dry" else 5
                if season == "dry":
                    warnings.append("Needs rain or irrigation; dry-season rainfed planting is risky")
            else:
                score += 8 if season != "dry" else 0
                warnings.append("High water demand; yields suffer without irrigation")
        else:
            score += 25
            reasons.append("Water needs can be met with irrigation")

        # Altitude (weight 15)
        if altitude_m is not None:
            lo, hi = crop["altitude_m"]
            if lo <= altitude_m <= hi:
                score += 15
                reasons.append(f"Altitude {altitude_m:.0f} m is within its range")
            else:
                warnings.append(f"Best between {lo} and {hi} m altitude")
        else:
            score += 8

        # Temperature (bonus/penalty)
        if avg_temp_c is not None:
            lo, hi = crop["temp_c"]
            if lo <= avg_temp_c <= hi:
                score += 5
            else:
                score -= 10
                warnings.append(f"Prefers {lo}-{hi}°C")

        # Very small farms: favour high-value, short-duration crops
        if farm_size_acres is not None and farm_size_acres <= 0.5:
            if crop["category"] == "vegetable":
                score += 5
                reasons.append("High value per acre for a small plot")

        results.append(
            {
                "key": key,
                "name": crop["name"],
                "icon": crop["icon"],
                "category": crop["category"],
                "duration_days": crop["duration_days"],
                "water_need": need,
                "score": max(0, min(100, score)),
                "suitability": _label(score),
                "reasons": reasons,
                "warnings": warnings,
            }
        )

    results.sort(key=lambda r: -r["score"])
    return results


def _label(score: int) -> str:
    if score >= 80:
        return "Highly suitable"
    if score >= 60:
        return "Suitable"
    if score >= 40:
        return "Marginal"
    return "Not recommended"
