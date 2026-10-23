import requests

REGION_COORDINATES = {
    "nyeri": {"lat": -0.4169, "lon": 36.9511},
    "nairobi": {"lat": -1.2921, "lon": 36.8219},
    "nakuru": {"lat": -0.3031, "lon": 36.0800},
    "eldoret": {"lat": 0.5143, "lon": 35.2698},
    "kisumu": {"lat": -0.1022, "lon": 34.7617},
}

def get_weather_data(location: str):
    loc_key = location.lower().strip()
    coords = REGION_COORDINATES.get(loc_key, REGION_COORDINATES["nairobi"])
    
    lat = coords["lat"]
    lon = coords["lon"]
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&daily=precipitation_probability_max,temperature_2m_max,temperature_2m_min&timezone=auto"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        daily = data.get("daily", {})
        
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")
        precip_prob = daily.get("precipitation_probability_max", [0])[0] if daily.get("precipitation_probability_max") else 0
        
        recommendation = "Good conditions for general farm activities."
        if precip_prob > 60:
            recommendation = "Rain expected soon -> Avoid irrigation today to save water and prevent root rot."
        elif temp and temp > 30:
            recommendation = "High temperatures detected -> Ensure crops receive adequate water."
            
        return {
            "location": location.capitalize(),
            "temperature_celsius": temp,
            "humidity_percent": humidity,
            "wind_speed_kmh": wind,
            "rain_probability_percent": precip_prob,
            "farming_recommendation": recommendation
        }
    except Exception as e:
        return {"error": str(e)}