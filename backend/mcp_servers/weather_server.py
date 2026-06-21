import httpx
import time
from typing import Dict, Any
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def get_mock_seasonal_info(city: str, month: str) -> Dict[str, Any]:
    with tracer.start_as_current_span("weather_server.get_mock_seasonal_info") as span:
        start_time = time.time()
        span.set_attribute("mcp.server", "weather_server")
        span.set_attribute("mcp.tool", "get_mock_seasonal_info")
        
        tier_used = "fallback"
        cache_hit = False
        weather_note = "Pleasant temperatures with moderate rainfall risk."
        
        try:
            r_geo = httpx.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1", timeout=5.0)
            if r_geo.status_code == 200 and r_geo.json().get("results"):
                lat = r_geo.json()["results"][0]["latitude"]
                lon = r_geo.json()["results"][0]["longitude"]
                
                r_weather = httpx.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true", timeout=5.0)
                if r_weather.status_code == 200:
                    cw = r_weather.json().get("current_weather", {})
                    temp = cw.get("temperature")
                    tier_used = "open-meteo"
                    weather_note = f"Current temp is around {temp}°C."
        except Exception:
            pass

        span.set_attribute("mcp.tier_used", tier_used)
        span.set_attribute("mcp.cache_hit", cache_hit)
        span.set_attribute("mcp.latency_ms", (time.time() - start_time) * 1000)

        return {
            "city": city,
            "month": month,
            "crowd_level": "medium",
            "weather_note": weather_note,
            "data_vintage": "2026-06-01"
        }
