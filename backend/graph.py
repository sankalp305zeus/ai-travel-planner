from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, START, END
from backend.schemas import TravelConstraints, ActivityCatalog, LodgingPlan, MovementPlan, DaySkeleton, BudgetBreakdown, DraftItinerary, AgentResult, DayActivity
from backend.agents.orchestrator import extract_constraints
from backend.agents.destination import research_destination
from backend.agents.logistics import plan_logistics
from backend.agents.budget import calculate_budget
from backend.mcp_servers.pricing_server import get_fx_rate

class TravelPlanState(TypedDict):
    raw_request: str
    constraints: Optional[TravelConstraints]
    activity_catalog: Optional[ActivityCatalog]
    lodging_plan: Optional[LodgingPlan]
    movement_plan: Optional[MovementPlan]
    day_skeletons: Optional[List[DaySkeleton]]
    budget_breakdown: Optional[BudgetBreakdown]
    errors: List[str]
    draft_itinerary: Optional[DraftItinerary]

async def node_extract_constraints(state: TravelPlanState) -> dict:
    res = await extract_constraints(state["raw_request"])
    if isinstance(res, AgentResult):
        return {"errors": [res.error_detail or "Failed to extract constraints"]}
    return {"constraints": res}

async def node_destination_agent(state: TravelPlanState) -> dict:
    constraints = state["constraints"]
    if not constraints:
        return {"errors": ["No constraints found for destination research"]}
    res = await research_destination(constraints)
    if isinstance(res, AgentResult):
        return {"errors": [res.error_detail or "Destination research failed"]}
    return {"activity_catalog": res}

async def node_logistics_agent(state: TravelPlanState) -> dict:
    constraints = state["constraints"]
    if not constraints:
        return {"errors": ["No constraints found for logistics"]}
        
    from backend.mcp_servers.search_server import get_mock_activity_catalog
    from backend.schemas import ActivityItem
    
    mock_activities = []
    for city in constraints.cities:
        catalog_dict = get_mock_activity_catalog(city)
        for act_dict in catalog_dict.get("activities", []):
            mock_activities.append(ActivityItem(
                id=act_dict["id"],
                city=act_dict.get("city", city),
                name=act_dict["name"],
                type=act_dict["type"],
                estimated_duration_hours=act_dict["estimated_duration_hours"],
                crowd_level=act_dict["crowd_level"],
                cost_band=act_dict["cost_band"],
                must_do=act_dict["must_do"],
                rationale=act_dict["rationale"]
            ))
            
    lodging_plan, movement_plan, day_skeletons = await plan_logistics(constraints, mock_activities)
    return {
        "lodging_plan": lodging_plan,
        "movement_plan": movement_plan,
        "day_skeletons": day_skeletons
    }

async def node_budget_agent(state: TravelPlanState) -> dict:
    constraints = state["constraints"]
    if not constraints:
        return {"errors": ["No constraints found for budget"]}
        
    empty_catalog = ActivityCatalog(activities=[], crowd_level_summary="", cost_band_summary="", rationale="")
    empty_lodging = LodgingPlan(lodgings=[], total_lodging_cost=0.0)
    empty_movement = MovementPlan(movements=[], total_movement_cost=0.0)
    
    budget_breakdown = await calculate_budget(constraints, empty_catalog, empty_lodging, empty_movement)
    return {"budget_breakdown": budget_breakdown}

async def merge_artifacts(state: TravelPlanState) -> dict:
    """Merges parallel outputs into DraftItinerary in pure Python."""
    constraints = state["constraints"]
    activity_catalog = state["activity_catalog"]
    lodging_plan = state["lodging_plan"]
    movement_plan = state["movement_plan"]
    day_skeletons = state["day_skeletons"]
    
    # Group activities by city
    city_acts = {}
    for act in activity_catalog.activities:
        city_acts.setdefault(act.city, []).append(act)
        
    city_counters = {c: 0 for c in city_acts}
    merged_skeletons = []
    
    rate = await get_fx_rate(constraints.currency)
    cost_map = {"free": 0.0, "low": 15.0, "medium": 40.0, "high": 100.0}
    slots = ["AM", "PM", "Evening"]
    
    for day in day_skeletons:
        city = day.city
        acts = city_acts.get(city, [])
        day_acts = []
        
        start_idx = city_counters.get(city, 0)
        current_day_acts = acts[start_idx:start_idx+3]
        city_counters[city] = start_idx + len(current_day_acts)
        
        for j, act in enumerate(current_day_acts):
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
            
        merged_skeletons.append(DaySkeleton(
            day_number=day.day_number,
            city=day.city,
            activities=day_acts,
            lodging_hotel_name=day.lodging_hotel_name,
            notes=day.notes
        ))
        
    # Recompute budget with actual plans
    final_budget = await calculate_budget(constraints, activity_catalog, lodging_plan, movement_plan)
    
    draft = DraftItinerary(
        constraints=constraints,
        activity_catalog=activity_catalog,
        lodging_plan=lodging_plan,
        movement_plan=movement_plan,
        day_skeletons=merged_skeletons,
        budget_breakdown=final_budget
    )
    
    return {
        "draft_itinerary": draft,
        "budget_breakdown": final_budget,
        "day_skeletons": merged_skeletons
    }

# Build LangGraph Workflow
workflow = StateGraph(TravelPlanState)

workflow.add_node("extract_constraints", node_extract_constraints)
workflow.add_node("destination_agent", node_destination_agent)
workflow.add_node("logistics_agent", node_logistics_agent)
workflow.add_node("budget_agent", node_budget_agent)
workflow.add_node("merge_artifacts", merge_artifacts)

workflow.add_edge(START, "extract_constraints")

# Fan-out from constraints extraction
workflow.add_edge("extract_constraints", "destination_agent")
workflow.add_edge("extract_constraints", "logistics_agent")
workflow.add_edge("extract_constraints", "budget_agent")

# Fan-in to merge node
workflow.add_edge("destination_agent", "merge_artifacts")
workflow.add_edge("logistics_agent", "merge_artifacts")
workflow.add_edge("budget_agent", "merge_artifacts")

workflow.add_edge("merge_artifacts", END)

app_graph = workflow.compile()

async def run_travel_planner_graph(raw_request: str) -> dict:
    """Runs the LangGraph orchestration flow and returns the state."""
    initial_state = {
        "raw_request": raw_request,
        "constraints": None,
        "activity_catalog": None,
        "lodging_plan": None,
        "movement_plan": None,
        "day_skeletons": None,
        "budget_breakdown": None,
        "errors": [],
        "draft_itinerary": None
    }
    return await app_graph.ainvoke(initial_state)
