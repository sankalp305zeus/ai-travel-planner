import os
import pytest
import time
from unittest.mock import patch

# Set mock env vars before importing anything
os.environ["GEMINI_API_KEY"] = "mock_key"
os.environ["GROQ_API_KEY"] = "mock_key"
os.environ["LANGFUSE_PUBLIC_KEY"] = "mock_key"
os.environ["LANGFUSE_SECRET_KEY"] = "mock_key"
os.environ["OPENEXCHANGERATES_APP_ID"] = "mock_key"

from fastapi.testclient import TestClient
from backend.main import app
from backend.schemas import DraftItinerary
from backend.graph import run_travel_planner_graph

client = TestClient(app)

@pytest.mark.asyncio
async def test_parallel_under_15s():
    start_time = time.time()
    # Execute graph directly
    state = await run_travel_planner_graph("5 days Japan, Tokyo + Kyoto, $3000, love food and temples, hate crowds")
    end_time = time.time()
    elapsed = end_time - start_time
    assert elapsed < 15.0
    assert "draft_itinerary" in state

def test_draft_has_correct_day_count():
    response = client.post("/api/plan", json={"request": "3 days Rome, $1500, history and food"})
    assert response.status_code == 200
    plan_id = response.json()["plan_id"]
    
    import time
    for _ in range(30):
        res = client.get(f"/api/plan/{plan_id}/status")
        if res.json()["status"] == "completed":
            break
        time.sleep(0.5)
        
    data = client.get(f"/api/plan/{plan_id}").json()
    draft = DraftItinerary(**data)
    assert draft.constraints.duration_days == 3
    assert len(draft.day_skeletons) == 3

def test_all_activity_ids_resolve():
    response = client.post("/api/plan", json={"request": "5 days Japan, Tokyo + Kyoto, $3000, love food and temples, hate crowds"})
    assert response.status_code == 200
    plan_id = response.json()["plan_id"]
    
    import time
    for _ in range(30):
        res = client.get(f"/api/plan/{plan_id}/status")
        if res.json()["status"] == "completed":
            break
        time.sleep(0.5)
        
    data = client.get(f"/api/plan/{plan_id}").json()
    draft = DraftItinerary(**data)
    
    catalog_ids = {act.id for act in draft.activity_catalog.activities}
    for day in draft.day_skeletons:
        for day_act in day.activities:
            assert day_act.activity_id in catalog_ids

@pytest.mark.asyncio
async def test_no_llm_calls_in_merge():
    # Run the graph directly, and patch Agent.run to make sure it's not called during the merge_artifacts step
    # We will spy on pydantic_ai.Agent.run
    from backend.graph import merge_artifacts, TravelPlanState
    from backend.schemas import TravelConstraints, ActivityCatalog, LodgingPlan, MovementPlan
    
    state: TravelPlanState = {
        "raw_request": "3 days Rome",
        "constraints": TravelConstraints(
            destination_region="Italy", cities=["Rome"], duration_days=3, budget_total=1500.0,
            currency="USD", requested_currency="USD", budget_in_usd=1500.0, budget_in_inr=125000.0,
            preferences=[], avoidances=[], hard_requirements=[], soft_preferences=[]
        ),
        "activity_catalog": ActivityCatalog(activities=[], crowd_level_summary="", cost_band_summary="", rationale=""),
        "lodging_plan": LodgingPlan(lodgings=[], total_lodging_cost=0.0),
        "movement_plan": MovementPlan(movements=[], total_movement_cost=0.0),
        "day_skeletons": [],
        "budget_breakdown": None,
        "errors": []
    }
    
    with patch("pydantic_ai.Agent.run", side_effect=RuntimeError("LLM should not be called in merge")):
        res_state = await merge_artifacts(state)
        assert res_state["budget_breakdown"] is not None

def test_budget_swaps_reflected_in_draft():
    # Patch extract_constraints to return a low budget constraint
    from backend.schemas import TravelConstraints
    mock_constraints = TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo", "Kyoto"],
        duration_days=5,
        budget_total=100.0,
        currency="USD",
        requested_currency="USD",
        budget_in_usd=100.0,
        budget_in_inr=8000.0,
        preferences=["food"],
        avoidances=[],
        hard_requirements=[],
        soft_preferences=[]
    )
    with patch("backend.graph.extract_constraints", return_value=mock_constraints):
        from backend.schemas import ReviewReport
        mock_review = ReviewReport(
            passed=True, 
            blocking_issues=[], 
            repair_hints=[],
            days_match=True,
            cities_included=True,
            within_budget=True,
            preference_alignment_score=True,
            crowd_avoidance_effort=True,
            logistics_realistic=True,
            advisory_issues=[]
        )
        with patch("backend.graph.review_destination_itinerary", return_value=mock_review):
            response = client.post("/api/plan", json={"request": "5 days Japan, Tokyo + Kyoto, $100, love food, hate crowds"})
        assert response.status_code == 200
        plan_id = response.json()["plan_id"]
        
        import time
        for _ in range(30):
            res = client.get(f"/api/plan/{plan_id}/status")
            if res.json()["status"] == "completed":
                break
            time.sleep(0.5)
            
        data = client.get(f"/api/plan/{plan_id}").json()
        draft = DraftItinerary(**data)
        assert draft.budget_breakdown.within_budget is False
        assert len(draft.budget_breakdown.suggested_swaps) > 0

