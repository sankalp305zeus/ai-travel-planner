from typing import Dict, Any

def get_mock_seasonal_info(city: str, month: str) -> Dict[str, Any]:
    """Mock seasonal guide information for weather and crowds."""
    return {
        "city": city,
        "month": month,
        "crowd_level": "medium",
        "weather_note": "Pleasant temperatures with moderate rainfall risk.",
        "data_vintage": "2026-06-01"
    }
