import time
import httpx
import json
from pathlib import Path
from typing import Dict, List, Any

_last_nominatim_call = 0.0

async def query_nominatim_with_fallback(city: str) -> Dict[str, Any]:
    global _last_nominatim_call
    cleaned_city = city.strip().lower()
    
    # Tier 1: Nominatim API
    try:
        # Enforce rate limit (1.1s between calls)
        now = time.time()
        elapsed = now - _last_nominatim_call
        if elapsed < 1.1:
            # We use time.sleep or asyncio.sleep. Since it's an async function, asyncio.sleep is better,
            # but time.sleep is fine too. Let's use asyncio.sleep to prevent blocking the async loop.
            import asyncio
            await asyncio.sleep(1.1 - elapsed)
        
        _last_nominatim_call = time.time()
        
        url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json"
        headers = {"User-Agent": "AITravelPlannerAgent/1.0 (sankalpshah305@gmail.com)"}
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return {
                        "lat": float(data[0]["lat"]),
                        "lon": float(data[0]["lon"]),
                        "display_name": data[0]["display_name"]
                    }
    except Exception:
        pass
        
    # Tier 2: local coordinates fallback database
    local_coordinates = {
        "tokyo": {"lat": 35.6762, "lon": 139.6503, "display_name": "Tokyo"},
        "kyoto": {"lat": 35.0116, "lon": 135.7681, "display_name": "Kyoto"},
        "paris": {"lat": 48.8566, "lon": 2.3522, "display_name": "Paris"},
        "london": {"lat": 51.5074, "lon": -0.1278, "display_name": "London"},
        "bangkok": {"lat": 13.7563, "lon": 100.5018, "display_name": "Bangkok"},
        "bali": {"lat": -8.4095, "lon": 115.1889, "display_name": "Bali"},
        "singapore": {"lat": 1.3521, "lon": 103.8198, "display_name": "Singapore"},
        "rome": {"lat": 41.9028, "lon": 12.4964, "display_name": "Rome"},
        "delhi": {"lat": 28.6139, "lon": 77.2090, "display_name": "Delhi"},
        "agra": {"lat": 27.1767, "lon": 78.0081, "display_name": "Agra"},
        "jaipur": {"lat": 26.9124, "lon": 75.7873, "display_name": "Jaipur"},
        "madrid": {"lat": 40.4168, "lon": -3.7038, "display_name": "Madrid"},
        "barcelona": {"lat": 41.3851, "lon": 2.1734, "display_name": "Barcelona"},
        "new york": {"lat": 40.7128, "lon": -74.0060, "display_name": "New York"},
        "lima": {"lat": -12.0464, "lon": -77.0428, "display_name": "Lima"},
        "cusco": {"lat": -13.5319, "lon": -71.9675, "display_name": "Cusco"},
        "sydney": {"lat": -33.8688, "lon": 151.2093, "display_name": "Sydney"},
        "melbourne": {"lat": -37.8136, "lon": 144.9631, "display_name": "Melbourne"},
        "cairns": {"lat": -16.9186, "lon": 145.7781, "display_name": "Cairns"},
        "osaka": {"lat": 34.6937, "lon": 135.5023, "display_name": "Osaka"}
    }
    
    if cleaned_city in local_coordinates:
        return local_coordinates[cleaned_city]
        
    return {
        "lat": 0.0,
        "lon": 0.0,
        "display_name": city
    }

def get_transit_details(city1: str, city2: str) -> Dict[str, Any]:
    matrix_path = Path(__file__).resolve().parent.parent / "data" / "logistics" / "transit_matrix.json"
    
    key1 = f"{city1}-{city2}"
    key2 = f"{city2}-{city1}"
    
    if matrix_path.exists():
        try:
            with open(matrix_path, "r") as f:
                data = json.load(f)
            if key1 in data:
                return data[key1]
            if key2 in data:
                return data[key2]
        except Exception:
            pass
            
    # Default fallback transit details
    return {
        "distance_km": 300,
        "duration_minutes": 180,
        "estimated_cost_usd": 80.0,
        "transport_mode": "train"
    }

# Retain and adapt mock functions for compatibility
def get_mock_lodging_plan(cities: List[str]) -> Dict[str, Any]:
    lodgings = []
    for city in cities:
        lodgings.append({
            "city": city,
            "hotel_name": f"{city} Park Hotel",
            "cost_per_night": 120.0,
            "nights": 2,
            "total_cost": 240.0,
            "rationale": f"Highly rated hotel in a central area of {city}."
        })
    return {
        "lodgings": lodgings,
        "total_lodging_cost": sum(l["total_cost"] for l in lodgings)
    }

def get_mock_movement_plan(cities: List[str]) -> Dict[str, Any]:
    movements = []
    for i in range(len(cities) - 1):
        details = get_transit_details(cities[i], cities[i+1])
        movements.append({
            "from_city": cities[i],
            "to_city": cities[i+1],
            "transport_mode": details.get("transport_mode", "train"),
            "duration_minutes": details.get("duration_minutes", 120),
            "estimated_cost": details.get("estimated_cost_usd", 100.0),
            "departure_time": "09:00 AM",
            "arrival_time": "11:20 AM"
        })
    return {
        "movements": movements,
        "total_movement_cost": sum(m["estimated_cost"] for m in movements)
    }

def get_mock_day_skeletons(cities: List[str], duration_days: int) -> List[Dict[str, Any]]:
    skeletons = []
    for day in range(1, duration_days + 1):
        city = cities[min(day - 1, len(cities) - 1)]
        skeletons.append({
            "day_number": day,
            "city": city,
            "activities": [],
            "lodging_hotel_name": f"{city} Park Hotel",
            "notes": "Bring comfortable walking shoes."
        })
    return skeletons
