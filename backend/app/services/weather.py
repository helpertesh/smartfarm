"""Weather intelligence via Open-Meteo (free, no API key).

Provides current conditions, a 7-day forecast, and farming recommendations
derived from the forecast.
"""

import time

import httpx

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 15 * 60

WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    80: ("Slight showers", "🌦️"),
    81: ("Moderate showers", "🌧️"),
    82: ("Violent showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}


def describe_code(code: int) -> dict:
    label, icon = WEATHER_CODES.get(code, ("Unknown", "🌡️"))
    return {"code": code, "label": label, "icon": icon}


async def geocode(place: str, country_code: str = "KE") -> list[dict]:
    """Look up a place name and return candidate coordinates."""
    params = {"name": place, "count": 5, "language": "en", "format": "json"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(GEOCODE_URL, params=params)
        r.raise_for_status()
        data = r.json()
    results = []
    for item in data.get("results", []):
        results.append(
            {
                "name": item.get("name"),
                "admin1": item.get("admin1"),
                "country": item.get("country"),
                "country_code": item.get("country_code"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "elevation": item.get("elevation"),
            }
        )
    # Prefer local results first
    results.sort(key=lambda x: 0 if x["country_code"] == country_code else 1)
    return results


async def fetch_weather(lat: float, lon: float) -> dict:
    key = f"{lat:.3f},{lon:.3f}"
    now = time.time()
    cached = _cache.get(key)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "hourly": "precipitation_probability,precipitation",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,et0_fao_evapotranspiration",
        "timezone": "auto",
        "forecast_days": 7,
        "past_days": 3,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(FORECAST_URL, params=params)
        r.raise_for_status()
        raw = r.json()

    data = _shape(raw)
    _cache[key] = (now, data)
    return data


def _shape(raw: dict) -> dict:
    cur = raw.get("current", {})
    daily = raw.get("daily", {})
    hourly = raw.get("hourly", {})

    # Rain probability over the next 24 hours from hourly data
    probs = hourly.get("precipitation_probability", []) or []
    hourly_times = hourly.get("time", [])
    cur_time = cur.get("time")
    start = 0
    if cur_time and cur_time in hourly_times:
        start = hourly_times.index(cur_time)
    next24 = [p for p in probs[start : start + 24] if p is not None]
    rain_prob_24h = max(next24) if next24 else None
    rain_mm_24h = sum(v or 0 for v in (hourly.get("precipitation", [])[start : start + 24]))

    days = []
    past_days = 3
    for i, d in enumerate(daily.get("time", [])):
        days.append(
            {
                "date": d,
                "is_past": i < past_days,
                "weather": describe_code(daily["weather_code"][i]),
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "rain_mm": daily["precipitation_sum"][i],
                "rain_probability": daily["precipitation_probability_max"][i],
                "wind_max_kmh": daily["wind_speed_10m_max"][i],
                "et0_mm": daily.get("et0_fao_evapotranspiration", [None] * len(daily["time"]))[i],
            }
        )

    past = [d for d in days if d["is_past"]]
    future = [d for d in days if not d["is_past"]]

    return {
        "timezone": raw.get("timezone"),
        "current": {
            "time": cur_time,
            "temperature": cur.get("temperature_2m"),
            "humidity": cur.get("relative_humidity_2m"),
            "precipitation": cur.get("precipitation"),
            "wind_kmh": cur.get("wind_speed_10m"),
            "weather": describe_code(cur.get("weather_code", 0)),
            "rain_probability_24h": rain_prob_24h,
            "rain_mm_24h": round(rain_mm_24h, 1),
        },
        "past_rain_mm_3d": round(sum(d["rain_mm"] or 0 for d in past), 1),
        "forecast": future,
    }


def weather_recommendations(weather: dict) -> list[dict]:
    """Turn forecast data into plain-language farming advice."""
    recs: list[dict] = []
    cur = weather["current"]
    forecast = weather["forecast"]
    today = forecast[0] if forecast else None
    tomorrow = forecast[1] if len(forecast) > 1 else None

    rain_prob = cur.get("rain_probability_24h") or 0
    rain_mm = cur.get("rain_mm_24h") or 0

    if rain_prob >= 60 or rain_mm >= 5:
        recs.append(
            {
                "level": "info",
                "title": "Rain expected within 24 hours",
                "message": "Skip irrigation today and avoid applying foliar sprays or fertiliser that could be washed away.",
            }
        )
    elif rain_prob <= 20 and (weather.get("past_rain_mm_3d") or 0) < 5:
        recs.append(
            {
                "level": "warning",
                "title": "Dry spell",
                "message": "No significant rain in the last 3 days and none expected. Irrigate crops in critical growth stages and mulch to conserve moisture.",
            }
        )

    heavy = [d for d in forecast[:3] if (d["rain_mm"] or 0) >= 30]
    if heavy:
        recs.append(
            {
                "level": "danger",
                "title": "Heavy rainfall ahead",
                "message": f"Up to {max(d['rain_mm'] for d in heavy):.0f} mm expected on {heavy[0]['date']}. Open drainage channels, delay planting on low ground and harvest ripe produce early.",
            }
        )

    if today and (today["temp_max"] or 0) >= 33:
        recs.append(
            {
                "level": "warning",
                "title": "Very high temperatures",
                "message": "Water early in the morning or evening, provide shade for seedlings and avoid transplanting in the heat of the day.",
            }
        )

    if today and (today["temp_min"] or 99) <= 8:
        recs.append(
            {
                "level": "warning",
                "title": "Cold night expected",
                "message": "Low temperatures can damage tomatoes, beans and young seedlings. Cover nurseries overnight.",
            }
        )

    if today and (today["wind_max_kmh"] or 0) >= 35:
        recs.append(
            {
                "level": "warning",
                "title": "Strong winds",
                "message": "Postpone spraying to avoid drift, and prop or stake tall crops such as bananas and maize.",
            }
        )

    humid_days = [d for d in forecast[:3] if (d["rain_probability"] or 0) >= 50]
    if (cur.get("humidity") or 0) >= 80 and humid_days:
        recs.append(
            {
                "level": "warning",
                "title": "High disease risk",
                "message": "Warm, humid conditions favour blight, mildew and leaf spots. Scout tomatoes, potatoes and beans and apply preventive fungicide where needed.",
            }
        )

    if tomorrow and (tomorrow["rain_probability"] or 0) >= 60 and rain_prob < 60:
        recs.append(
            {
                "level": "info",
                "title": "Good day to apply fertiliser",
                "message": "Rain is likely tomorrow, so top-dressing applied today will be watered in naturally.",
            }
        )

    if not recs:
        recs.append(
            {
                "level": "success",
                "title": "Favourable conditions",
                "message": "Weather looks stable. A good window for weeding, planting and routine field work.",
            }
        )
    return recs
