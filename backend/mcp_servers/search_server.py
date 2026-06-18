from typing import Dict, Any

def get_mock_activity_catalog(city: str) -> Dict[str, Any]:
    """Mock destination content research from Wikivoyage/Lonely Planet."""
    return {
        "activities": [
            {
                "id": "tokyo_sensoji",
                "city": city,
                "name": "Senso-ji Temple",
                "type": "temple",
                "estimated_duration_hours": 2.0,
                "crowd_level": "high",
                "cost_band": "free",
                "must_do": True,
                "rationale": "Tokyo's oldest and most iconic Buddhist temple."
            },
            {
                "id": "tokyo_shinjuku_gyoen",
                "city": city,
                "name": "Shinjuku Gyoen National Garden",
                "type": "park",
                "estimated_duration_hours": 1.5,
                "crowd_level": "medium",
                "cost_band": "low",
                "must_do": True,
                "rationale": "Stunning landscape garden offering a peaceful escape."
            }
        ],
        "crowd_level_summary": "medium",
        "cost_band_summary": "low",
        "rationale": "Senso-ji is crowded but Shinjuku Gyoen offers quiet spots."
    }
