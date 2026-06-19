import httpx
import json
from pathlib import Path
from typing import Dict, List, Any
from backend import config

async def get_fx_rate(to_currency: str) -> float:
    """Gets exchange rate from USD to target currency with static fallback."""
    to_currency = to_currency.upper().strip()
    if to_currency == "USD":
        return 1.0
        
    # Tier 1: Open Exchange Rates
    app_id = config.OPENEXCHANGERATES_APP_ID
    if app_id and app_id != "mock_key":
        try:
            url = f"https://openexchangerates.org/api/latest.json?app_id={app_id}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    rates = data.get("rates", {})
                    if to_currency in rates:
                        return float(rates[to_currency])
        except Exception:
            pass
            
    # Tier 2: Static fx_rates.json
    fx_path = Path(__file__).resolve().parent.parent / "data" / "pricing" / "fx_rates.json"
    if fx_path.exists():
        try:
            with open(fx_path, "r") as f:
                data = json.load(f)
            rates = data.get("rates", {})
            if to_currency in rates:
                return float(rates[to_currency])
        except Exception:
            pass
            
    # Default fallbacks
    defaults = {"EUR": 0.92, "GBP": 0.79, "JPY": 155.0, "AUD": 1.50, "SGD": 1.35, "INR": 83.5}
    return defaults.get(to_currency, 1.0)

def get_city_costs(city: str) -> Dict[str, float]:
    """Gets static cost profiles for a given city in USD."""
    cleaned_city = city.lower().strip().replace(" ", "_")
    bands_path = Path(__file__).resolve().parent.parent / "data" / "pricing" / "city_cost_bands.json"
    if bands_path.exists():
        try:
            with open(bands_path, "r") as f:
                data = json.load(f)
            if cleaned_city in data:
                return data[cleaned_city]
        except Exception:
            pass
            
    # Default fallback values
    return {
        "hotel_budget": 30.0,
        "hotel_mid": 75.0,
        "hotel_luxury": 200.0,
        "meal_avg": 15.0,
        "activity_avg": 10.0
    }

# Keep original helper functions for backwards compatibility
def get_mock_budget_breakdown(
    lodging_cost: float,
    movement_cost: float,
    activity_cost: float,
    budget_total: float,
    duration_days: int
) -> Dict[str, Any]:
    food_cost = 50.0 * duration_days
    total_estimated = lodging_cost + movement_cost + activity_cost + food_cost
    within_budget = total_estimated <= budget_total
    
    categories = [
        {"category": "lodging", "total": lodging_cost},
        {"category": "transport", "total": movement_cost},
        {"category": "activities", "total": activity_cost},
        {"category": "food", "total": food_cost}
    ]
    
    violations = []
    suggested_swaps = []
    if not within_budget:
        excess = total_estimated - budget_total
        violations.append(f"Budget exceeded by {excess:.2f} USD")
        suggested_swaps.append("Downgrade park hotel to budget lodging or choose fewer paid activities.")
        
    return {
        "categories": categories,
        "total_estimated_cost": total_estimated,
        "within_budget": within_budget,
        "violations": violations,
        "suggested_swaps": suggested_swaps
    }
