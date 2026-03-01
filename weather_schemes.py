import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter
from pydantic import BaseModel
from data_input import llm_call

router = APIRouter()


class LocationRequest(BaseModel):
    latitude: float
    longitude: float
    language: str = "english"


def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch last 30 days of weather from Open-Meteo (free, no API key)."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily=temperature_2m_max,temperature_2m_min,"
        f"precipitation_sum,rain_sum,wind_speed_10m_max"
        f"&timezone=Asia/Kolkata"
    )

    resp = httpx.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


def analyze_weather(data: dict) -> dict:
    """Compute weather summary stats from Open-Meteo daily data."""
    daily = data.get("daily", {})
    temps_max = [t for t in (daily.get("temperature_2m_max") or []) if t is not None]
    temps_min = [t for t in (daily.get("temperature_2m_min") or []) if t is not None]
    precip = [p for p in (daily.get("precipitation_sum") or []) if p is not None]
    rain = [r for r in (daily.get("rain_sum") or []) if r is not None]
    wind = [w for w in (daily.get("wind_speed_10m_max") or []) if w is not None]

    total_rain = sum(rain) if rain else 0
    avg_temp_max = sum(temps_max) / len(temps_max) if temps_max else 0
    avg_temp_min = sum(temps_min) / len(temps_min) if temps_min else 0
    max_temp = max(temps_max) if temps_max else 0
    rainy_days = sum(1 for r in rain if r > 2.0)
    heavy_rain_days = sum(1 for r in rain if r > 20.0)
    max_wind = max(wind) if wind else 0
    dry_days = sum(1 for r in rain if r < 0.5)

    return {
        "total_rainfall_mm": round(total_rain, 1),
        "avg_temp_max_c": round(avg_temp_max, 1),
        "avg_temp_min_c": round(avg_temp_min, 1),
        "max_temp_c": round(max_temp, 1),
        "rainy_days": rainy_days,
        "heavy_rain_days": heavy_rain_days,
        "dry_days": dry_days,
        "max_wind_kmh": round(max_wind, 1),
        "period_days": len(rain) if rain else 30,
    }


@router.post("/weather-schemes")
def weather_schemes(req: LocationRequest):
    """Fetch 30-day weather for farmer's location and suggest schemes."""
    try:
        raw = fetch_weather(req.latitude, req.longitude)
    except Exception as e:
        print(f"[Weather] API error: {e}")
        return {"error": "Could not fetch weather data. Please try again."}

    stats = analyze_weather(raw)
    print(f"[Weather] Stats: {stats}")

    prompt = f"""You are an expert on Indian government farmer schemes.

Based on the weather data from the farmer's location over the last 30 days, recommend which schemes the farmer should urgently consider.

WEATHER DATA:
- Total rainfall: {stats['total_rainfall_mm']} mm
- Rainy days: {stats['rainy_days']} out of {stats['period_days']} days
- Heavy rain days (>20mm): {stats['heavy_rain_days']}
- Dry days (<0.5mm): {stats['dry_days']}
- Average max temperature: {stats['avg_temp_max_c']}°C
- Max temperature recorded: {stats['max_temp_c']}°C
- Average min temperature: {stats['avg_temp_min_c']}°C
- Max wind speed: {stats['max_wind_kmh']} km/h

AVAILABLE SCHEMES:
1. PMFBY (Pradhan Mantri Fasal Bima Yojana) - Crop insurance against natural calamities
2. PMKSY (Pradhan Mantri Krishi Sinchai Yojana) - Irrigation and water management
3. Soil Health Card - Soil testing and nutrient management
4. PM-KISAN - Direct income support
5. KCC (Kisan Credit Card) - Agricultural credit
6. NLM (National Livestock Mission) - Livestock support

RULES:
- Recommend 2-3 most relevant schemes based on the weather patterns
- For each scheme explain WHY the weather data makes it relevant
- Keep each explanation to 1-2 sentences
- Be specific about what weather pattern triggered the recommendation
- Respond ENTIRELY in {req.language.upper()}

OUTPUT FORMAT (respond in plain text, not JSON):
For each scheme:
[Scheme Name]: [Why this weather makes it relevant]
"""

    try:
        recommendation = llm_call(prompt)
        if not recommendation:
            recommendation = "Based on your area's weather, consider PMFBY for crop insurance and PMKSY for irrigation support."
    except Exception as e:
        print(f"[Weather] LLM error: {e}")
        recommendation = "Based on your area's weather, consider PMFBY for crop insurance and PMKSY for irrigation support."

    return {
        "weather_summary": stats,
        "recommendation": recommendation,
    }
