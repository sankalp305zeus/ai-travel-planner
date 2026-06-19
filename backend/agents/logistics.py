import math
from typing import Union, List, Tuple
from backend.schemas import TravelConstraints, ActivityItem, LodgingPlan, LodgingItem, MovementPlan, MovementItem, DaySkeleton, DayActivity, AgentResult
from backend.mcp_servers.geo_server import query_nominatim_with_fallback, get_transit_details
from backend.mcp_servers.pricing_server import get_city_costs, get_fx_rate
from backend import config

async def plan_logistics(constraints: TravelConstraints, activities: List[ActivityItem]) -> Tuple[LodgingPlan, MovementPlan, List[DaySkeleton]]:
    """
    Plans lodging, movements, and daily skeletons for the trip.
    Groups activities geographically within each city using coordinates from geo_server to minimize backtracking.
    """
    num_cities = len(constraints.cities)
    if num_cities == 0:
        return LodgingPlan(lodgings=[], total_lodging_cost=0.0), MovementPlan(movements=[], total_movement_cost=0.0), []
        
    # 1. Distribute nights across cities
    base_nights = constraints.duration_days // num_cities
    extra_nights = constraints.duration_days % num_cities
    
    nights_distribution = []
    for i in range(num_cities):
        nights = base_nights + (1 if i < extra_nights else 0)
        nights_distribution.append(nights)
        
    # Get currency exchange rate
    rate = await get_fx_rate(constraints.currency)
    
    # Select lodging tier based on daily budget
    daily_budget_usd = (constraints.budget_total / constraints.duration_days) / rate if constraints.duration_days > 0 else 0
    if daily_budget_usd < 100.0:
        tier_key = "hotel_budget"
    elif daily_budget_usd > 400.0:
        tier_key = "hotel_luxury"
    else:
        tier_key = "hotel_mid"
        
    lodgings = []
    total_lodging_cost = 0.0
    for city, nights in zip(constraints.cities, nights_distribution):
        if nights == 0:
            continue
        costs = get_city_costs(city)
        usd_cost = costs.get(tier_key, 100.0)
        cost_per_night = usd_cost * rate
        total_cost = cost_per_night * nights
        
        if tier_key == "hotel_mid":
            hotel_name = f"{city} Park Hotel"
        elif tier_key == "hotel_luxury":
            hotel_name = f"{city} Grand Plaza"
        else:
            hotel_name = f"{city} Budget Inn"
            
        lodgings.append(LodgingItem(
            city=city,
            hotel_name=hotel_name,
            cost_per_night=round(cost_per_night, 2),
            nights=nights,
            total_cost=round(total_cost, 2),
            rationale=f"Selected {hotel_name} based on budget limits."
        ))
        total_lodging_cost += total_cost
        
    lodging_plan = LodgingPlan(lodgings=lodgings, total_lodging_cost=round(total_lodging_cost, 2))
    
    # 2. Movement Plan
    movements = []
    total_movement_cost = 0.0
    for i in range(num_cities - 1):
        from_c = constraints.cities[i]
        to_c = constraints.cities[i+1]
        transit = get_transit_details(from_c, to_c)
        
        usd_cost = transit.get("estimated_cost_usd", 80.0)
        estimated_cost = usd_cost * rate
        total_movement_cost += estimated_cost
        
        movements.append(MovementItem(
            from_city=from_c,
            to_city=to_c,
            transport_mode=transit.get("transport_mode", "train"),
            duration_minutes=transit.get("duration_minutes", 120),
            estimated_cost=round(estimated_cost, 2),
            departure_time="09:00 AM",
            arrival_time="11:20 AM"
        ))
        
    movement_plan = MovementPlan(movements=movements, total_movement_cost=round(total_movement_cost, 2))
    
    # 3. Day Skeletons
    # Filter and group activities by city
    city_activities = {city: [] for city in constraints.cities}
    for act in activities:
        if act.city in city_activities:
            city_activities[act.city].append(act)
            
    # For each city, sort activities geographically to mitigate backtracking
    for city, acts in city_activities.items():
        if len(acts) <= 1:
            continue
        coords = []
        for act in acts:
            try:
                geo = await query_nominatim_with_fallback(f"{act.name}, {act.city}")
                coords.append((act, geo.get("lat", 0.0), geo.get("lon", 0.0)))
            except Exception:
                coords.append((act, 0.0, 0.0))
        # Simple geographic sweep sort
        coords.sort(key=lambda x: (x[1], x[2]))
        city_activities[city] = [x[0] for x in coords]
        
    day_skeletons = []
    day_idx = 1
    
    for city, nights in zip(constraints.cities, nights_distribution):
        acts_for_city = city_activities.get(city, [])
        slots = ["AM", "PM", "Evening"]
        
        for n in range(nights):
            day_acts = []
            hotel_name = next((l.hotel_name for l in lodgings if l.city == city), f"{city} Park Hotel")
            
            # Take up to 3 activities for this day
            start_index = n * 3
            current_day_acts = acts_for_city[start_index:start_index+3]
            
            for j, act in enumerate(current_day_acts):
                cost_map = {"free": 0.0, "low": 15.0, "medium": 40.0, "high": 100.0}
                usd_cost = cost_map.get(act.cost_band, 20.0)
                cost_in_curr = usd_cost * rate
                
                day_acts.append(DayActivity(
                    time_slot=slots[j],
                    activity_id=act.id,
                    name=act.name,
                    duration_hours=act.estimated_duration_hours,
                    cost=round(cost_in_curr, 2),
                    rationale=act.rationale
                ))
                
            day_skeletons.append(DaySkeleton(
                day_number=day_idx,
                city=city,
                activities=day_acts,
                lodging_hotel_name=hotel_name,
                notes=f"Exploring {city} on Day {day_idx}."
            ))
            day_idx += 1
            
    return lodging_plan, movement_plan, day_skeletons
