import os
import json
from pathlib import Path
from typing import Dict, Any

def get_mock_activity_catalog(city: str) -> Dict[str, Any]:
    """Mock destination content research from Wikivoyage/Lonely Planet."""
    # Attempt to load from JSON database if available
    cleaned_city = city.lower().strip().replace(" ", "_")
    json_path = Path(__file__).resolve().parent.parent / "data" / "destinations" / f"{cleaned_city}.json"
    
    if json_path.exists():
        try:
            with open(json_path, "r") as f:
                activities = json.load(f)
            # Ensure city matches exactly the queried city (case normalized)
            for act in activities:
                act["city"] = city
            return {
                "activities": activities,
                "crowd_level_summary": "medium",
                "cost_band_summary": "medium",
                "rationale": f"Loaded realistic mock data for {city}."
            }
        except Exception:
            pass
            
    # Default fallback for other cities
    return {
        "activities": [
            {
                "id": f"{cleaned_city}_attraction_1",
                "city": city,
                "name": f"Famous Landmark in {city}",
                "type": "landmark",
                "estimated_duration_hours": 2.0,
                "crowd_level": "high",
                "cost_band": "free",
                "must_do": True,
                "rationale": f"The main historical landmark of {city}."
            },
            {
                "id": f"{cleaned_city}_attraction_2",
                "city": city,
                "name": f"Local Market in {city}",
                "type": "food",
                "estimated_duration_hours": 1.5,
                "crowd_level": "medium",
                "cost_band": "low",
                "must_do": True,
                "rationale": f"Popular spot for tasting local cuisine in {city}."
            }
        ],
        "crowd_level_summary": "medium",
        "cost_band_summary": "low",
        "rationale": f"Senso-ji style mock attractions for {city}."
    }

