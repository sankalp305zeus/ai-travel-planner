import os
import pytest

# Ensure mock keys are set for testing
os.environ["GEMINI_API_KEY"] = "mock_key"
os.environ["GROQ_API_KEY"] = "mock_key"
os.environ["LANGFUSE_PUBLIC_KEY"] = "mock_key"
os.environ["LANGFUSE_SECRET_KEY"] = "mock_key"
os.environ["OPENEXCHANGERATES_APP_ID"] = "mock_key"

from backend.schemas import ActivityCatalog, TravelConstraints
from backend.agents.orchestrator import extract_constraints
from backend.agents.destination import research_destination

@pytest.mark.asyncio
async def test_case_1_japan():
    constraints = await extract_constraints("5 days Japan, Tokyo + Kyoto, $3000, love food and temples, hate crowds")
    assert isinstance(constraints, TravelConstraints)
    
    res = await research_destination(constraints)
    assert isinstance(res, ActivityCatalog)
    assert len(res.activities) > 0
    # Ensure both cities have activities
    cities = {act.city for act in res.activities}
    assert "Tokyo" in cities
    assert "Kyoto" in cities
    for act in res.activities:
        assert act.crowd_level in ["low", "medium", "high"]
        assert act.cost_band in ["free", "low", "medium", "high"]
        assert act.id is not None
        assert act.name is not None
        assert act.type is not None
        assert act.estimated_duration_hours > 0

@pytest.mark.asyncio
async def test_case_2_paris():
    constraints = await extract_constraints("Weekend in Paris, €800, art museums, no queues")
    res = await research_destination(constraints)
    assert isinstance(res, ActivityCatalog)
    assert len(res.activities) > 0
    assert any(act.city == "Paris" for act in res.activities)
    for act in res.activities:
        assert act.crowd_level in ["low", "medium", "high"]

@pytest.mark.asyncio
async def test_case_3_sea():
    constraints = await extract_constraints("2 weeks Southeast Asia, Bangkok + Bali + Singapore, $5000, beaches and nightlife")
    res = await research_destination(constraints)
    assert isinstance(res, ActivityCatalog)
    cities = {act.city for act in res.activities}
    assert "Bangkok" in cities
    assert "Bali" in cities
    assert "Singapore" in cities

@pytest.mark.asyncio
async def test_case_4_rome():
    constraints = await extract_constraints("3 days Rome, $1500, history and food, avoid tourist traps")
    res = await research_destination(constraints)
    assert isinstance(res, ActivityCatalog)
    assert any(act.city == "Rome" for act in res.activities)

@pytest.mark.asyncio
async def test_case_5_india():
    constraints = await extract_constraints("10 days India, Delhi + Agra + Jaipur, $2000, culture, no luxury hotels")
    res = await research_destination(constraints)
    assert isinstance(res, ActivityCatalog)
    cities = {act.city for act in res.activities}
    assert "Delhi" in cities
    assert "Agra" in cities
    assert "Jaipur" in cities

@pytest.mark.asyncio
async def test_case_6_spain():
    constraints = await extract_constraints("A fortnight in Spain, Madrid + Barcelona, €4000, museums, avoid summer heat")
    res = await research_destination(constraints)
    assert isinstance(res, ActivityCatalog)
    cities = {act.city for act in res.activities}
    assert "Madrid" in cities
    assert "Barcelona" in cities

@pytest.mark.asyncio
async def test_case_7_ny():
    constraints = await extract_constraints("One week in New York, $2500, broadway shows, no cars")
    res = await research_destination(constraints)
    assert isinstance(res, ActivityCatalog)
    assert any(act.city == "New York" for act in res.activities)

@pytest.mark.asyncio
async def test_case_8_south_america():
    constraints = await extract_constraints("3 weeks in South America, Lima + Cusco, $3500, hiking, no high altitude without acclimation")
    res = await research_destination(constraints)
    assert isinstance(res, ActivityCatalog)
    cities = {act.city for act in res.activities}
    assert "Lima" in cities
    assert "Cusco" in cities

@pytest.mark.asyncio
async def test_case_9_london():
    constraints = await extract_constraints("Weekend getaway to London, £1000, theater, no crowded tube")
    res = await research_destination(constraints)
    assert isinstance(res, ActivityCatalog)
    assert any(act.city == "London" for act in res.activities)

@pytest.mark.asyncio
async def test_case_10_australia():
    constraints = await extract_constraints("12 days in Australia, Sydney + Melbourne + Cairns, $6000, diving and cafes")
    res = await research_destination(constraints)
    assert isinstance(res, ActivityCatalog)
    cities = {act.city for act in res.activities}
    assert "Sydney" in cities
    assert "Melbourne" in cities
    assert "Cairns" in cities
