import os
import pytest
from fastapi.testclient import TestClient

# Mock environment variables before importing app to prevent config ValueError
os.environ["GEMINI_API_KEY"] = "mock_key"
os.environ["GROQ_API_KEY"] = "mock_key"
os.environ["Groq_API_KEY"] = "mock_key"
os.environ["LANGFUSE_PUBLIC_KEY"] = "mock_key"
os.environ["LANGFUSE_SECRET_KEY"] = "mock_key"
os.environ["OPENEXCHANGERATES_APP_ID"] = "mock_key"

from backend.main import app

def test_health_returns_200():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok", "version": "0.1"}

def test_env_is_gitignored():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    gitignore_path = os.path.join(project_root, ".gitignore")
    with open(gitignore_path, "r") as f:
        content = f.read()
    assert ".env" in content

def test_all_schemas_importable():
    from backend.schemas import (
        TravelConstraints,
        ActivityItem,
        ActivityCatalog,
        LodgingPlan,
        MovementPlan,
        DaySkeleton,
        BudgetBreakdown,
        DraftItinerary,
        ReviewReport,
        AgentResult,
        FinalItinerary
    )
    assert TravelConstraints is not None
    assert ActivityItem is not None
    assert ActivityCatalog is not None
    assert LodgingPlan is not None
    assert MovementPlan is not None
    assert DaySkeleton is not None
    assert BudgetBreakdown is not None
    assert DraftItinerary is not None
    assert ReviewReport is not None
    assert AgentResult is not None
    assert FinalItinerary is not None

def test_mock_search_server_returns_dict():
    from backend.mcp_servers.search_server import get_mock_activity_catalog
    res = get_mock_activity_catalog("Tokyo")
    assert isinstance(res, dict)
    assert "activities" in res
    assert "crowd_level_summary" in res
