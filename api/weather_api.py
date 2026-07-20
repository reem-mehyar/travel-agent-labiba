import requests

GEOCODE_URL =  "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

def get_coordinates(city_name: str) -> dict:
    
    response = requests.get(GEOCODE_URL, params={"name": city_name, "count": 1}, timeout=15)
    response.raise_for_status()
    data = response.json()

    results = data.get("results")
    if not results:
        raise ValueError(f"Could not find location:{city_name}")
    
    top = results[0]
    return {"latitude": top["latitude"], "longitude":
             top["longitude"], "name": top["name"], "country": top.get("country")}

def get_weather_forecase(city_name: str, start_date: str, end_date: str) -> dict:

    location = get_coordinates(city_name)

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date,
    } 

    response = requests.get(FORECAST_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    daily = data.get("daily", {})
    forecast = []

    for i, date_str in enumerate(daily.get("time", [])):
        forecast.append({"date": date_str,
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "precipitation_chance": daily["precipitation_probability_max"][i],
            "weather_code": daily["weathercode"][i],})
        
    return {"location": location["name"], "country": location["country"], "forecast": forecast}