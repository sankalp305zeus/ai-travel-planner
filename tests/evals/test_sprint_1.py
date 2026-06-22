import os
import pytest
from backend.schemas import TravelConstraints, AgentResult

# Ensure mock keys are set for testing config import
os.environ["GEMINI_API_KEY"] = "mock_key"
os.environ["GROQ_API_KEY"] = "mock_key"
os.environ["LANGFUSE_PUBLIC_KEY"] = "mock_key"
os.environ["LANGFUSE_SECRET_KEY"] = "mock_key"
os.environ["OPENEXCHANGERATES_APP_ID"] = "mock_key"

from backend.agents.orchestrator import extract_constraints

@pytest.mark.asyncio
async def test_case_1_japan():
    # 1. "5 days Japan, Tokyo + Kyoto, $3000, love food and temples, hate crowds"
    res = await extract_constraints("5 days Japan, Tokyo + Kyoto, $3000, love food and temples, hate crowds")
    assert isinstance(res, TravelConstraints)
    assert res.duration_days == 5
    assert set(c.title() for c in res.cities) == {"Tokyo", "Kyoto"}
    assert res.budget_total == 3000.0
    assert any("food" in p.lower() for p in res.preferences)
    assert any("crowd" in a.lower() for a in res.avoidances)

@pytest.mark.asyncio
async def test_case_2_paris():
    # 2. "Weekend in Paris, €800, art museums, no queues"
    res = await extract_constraints("Weekend in Paris, €800, art museums, no queues")
    assert isinstance(res, TravelConstraints)
    assert res.duration_days == 2
    assert "Paris" in res.cities
    assert res.budget_total == 800.0

@pytest.mark.asyncio
async def test_case_3_sea():
    # 3. "2 weeks Southeast Asia, Bangkok + Bali + Singapore, $5000, beaches and nightlife"
    res = await extract_constraints("2 weeks Southeast Asia, Bangkok + Bali + Singapore, $5000, beaches and nightlife")
    assert isinstance(res, TravelConstraints)
    assert res.duration_days == 14
    assert len(res.cities) == 3
    assert "Bangkok" in res.cities
    assert "Bali" in res.cities
    assert "Singapore" in res.cities
    assert res.budget_total == 5000.0

@pytest.mark.asyncio
async def test_case_4_rome():
    # 4. "3 days Rome, $1500, history and food, avoid tourist traps"
    res = await extract_constraints("3 days Rome, $1500, history and food, avoid tourist traps")
    assert isinstance(res, TravelConstraints)
    assert res.duration_days == 3
    assert "Rome" in res.cities
    assert res.budget_total == 1500.0

@pytest.mark.asyncio
async def test_case_5_india():
    # 5. "10 days India, Delhi + Agra + Jaipur, $2000, culture, no luxury hotels"
    res = await extract_constraints("10 days India, Delhi + Agra + Jaipur, $2000, culture, no luxury hotels")
    assert isinstance(res, TravelConstraints)
    assert res.duration_days == 10
    assert len(res.cities) == 3
    assert "Delhi" in res.cities
    assert "Agra" in res.cities
    assert "Jaipur" in res.cities
    assert res.budget_total == 2000.0

@pytest.mark.asyncio
async def test_case_6_spain_fortnight():
    # 6. "A fortnight in Spain, Madrid + Barcelona, €4000, museums, avoid summer heat"
    res = await extract_constraints("A fortnight in Spain, Madrid + Barcelona, €4000, museums, avoid summer heat")
    assert isinstance(res, TravelConstraints)
    assert res.duration_days == 14
    assert set(res.cities) == {"Madrid", "Barcelona"}
    assert res.budget_total == 4000.0
    assert res.currency == "EUR"

@pytest.mark.asyncio
async def test_case_7_ny_week():
    # 7. "One week in New York, $2500, broadway shows, no cars"
    res = await extract_constraints("One week in New York, $2500, broadway shows, no cars")
    assert isinstance(res, TravelConstraints)
    assert res.duration_days == 7
    assert "New York" in res.cities
    assert res.budget_total == 2500.0
    assert any("car" in a.lower() for a in res.avoidances)

@pytest.mark.asyncio
async def test_case_8_south_america():
    # 8. "3 weeks in South America, Lima + Cusco, $3500, hiking, no high altitude without acclimation"
    res = await extract_constraints("3 weeks in South America, Lima + Cusco, $3500, hiking, no high altitude without acclimation")
    assert isinstance(res, TravelConstraints)
    assert res.duration_days == 21
    assert "Lima" in res.cities
    assert "Cusco" in res.cities
    assert res.budget_total == 3500.0

@pytest.mark.asyncio
async def test_case_9_london():
    # 9. "Weekend getaway to London, £1000, theater, no crowded tube"
    res = await extract_constraints("Weekend getaway to London, £1000, theater, no crowded tube")
    assert isinstance(res, TravelConstraints)
    assert res.duration_days == 2
    assert "London" in res.cities
    assert res.budget_total == 1000.0
    assert res.currency == "GBP"

@pytest.mark.asyncio
async def test_case_10_australia():
    # 10. "12 days in Australia, Sydney + Melbourne + Cairns, $6000, diving and cafes"
    res = await extract_constraints("12 days in Australia, Sydney + Melbourne + Cairns, $6000, diving and cafes")
    assert isinstance(res, TravelConstraints)
    assert res.duration_days == 12
    assert len(res.cities) == 3
    assert "Sydney" in res.cities
    assert "Melbourne" in res.cities
    assert "Cairns" in res.cities
    assert res.budget_total == 6000.0
