import os
import pytest
from unittest.mock import patch, MagicMock

# Set mock env vars
os.environ["GEMINI_API_KEY"] = "mock_key"
os.environ["LANGFUSE_PUBLIC_KEY"] = "mock_key"
os.environ["LANGFUSE_SECRET_KEY"] = "mock_key"
os.environ["OPENEXCHANGERATES_APP_ID"] = "mock_key"

from backend.schemas import TravelConstraints, DraftItinerary, ActivityCatalog, LodgingPlan, MovementPlan, BudgetBreakdown, ReviewReport
from backend.agents.review import review_destination_itinerary
from backend.graph import run_travel_planner_graph

def get_base_draft_and_constraints():
    constraints = TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo", "Kyoto"],
        duration_days=5,
        budget_total=3000.0,
        currency="USD",
        preferences=["food"],
        avoidances=[],
        hard_requirements=[],
        soft_preferences=[]
    )
    
    from backend.schemas import DaySkeleton
    draft = DraftItinerary(
        constraints=constraints,
        activity_catalog=ActivityCatalog(activities=[], crowd_level_summary="", cost_band_summary="", rationale=""),
        lodging_plan=LodgingPlan(lodgings=[], total_lodging_cost=0.0),
        movement_plan=MovementPlan(movements=[], total_movement_cost=0.0),
        day_skeletons=[
            DaySkeleton(day_number=1, city="Tokyo", activities=[], lodging_hotel_name="Hotel", notes=""),
            DaySkeleton(day_number=2, city="Tokyo", activities=[], lodging_hotel_name="Hotel", notes=""),
            DaySkeleton(day_number=3, city="Tokyo", activities=[], lodging_hotel_name="Hotel", notes=""),
            DaySkeleton(day_number=4, city="Kyoto", activities=[], lodging_hotel_name="Hotel", notes=""),
            DaySkeleton(day_number=5, city="Kyoto", activities=[], lodging_hotel_name="Hotel", notes="")
        ],
        budget_breakdown=BudgetBreakdown(categories=[], total_estimated_cost=2000.0, within_budget=True, violations=[], suggested_swaps=[])
    )
    return draft, constraints

@pytest.mark.asyncio
async def test_catches_wrong_day_count():
    draft, constraints = get_base_draft_and_constraints()
    # Inject 3-day plan when constraints require 5
    draft.day_skeletons = draft.day_skeletons[:3]
    
    res = await review_destination_itinerary(draft, constraints)
    assert isinstance(res, ReviewReport)
    assert res.passed is False
    assert res.days_match is False
    assert any("day" in issue.lower() for issue in res.blocking_issues)

@pytest.mark.asyncio
async def test_catches_over_budget():
    draft, constraints = get_base_draft_and_constraints()
    # Inject $4000 cost on $3000 budget
    draft.budget_breakdown.total_estimated_cost = 4000.0
    draft.budget_breakdown.within_budget = False
    
    res = await review_destination_itinerary(draft, constraints)
    assert res.passed is False
    assert res.within_budget is False
    assert any("budget" in issue.lower() for issue in res.blocking_issues)

@pytest.mark.asyncio
async def test_catches_missing_city():
    draft, constraints = get_base_draft_and_constraints()
    # Kyoto is missing from skeletons
    for day in draft.day_skeletons:
        day.city = "Tokyo"
        
    res = await review_destination_itinerary(draft, constraints)
    assert res.passed is False
    assert res.cities_included is False
    assert any("kyoto" in issue.lower() for issue in res.blocking_issues)

@pytest.mark.asyncio
async def test_layer1_runs_before_any_llm():
    draft, constraints = get_base_draft_and_constraints()
    # Fail layer 1 (wrong day count)
    draft.day_skeletons = draft.day_skeletons[:3]
    
    # Spy on agent run/run_async or LLM calls
    with patch("pydantic_ai.Agent.run", side_effect=RuntimeError("LLM should not be called in Layer 1 failures")):
        res = await review_destination_itinerary(draft, constraints)
        assert res.passed is False

@pytest.mark.asyncio
async def test_repair_loop_capped_at_3():
    # Mock review report to always fail
    mock_report = ReviewReport(
        passed=False, days_match=False, cities_included=True, within_budget=True,
        preference_alignment_score=0.9, crowd_avoidance_effort=True, logistics_realistic=True,
        blocking_issues=["Day count mismatch"], advisory_issues=[], repair_hints=["Fix day count"]
    )
    draft, constraints = get_base_draft_and_constraints()
    
    with patch("backend.graph.extract_constraints", return_value=constraints), \
         patch("backend.graph.research_destination", return_value=draft.activity_catalog), \
         patch("backend.graph.plan_logistics", return_value=(draft.lodging_plan, draft.movement_plan, draft.day_skeletons)), \
         patch("backend.graph.calculate_budget", return_value=draft.budget_breakdown), \
         patch("backend.graph.get_fx_rate", return_value=1.0), \
         patch("backend.graph.review_destination_itinerary", return_value=mock_report):
        state = await run_travel_planner_graph("5 days Japan, Tokyo + Kyoto, $3000")
        assert state.get("error_code") == "REPAIR_EXHAUSTED"
        assert state.get("success") is False
        assert state.get("repair_count") >= 3

@pytest.mark.asyncio
async def test_repair_routes_to_correct_agent():
    # Test budget failure: re-runs only budget agent
    mock_fail_report = ReviewReport(
        passed=False, days_match=True, cities_included=True, within_budget=False,
        preference_alignment_score=0.9, crowd_avoidance_effort=True, logistics_realistic=True,
        blocking_issues=["Over budget"], advisory_issues=[], repair_hints=["Downgrade lodging"]
    )
    mock_pass_report = ReviewReport(
        passed=True, days_match=True, cities_included=True, within_budget=True,
        preference_alignment_score=0.9, crowd_avoidance_effort=True, logistics_realistic=True,
        blocking_issues=[], advisory_issues=[], repair_hints=[]
    )
    
    draft, constraints = get_base_draft_and_constraints()
    
    with patch("backend.graph.extract_constraints", return_value=constraints), \
         patch("backend.graph.research_destination", return_value=draft.activity_catalog) as mock_dest, \
         patch("backend.graph.plan_logistics", return_value=(draft.lodging_plan, draft.movement_plan, draft.day_skeletons)) as mock_log, \
         patch("backend.graph.calculate_budget", return_value=draft.budget_breakdown) as mock_budg, \
         patch("backend.graph.get_fx_rate", return_value=1.0), \
         patch("backend.graph.review_destination_itinerary", side_effect=[mock_fail_report, mock_pass_report]):
        
        state = await run_travel_planner_graph("5 days Japan, Tokyo + Kyoto, $3000")
        assert mock_budg.call_count == 2
        assert mock_log.call_count == 1
        assert mock_dest.call_count == 1

@pytest.mark.asyncio
async def test_valid_plan_passes():
    draft, constraints = get_base_draft_and_constraints()
    
    # For valid plan, Layer 1 passes. Layer 2 runs.
    # Mock LLM agent to return passes
    mock_agent_result = MagicMock()
    mock_agent_result.data = ReviewReport(
        passed=True, days_match=True, cities_included=True, within_budget=True,
        preference_alignment_score=0.95, crowd_avoidance_effort=True, logistics_realistic=True,
        blocking_issues=[], advisory_issues=[], repair_hints=[]
    )
    
    with patch("pydantic_ai.Agent.run", return_value=mock_agent_result):
        res = await review_destination_itinerary(draft, constraints)
        assert res.passed is True
        assert res.preference_alignment_score > 0.8
