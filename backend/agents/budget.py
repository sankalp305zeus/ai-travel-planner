from typing import List
from backend.schemas import TravelConstraints, ActivityCatalog, LodgingPlan, MovementPlan, BudgetBreakdown, BudgetCategory
from backend.mcp_servers.pricing_server import get_city_costs, fx_convert, get_destination_currency

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
    # 1. Lodging cost
    lodging_total = lodging_plan.total_lodging_cost
    
    # 2. Transport cost
    transport_total = movement_plan.total_movement_cost
    
    # 3. Activities cost (in USD)
    activity_total = 0.0
    cost_map = {"free": 0.0, "low": 15.0, "medium": 40.0, "high": 100.0}
    for act in catalog.activities:
        activity_total += cost_map.get(act.cost_band, 20.0)
        
    # 4. Food cost (in USD, assume 3 meals per day based on city averages)
    food_total = 0.0
    num_cities = len(constraints.cities)
    if num_cities > 0:
        base_days = constraints.duration_days // num_cities
        extra_days = constraints.duration_days % num_cities
        
        for i, city in enumerate(constraints.cities):
            days = base_days + (1 if i < extra_days else 0)
            costs = get_city_costs(city)
            food_total += days * 3 * costs.get("meal_avg", 15.0)
            
    # Calculate sum and totals in USD
    lodging_total = round(lodging_total, 2)
    transport_total = round(transport_total, 2)
    activity_total = round(activity_total, 2)
    food_total = round(food_total, 2)
    
    total_usd = round(lodging_total + transport_total + activity_total + food_total, 2)
    within_budget = total_usd <= constraints.budget_in_usd
    
    # Perform currency conversions
    req_cur = (constraints.requested_currency or "INR").upper()
    dest_city = constraints.cities[0] if num_cities > 0 else "Unknown"
    dest_cur = get_destination_currency(dest_city)

    total_inr = await fx_convert(total_usd, "USD", "INR")
    total_requested = await fx_convert(total_usd, "USD", req_cur)
    total_destination = await fx_convert(total_usd, "USD", dest_cur)

    # Calculate individual categories in requested currency for the frontend chart
    # (Since BudgetCategory expects amounts we should return them in requested_currency so the chart shows the user's preferred currency by default)
    # Wait, the prompt says "Default: show requested_currency" in frontend, so we should convert the categories array to requested_currency.
    rate_to_req = await fx_convert(1.0, "USD", req_cur)
    categories = [
        BudgetCategory(category="lodging", total=round(lodging_total * rate_to_req, 2)),
        BudgetCategory(category="transport", total=round(transport_total * rate_to_req, 2)),
        BudgetCategory(category="activities", total=round(activity_total * rate_to_req, 2)),
        BudgetCategory(category="food", total=round(food_total * rate_to_req, 2))
    ]
    
    # Store exchange rates used
    exchange_rates = {
        f"USD_TO_{req_cur}": await fx_convert(1.0, "USD", req_cur),
        f"USD_TO_{dest_cur}": await fx_convert(1.0, "USD", dest_cur),
        f"USD_TO_INR": await fx_convert(1.0, "USD", "INR"),
        f"{req_cur}_TO_USD": await fx_convert(1.0, req_cur, "USD"),
        f"{req_cur}_TO_INR": await fx_convert(1.0, req_cur, "INR"),
        f"{req_cur}_TO_{dest_cur}": await fx_convert(1.0, req_cur, dest_cur)
    }

    violations = []
    suggested_swaps = []
    if not within_budget:
        excess_usd = total_usd - constraints.budget_in_usd
        excess_req = excess_usd * rate_to_req
        violations.append(f"Budget exceeded by {excess_req:.2f} {req_cur}")
        suggested_swaps.append("Downgrade lodging tier to budget lodging.")
        suggested_swaps.append("Select fewer high cost-band activities.")
        suggested_swaps.append("Substitute train transit for flights or taxi transfers where possible.")
        
    return BudgetBreakdown(
        categories=categories,
        total_estimated_cost=round(total_requested, 2),
        total_inr=round(total_inr, 2),
        total_requested_currency=round(total_requested, 2),
        total_destination_currency=round(total_destination, 2),
        destination_currency_code=dest_cur,
        exchange_rates_used=exchange_rates,
        within_budget=within_budget,
        violations=violations,
        suggested_swaps=suggested_swaps
    )
