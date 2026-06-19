from typing import List
from backend.schemas import TravelConstraints, ActivityCatalog, LodgingPlan, MovementPlan, BudgetBreakdown, BudgetCategory
from backend.mcp_servers.pricing_server import get_city_costs, get_fx_rate

async def calculate_budget(
    constraints: TravelConstraints,
    catalog: ActivityCatalog,
    lodging_plan: LodgingPlan,
    movement_plan: MovementPlan
) -> BudgetBreakdown:
    """
    Calculates the detailed budget breakdown for the trip.
    Evaluates costs in pure Python (zero LLM calls) for mathematical precision.
    """
    rate = await get_fx_rate(constraints.currency)
    
    # 1. Lodging cost
    lodging_total = lodging_plan.total_lodging_cost
    
    # 2. Transport cost
    transport_total = movement_plan.total_movement_cost
    
    # 3. Activities cost (convert cost bands to constraints currency)
    activity_total = 0.0
    cost_map = {"free": 0.0, "low": 15.0, "medium": 40.0, "high": 100.0}
    for act in catalog.activities:
        usd_cost = cost_map.get(act.cost_band, 20.0)
        activity_total += usd_cost * rate
        
    # 4. Food cost (assume 3 meals per day based on city averages)
    food_total = 0.0
    num_cities = len(constraints.cities)
    if num_cities > 0:
        base_days = constraints.duration_days // num_cities
        extra_days = constraints.duration_days % num_cities
        
        for i, city in enumerate(constraints.cities):
            days = base_days + (1 if i < extra_days else 0)
            costs = get_city_costs(city)
            meal_avg_usd = costs.get("meal_avg", 15.0)
            food_total += days * 3 * meal_avg_usd * rate
            
    # Calculate sum and totals
    lodging_total = round(lodging_total, 2)
    transport_total = round(transport_total, 2)
    activity_total = round(activity_total, 2)
    food_total = round(food_total, 2)
    
    total_estimated_cost = round(lodging_total + transport_total + activity_total + food_total, 2)
    within_budget = total_estimated_cost <= constraints.budget_total
    
    categories = [
        BudgetCategory(category="lodging", total=lodging_total),
        BudgetCategory(category="transport", total=transport_total),
        BudgetCategory(category="activities", total=activity_total),
        BudgetCategory(category="food", total=food_total)
    ]
    
    violations = []
    suggested_swaps = []
    if not within_budget:
        excess = total_estimated_cost - constraints.budget_total
        violations.append(f"Budget exceeded by {excess:.2f} {constraints.currency}")
        suggested_swaps.append("Downgrade lodging tier to budget lodging.")
        suggested_swaps.append("Select fewer high cost-band activities.")
        suggested_swaps.append("Substitute train transit for flights or taxi transfers where possible.")
        
    return BudgetBreakdown(
        categories=categories,
        total_estimated_cost=total_estimated_cost,
        within_budget=within_budget,
        violations=violations,
        suggested_swaps=suggested_swaps
    )
