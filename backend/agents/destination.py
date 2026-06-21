from typing import Union
from pydantic_ai import Agent
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.models.groq import GroqModel
from backend.schemas import TravelConstraints, ActivityCatalog, AgentResult, ActivityItem
from backend import config

# Initialize model
if config.GROQ_API_KEY and config.GROQ_API_KEY != "mock_key":
    provider = GroqProvider(api_key=config.GROQ_API_KEY)
    model = GroqModel('llama-3.3-70b-versatile', provider=provider)
    agent = Agent(
        model,
        output_type=ActivityCatalog,
        system_prompt=(
            "You are an expert travel planner destination research agent.\n"
            "Your task is to compile a comprehensive ActivityCatalog for the cities specified in the TravelConstraints.\n"
            "For each city, provide a list of activities, estimated duration, cost band, crowd level, and must-do status.\n"
            "Take into account the user's preferences, avoidances, hard requirements, and soft preferences.\n"
            "Provide a crowd level summary, cost band summary, and a cohesive rationale for the selections.\n"
            "Return ONLY the validated JSON matching the ActivityCatalog schema."
        )
    )
    
    # Define mock tools for the agent in case it needs to search/query
    @agent.tool_plain
    def web_search(query: str) -> str:
        """Search the web for information about attractions, things to do, and travel tips in a city."""
        from backend.mcp_servers.search_server import get_mock_activity_catalog
        import json
        data = get_mock_activity_catalog(query)
        return json.dumps(data)

    @agent.tool_plain
    def places_api(city: str, query: str) -> str:
        """Query Places API for details of specific places or search terms in a city."""
        from backend.mcp_servers.search_server import get_mock_activity_catalog
        import json
        data = get_mock_activity_catalog(city)
        return json.dumps(data)

    @agent.tool_plain
    def reviews_scraper(place_id: str) -> str:
        """Scrape user reviews and crowd levels for a specific place by its ID."""
        return "Crowd level: medium. Overall rating: 4.7/5. Clean and historic."

else:
    agent = None


def mock_research_destination(constraints: TravelConstraints) -> ActivityCatalog:
    from backend.mcp_servers.search_server import get_mock_activity_catalog
    
    all_activities = []
    crowd_summaries = []
    cost_summaries = []
    rationales = []
    
    for city in constraints.cities:
        mock_data = get_mock_activity_catalog(city)
        # Parse activities into ActivityItem
        for act_dict in mock_data.get("activities", []):
            item = ActivityItem(
                id=act_dict.get("id"),
                city=act_dict.get("city", city),
                name=act_dict.get("name"),
                type=act_dict.get("type"),
                estimated_duration_hours=act_dict.get("estimated_duration_hours", 2.0),
                crowd_level=act_dict.get("crowd_level", "medium"),
                cost_band=act_dict.get("cost_band", "medium"),
                must_do=act_dict.get("must_do", True),
                rationale=act_dict.get("rationale", "")
            )
            all_activities.append(item)
        
        crowd_summaries.append(mock_data.get("crowd_level_summary", "medium"))
        cost_summaries.append(mock_data.get("cost_band_summary", "medium"))
        rationales.append(mock_data.get("rationale", ""))
        
    return ActivityCatalog(
        activities=all_activities,
        crowd_level_summary=", ".join(sorted(list(set(crowd_summaries)))),
        cost_band_summary=", ".join(sorted(list(set(cost_summaries)))),
        rationale="; ".join(rationales)
    )


async def research_destination(constraints: TravelConstraints) -> Union[ActivityCatalog, AgentResult]:
    """
    Researches destination details and returns an ActivityCatalog.
    Falls back to mock implementation if GROQ_API_KEY is not set or equals "mock_key".
    """
    if not config.GROQ_API_KEY or config.GROQ_API_KEY == "mock_key":
        try:
            return mock_research_destination(constraints)
        except Exception as e:
            return AgentResult(
                success=False,
                error_code="SCHEMA_FAIL",
                error_detail=str(e)
            )

    try:
        # Prompt the agent with the constraints details
        prompt = (
            f"Research activities for the following constraints:\n"
            f"Cities: {', '.join(constraints.cities)}\n"
            f"Duration: {constraints.duration_days} days\n"
            f"Budget: {constraints.budget_total} {constraints.currency}\n"
            f"Preferences: {', '.join(constraints.preferences)}\n"
            f"Avoidances: {', '.join(constraints.avoidances)}\n"
            f"Hard Requirements: {', '.join(constraints.hard_requirements)}\n"
            f"Soft Preferences: {', '.join(constraints.soft_preferences)}"
        )
        result = await agent.run(prompt)
        return result.output
    except Exception as e:
        return AgentResult(
            success=False,
            error_code="SCHEMA_FAIL",
            error_detail=str(e)
        )
