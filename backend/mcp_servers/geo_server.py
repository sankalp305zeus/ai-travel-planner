from typing import Dict, List, Any

def get_mock_lodging_plan(cities: List[str]) -> Dict[str, Any]:
    """Mock lodging plans based on selected cities."""
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
    """Mock inter-city movement plans."""
    movements = []
    for i in range(len(cities) - 1):
        movements.append({
            "from_city": cities[i],
            "to_city": cities[i+1],
            "transport_mode": "train",
            "duration_minutes": 140,
            "estimated_cost": 130.0,
            "departure_time": "09:00 AM",
            "arrival_time": "11:20 AM"
        })
    return {
        "movements": movements,
        "total_movement_cost": sum(m["estimated_cost"] for m in movements)
    }

def get_mock_day_skeletons(cities: List[str], duration_days: int) -> List[Dict[str, Any]]:
    """Mock daily timeline skeletons."""
    skeletons = []
    for day in range(1, duration_days + 1):
        # Assign city based on day distribution
        city = cities[min(day - 1, len(cities) - 1)]
        skeletons.append({
            "day_number": day,
            "city": city,
            "activities": [
                {
                    "time_slot": "AM",
                    "activity_id": "tokyo_sensoji",
                    "name": "Senso-ji Temple",
                    "duration_hours": 2.0,
                    "cost": 0.0,
                    "rationale": "Visit early in the morning when it is least crowded."
                },
                {
                    "time_slot": "PM",
                    "activity_id": "tokyo_shinjuku_gyoen",
                    "name": "Shinjuku Gyoen National Garden",
                    "duration_hours": 1.5,
                    "cost": 5.0,
                    "rationale": "Relaxing walk in the gardens during afternoon."
                }
            ],
            "lodging_hotel_name": f"{city} Park Hotel",
            "notes": "Make sure to bring comfortable walking shoes."
        })
    return skeletons
