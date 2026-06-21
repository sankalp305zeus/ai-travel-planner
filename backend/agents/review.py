import os
from typing import List, Optional
from pydantic_ai import Agent
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.models.groq import GroqModel
from backend.schemas import TravelConstraints, DraftItinerary, ReviewReport, AgentResult
from backend import config

# Initialize Pydantic AI agent for Layer 2 qualitative checks
if config.GROQ_API_KEY and config.GROQ_API_KEY != "mock_key":
    provider = GroqProvider(api_key=config.GROQ_API_KEY)
    model = GroqModel('llama-3.3-70b-versatile', provider=provider)
    agent = Agent(
        model,
        output_type=ReviewReport,
        system_prompt=(
            "You are an expert travel critic.\n"
            "Analyze the provided DraftItinerary against the TravelConstraints.\n"
            "Evaluate the qualitative aspects of the itinerary and return a ReviewReport:\n"
            "- preference_alignment_score: float (0.0 to 1.0) indicating how well the itinerary matches user preferences.\n"
            "- crowd_avoidance_effort: bool indicating if the itinerary avoids the user's avoidances.\n"
            "- logistics_realistic: bool indicating if the routing and scheduling are realistic.\n"
            "- blocking_issues: list of severe qualitative problems (e.g. logically impossible sequences).\n"
            "- advisory_issues: list of minor warnings.\n"
            "- repair_hints: list of actionable tips to fix failures.\n"
            "Return ONLY the validated JSON matching the ReviewReport schema."
        )
    )
else:
    agent = None


async def review_destination_itinerary(draft: DraftItinerary, constraints: TravelConstraints) -> ReviewReport:
    """
    Validates the itinerary draft against travel constraints.
    Runs a programmatic Layer 1 check first. If it fails, Layer 2 LLM is completely bypassed.
    """
    # 1. Programmatic Layer 1 checks
    days_match = len(draft.day_skeletons) == constraints.duration_days
    
    # Check that all constraints cities are in the day skeletons (case-insensitive)
    skeleton_cities = {day.city.strip().lower() for day in draft.day_skeletons}
    cities_included = all(c.strip().lower() in skeleton_cities for c in constraints.cities)
    
    # Check budget total
    within_budget = draft.budget_breakdown.total_estimated_cost <= constraints.budget_total
    
    # Check null/empty required fields
    null_fields = []
    if not constraints.destination_region:
        null_fields.append("Missing destination region in constraints.")
    if not draft.day_skeletons:
        null_fields.append("Missing day skeletons in draft.")
    for day in draft.day_skeletons:
        if not day.city:
            null_fields.append(f"Missing city for Day {day.day_number}.")
        if day.lodging_hotel_name is None:
            null_fields.append(f"Missing lodging hotel for Day {day.day_number}.")
            
    blocking_issues = []
    if not days_match:
        blocking_issues.append(f"Day count mismatch: requested {constraints.duration_days} days, got {len(draft.day_skeletons)} days.")
    if not cities_included:
        missing = [c for c in constraints.cities if c.strip().lower() not in skeleton_cities]
        blocking_issues.append(f"Missing cities in plan: {', '.join(missing)}")
    if not within_budget:
        blocking_issues.append(f"Over budget: estimated {draft.budget_breakdown.total_estimated_cost:.2f} {constraints.currency} exceeds limit of {constraints.budget_total:.2f} {constraints.currency}.")
    blocking_issues.extend(null_fields)
    
    if len(blocking_issues) > 0:
        # Layer 1 failure -> skip Layer 2 LLM
        return ReviewReport(
            passed=False,
            days_match=days_match,
            cities_included=cities_included,
            within_budget=within_budget,
            preference_alignment_score=0.0,
            crowd_avoidance_effort=False,
            logistics_realistic=False,
            blocking_issues=blocking_issues,
            advisory_issues=[],
            repair_hints=[f"Fix programmatic errors: {'; '.join(blocking_issues)}"]
        )
        
    # 2. Layer 2 LLM checks (only run if Layer 1 passes)
    if not config.GROQ_API_KEY or config.GROQ_API_KEY == "mock_key":
        # Mock Layer 2 fallback
        return ReviewReport(
            passed=True,
            days_match=True,
            cities_included=True,
            within_budget=True,
            preference_alignment_score=0.9,
            crowd_avoidance_effort=True,
            logistics_realistic=True,
            blocking_issues=[],
            advisory_issues=[],
            repair_hints=[]
        )
        
    try:
        prompt = (
            f"Review this Draft Itinerary against constraints:\n"
            f"Constraints:\n{constraints.model_dump_json(indent=2)}\n\n"
            f"Draft Itinerary:\n{draft.model_dump_json(indent=2)}"
        )
        res = await agent.run(prompt)
        report = res.output
        
        # Force correct programmatic variables
        report.days_match = True
        report.cities_included = True
        report.within_budget = True
        report.passed = len(report.blocking_issues) == 0
        return report
    except Exception as e:
        return ReviewReport(
            passed=False,
            days_match=True,
            cities_included=True,
            within_budget=True,
            preference_alignment_score=0.0,
            crowd_avoidance_effort=False,
            logistics_realistic=False,
            blocking_issues=[f"LLM review failed: {str(e)}"],
            advisory_issues=[],
            repair_hints=["Retry LLM review or verify API key connection."]
        )
