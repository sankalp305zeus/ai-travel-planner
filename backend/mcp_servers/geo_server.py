import time
import httpx
import json
from pathlib import Path
from typing import Dict, List, Any
from opentelemetry import trace
import asyncio

tracer = trace.get_tracer(__name__)

_last_nominatim_call = 0.0

async def query_nominatim_with_fallback(city: str) -> Dict[str, Any]:
    global _last_nominatim_call
    with tracer.start_as_current_span("geo_server.query_nominatim_with_fallback") as span:
        start_time = time.time()
        span.set_attribute("mcp.server", "geo_server")
        span.set_attribute("mcp.tool", "query_nominatim_with_fallback")
        
        tier_used = "fallback"
        cache_hit = False

        cleaned_city = city.strip().lower()
        
        try:
            now = time.time()
            elapsed = now - _last_nominatim_call
            if elapsed < 1.1:
                await asyncio.sleep(1.1 - elapsed)
            
            _last_nominatim_call = time.time()
            url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json"
            headers = {"User-Agent": "AITravelPlannerAgent/1.0 (sankalpshah305@gmail.com)"}
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        tier_used = "nominatim"
                        span.set_attribute("mcp.tier_used", tier_used)
                        span.set_attribute("mcp.cache_hit", cache_hit)
                        span.set_attribute("mcp.latency_ms", (time.time() - start_time) * 1000)
                        return {
                            "lat": float(data[0]["lat"]),
                            "lon": float(data[0]["lon"]),
                            "display_name": data[0]["display_name"]
                        }
        except Exception:
            pass
            
        local_coordinates = {
            "tokyo": {"lat": 35.6762, "lon": 139.6503, "display_name": "Tokyo"},
            "kyoto": {"lat": 35.0116, "lon": 135.7681, "display_name": "Kyoto"}
        }
        
        span.set_attribute("mcp.tier_used", tier_used)
        span.set_attribute("mcp.cache_hit", cache_hit)
        span.set_attribute("mcp.latency_ms", (time.time() - start_time) * 1000)
        
        if cleaned_city in local_coordinates:
            return local_coordinates[cleaned_city]
            
        return {"lat": 0.0, "lon": 0.0, "display_name": city}

def get_transit_details(city1: str, city2: str) -> Dict[str, Any]:
    with tracer.start_as_current_span("geo_server.get_transit_details") as span:
        start_time = time.time()
        span.set_attribute("mcp.server", "geo_server")
        span.set_attribute("mcp.tool", "get_transit_details")
        
        matrix_path = Path(__file__).resolve().parent.parent / "data" / "logistics" / "transit_matrix.json"
        key1 = f"{city1}-{city2}"
        key2 = f"{city2}-{city1}"
        
        if matrix_path.exists():
            try:
                with open(matrix_path, "r") as f:
                    data = json.load(f)
                if key1 in data or key2 in data:
                    res = data.get(key1) or data.get(key2)
                    span.set_attribute("mcp.tier_used", "json")
                    span.set_attribute("mcp.cache_hit", False)
                    span.set_attribute("mcp.latency_ms", (time.time() - start_time) * 1000)
                    return res
            except Exception:
                pass
                
        span.set_attribute("mcp.tier_used", "fallback")
        span.set_attribute("mcp.cache_hit", False)
        span.set_attribute("mcp.latency_ms", (time.time() - start_time) * 1000)
        return {"distance_km": 300, "duration_minutes": 180, "estimated_cost_usd": 80.0, "transport_mode": "train"}

def get_mock_lodging_plan(cities: List[str]) -> Dict[str, Any]:
    lodgings = [{"city": c, "hotel_name": f"{c} Park Hotel", "cost_per_night": 120.0, "nights": 2, "total_cost": 240.0, "rationale": f"Highly rated hotel in {c}."} for c in cities]
    return {"lodgings": lodgings, "total_lodging_cost": sum(l["total_cost"] for l in lodgings)}

def get_mock_movement_plan(cities: List[str]) -> Dict[str, Any]:
    movements = []
    for i in range(len(cities) - 1):
        details = get_transit_details(cities[i], cities[i+1])
        movements.append({
            "from_city": cities[i], "to_city": cities[i+1],
            "transport_mode": details.get("transport_mode", "train"),
            "duration_minutes": details.get("duration_minutes", 120),
            "estimated_cost": details.get("estimated_cost_usd", 100.0),
            "departure_time": "09:00 AM", "arrival_time": "11:20 AM"
        })
    return {"movements": movements, "total_movement_cost": sum(m["estimated_cost"] for m in movements)}

def get_mock_day_skeletons(cities: List[str], duration_days: int) -> List[Dict[str, Any]]:
    skeletons = []
    for day in range(1, duration_days + 1):
        city = cities[min(day - 1, len(cities) - 1)]
        skeletons.append({"day_number": day, "city": city, "activities": [], "lodging_hotel_name": f"{city} Park Hotel", "notes": ""})
    return skeletons
