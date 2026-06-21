import os
import pytest

# Set mock env vars
os.environ["GEMINI_API_KEY"] = "mock_key"
os.environ["LANGFUSE_PUBLIC_KEY"] = "mock_key"
os.environ["LANGFUSE_SECRET_KEY"] = "mock_key"
os.environ["OPENEXCHANGERATES_APP_ID"] = "mock_key"

from unittest.mock import patch, MagicMock
from backend.schemas import TravelConstraints, ActivityCatalog, ActivityItem, LodgingPlan, MovementPlan, DaySkeleton, BudgetBreakdown
from backend.agents.orchestrator import extract_constraints

from backend.agents.logistics import plan_logistics
from backend.agents.budget import calculate_budget
from backend.mcp_servers.geo_server import query_nominatim_with_fallback

@pytest.mark.asyncio
async def test_lodging_night_count_matches_duration():
    # Test case: 5 days trip to Tokyo & Kyoto
    constraints = TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo", "Kyoto"],
        duration_days=5,
        budget_total=3000.0,
        currency="USD",
        requested_currency="USD",
        budget_in_usd=3000.0,
        budget_in_inr=250000.0,
        preferences=["food"],
        avoidances=[],
        hard_requirements=[],
        soft_preferences=[]
    )
    
    # Mock search server to supply mock activities
    from backend.mcp_servers.search_server import get_mock_activity_catalog
    activities_dict = get_mock_activity_catalog("Tokyo")
    # Wrap in ActivityCatalog
    activities = [ActivityItem(**act) for act in activities_dict["activities"]]
    
    lodging_plan, movement_plan, day_skeletons = await plan_logistics(constraints, activities)
    
    assert isinstance(lodging_plan, LodgingPlan)
    total_nights = sum(item.nights for item in lodging_plan.lodgings)
    assert total_nights == constraints.duration_days

@pytest.mark.asyncio
async def test_movement_plan_covers_all_cities():
    constraints = TravelConstraints(
        destination_region="Southeast Asia",
        cities=["Bangkok", "Bali", "Singapore"],
        duration_days=10,
        budget_total=5000.0,
        currency="USD",
        requested_currency="USD",
        budget_in_usd=5000.0,
        budget_in_inr=400000.0,
        preferences=["beaches"],
        avoidances=[],
        hard_requirements=[],
        soft_preferences=[]
    )
    
    lodging_plan, movement_plan, day_skeletons = await plan_logistics(constraints, [])
    
    assert isinstance(movement_plan, MovementPlan)
    # 3 cities requires at least 2 movement segments (Bangkok -> Bali, Bali -> Singapore)
    assert len(movement_plan.movements) == 2
    assert movement_plan.movements[0].from_city == "Bangkok"
    assert movement_plan.movements[0].to_city == "Bali"
    assert movement_plan.movements[1].from_city == "Bali"
    assert movement_plan.movements[1].to_city == "Singapore"

@pytest.mark.asyncio
async def test_within_budget_is_pure_python():
    constraints = TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo"],
        duration_days=3,
        budget_total=1000.0,
        currency="USD",
        requested_currency="USD",
        budget_in_usd=1000.0,
        budget_in_inr=80000.0,
        preferences=[],
        avoidances=[],
        hard_requirements=[],
        soft_preferences=[]
    )
    
    catalog = ActivityCatalog(
        activities=[
            ActivityItem(
                id="act1", city="Tokyo", name="Sightseeing", type="landmark",
                estimated_duration_hours=2.0, crowd_level="medium", cost_band="medium",
                must_do=True, rationale="Fun"
            )
        ],
        crowd_level_summary="medium",
        cost_band_summary="medium",
        rationale="Fun"
    )
    
    from backend.schemas import LodgingItem, MovementItem
    lodging_plan = LodgingPlan(
        lodgings=[LodgingItem(city="Tokyo", hotel_name="Hotel", cost_per_night=100.0, nights=3, total_cost=300.0, rationale="Nice")],
        total_lodging_cost=300.0
    )
    movement_plan = MovementPlan(movements=[], total_movement_cost=0.0)
    
    # We patch pydantic_ai.Agent.run to raise an error if any LLM call is attempted
    with patch("pydantic_ai.Agent.run", side_effect=RuntimeError("LLM should not be called for budget calculation")):
        budget_breakdown = await calculate_budget(constraints, catalog, lodging_plan, movement_plan)
        assert isinstance(budget_breakdown, BudgetBreakdown)
        assert budget_breakdown.within_budget is True

@pytest.mark.asyncio
async def test_budget_sum_accurate():
    constraints = TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo"],
        duration_days=3,
        budget_total=1000.0,
        currency="USD",
        requested_currency="USD",
        budget_in_usd=1000.0,
        budget_in_inr=80000.0,
        preferences=[],
        avoidances=[],
        hard_requirements=[],
        soft_preferences=[]
    )
    
    catalog = ActivityCatalog(
        activities=[
            ActivityItem(
                id="act1", city="Tokyo", name="Sightseeing", type="landmark",
                estimated_duration_hours=2.0, crowd_level="medium", cost_band="medium",
                must_do=True, rationale="Fun"
            )
        ],
        crowd_level_summary="medium",
        cost_band_summary="medium",
        rationale="Fun"
    )
    
    from backend.schemas import LodgingItem
    lodging_plan = LodgingPlan(
        lodgings=[LodgingItem(city="Tokyo", hotel_name="Hotel", cost_per_night=150.0, nights=3, total_cost=450.0, rationale="Nice")],
        total_lodging_cost=450.0
    )
    movement_plan = MovementPlan(movements=[], total_movement_cost=0.0)
    
    budget_breakdown = await calculate_budget(constraints, catalog, lodging_plan, movement_plan)
    
    category_sum = sum(cat.total for cat in budget_breakdown.categories)
    assert abs(budget_breakdown.total_estimated_cost - category_sum) < 0.01

@pytest.mark.asyncio
async def test_suggested_swaps_present_when_overbudget():
    # Total budget = $200, but lodging alone is $300
    constraints = TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo"],
        duration_days=3,
        budget_total=200.0,
        currency="USD",
        requested_currency="USD",
        budget_in_usd=200.0,
        budget_in_inr=16000.0,
        preferences=[],
        avoidances=[],
        hard_requirements=[],
        soft_preferences=[]
    )
    
    catalog = ActivityCatalog(
        activities=[],
        crowd_level_summary="",
        cost_band_summary="",
        rationale=""
    )
    
    from backend.schemas import LodgingItem
    lodging_plan = LodgingPlan(
        lodgings=[LodgingItem(city="Tokyo", hotel_name="Hotel", cost_per_night=100.0, nights=3, total_cost=300.0, rationale="Nice")],
        total_lodging_cost=300.0
    )
    movement_plan = MovementPlan(movements=[], total_movement_cost=0.0)
    
    budget_breakdown = await calculate_budget(constraints, catalog, lodging_plan, movement_plan)
    
    assert budget_breakdown.within_budget is False
    assert len(budget_breakdown.violations) > 0
    assert len(budget_breakdown.suggested_swaps) > 0

@pytest.mark.asyncio
async def test_geo_fallback_on_nominatim_failure():
    # Mock httpx client or request call to raise an exception or fail
    with patch("httpx.AsyncClient.get", side_effect=Exception("Nominatim API error connection reset")):
        res = await query_nominatim_with_fallback("Tokyo")
        assert isinstance(res, dict)
        # Verify geocoding fields are present from fallback/matrix data
        assert "lat" in res
        assert "lon" in res
        assert res["display_name"] == "Tokyo"
