from typing import List, Literal, Optional, Any
from pydantic import BaseModel, Field

class TravelConstraints(BaseModel):
    destination_region: str
    cities: List[str]
    duration_days: int
    budget_total: float
    currency: str = "USD"
    requested_currency: str = "INR"
    budget_in_inr: float = 0.0
    budget_in_usd: float = 0.0
    preferences: List[str]        # ["food", "temples"]
    avoidances: List[str]         # ["crowds"]
    hard_requirements: List[str]  # non-negotiable
    soft_preferences: List[str]   # nice-to-have

class ActivityItem(BaseModel):
    id: str  # stable ID for cross-agent reference
    city: str
    name: str
    type: str                     # "temple" | "food" | "transport" etc
    estimated_duration_hours: float
    crowd_level: Literal["low", "medium", "high"]
    cost_band: Literal["free", "low", "medium", "high"]
    must_do: bool
    rationale: str

class ActivityCatalog(BaseModel):
    activities: List[ActivityItem]
    crowd_level_summary: str
    cost_band_summary: str
    rationale: str

class LodgingItem(BaseModel):
    city: str
    hotel_name: str
    cost_per_night: float
    nights: int
    total_cost: float
    rationale: str

class LodgingPlan(BaseModel):
    lodgings: List[LodgingItem]
    total_lodging_cost: float

class MovementItem(BaseModel):
    from_city: str
    to_city: str
    transport_mode: str  # "train" | "flight" | "car" etc
    duration_minutes: int
    estimated_cost: float
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None

class MovementPlan(BaseModel):
    movements: List[MovementItem]
    total_movement_cost: float

class DayActivity(BaseModel):
    time_slot: Literal["AM", "PM", "Evening"]
    activity_id: str
    name: str
    duration_hours: float
    cost: float
    rationale: str

class DaySkeleton(BaseModel):
    day_number: int
    city: str
    activities: List[DayActivity]
    lodging_hotel_name: str
    notes: str

class BudgetCategory(BaseModel):
    category: str  # "lodging" | "transport" | "food" | "activities"
    total: float

class BudgetBreakdown(BaseModel):
    categories: List[BudgetCategory]
    total_estimated_cost: float
    total_inr: float = 0.0
    total_requested_currency: float = 0.0
    total_destination_currency: float = 0.0
    destination_currency_code: str = "USD"
    exchange_rates_used: dict = {}
    within_budget: bool
    violations: List[str]
    suggested_swaps: List[str]

class DraftItinerary(BaseModel):
    constraints: TravelConstraints
    activity_catalog: ActivityCatalog
    lodging_plan: LodgingPlan
    movement_plan: MovementPlan
    day_skeletons: List[DaySkeleton]
    budget_breakdown: BudgetBreakdown

class ReviewReport(BaseModel):
    passed: bool
    days_match: bool
    cities_included: bool
    within_budget: bool
    preference_alignment_score: float  # 0.0–1.0
    crowd_avoidance_effort: bool
    logistics_realistic: bool
    blocking_issues: List[str]
    advisory_issues: List[str]
    repair_hints: List[str]

class AgentResult(BaseModel):
    success: bool
    artifact: Optional[Any] = None
    error_code: Optional[str] = None     # "TIMEOUT" | "SCHEMA_FAIL" | "TOOL_ERROR" | "NULL_FIELD"
    error_detail: Optional[str] = None
    partial_data: Optional[Any] = None   # what we got before failure

class FinalItinerary(BaseModel):
    itinerary: DraftItinerary
    review_report: ReviewReport
    disclaimer: str
    version: int = 1
