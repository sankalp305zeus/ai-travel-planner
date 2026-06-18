from typing import Dict, List, Any

def get_mock_budget_breakdown(
    lodging_cost: float,
    movement_cost: float,
    activity_cost: float,
    budget_total: float,
    duration_days: int
) -> Dict[str, Any]:
    """Mock budget breakdown calculations."""
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
