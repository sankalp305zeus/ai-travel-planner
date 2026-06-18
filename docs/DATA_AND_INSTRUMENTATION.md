# Data Sources, Fallback Strategy & Instrumentation Layer
> Addendum to BLUEPRINT.md — integrates into MCP server architecture and observability stack

---

## 1. Data Source Registry

Every MCP server uses a **tiered source strategy**: Primary → Fallback → Static Cache.
Agents never know which tier served them — they receive the same typed response regardless.

---

### MCP Server 1: `search_server` — Destination Content

| Tier | Source | What it provides | Cost | Notes |
|---|---|---|---|---|
| **Primary** | **Wikivoyage API** (Wikimedia Enterprise) | 142,000+ human-curated destination articles, POIs, itineraries, phrasebooks, crowd context | Free (open license) | No commercial bias, ad-free, consistent structured format per destination |
| **Secondary** | **Lonely Planet Content API** (`api.demo.content-api.lonelyplanet.com`) | 8,000+ city guides, do & see, restaurants, themed lists | API key required (B2B) | World's largest expert-curated travel data repository; filter by category |
| **Tertiary** | **Tripexpert API** (`api.tripexpert.com`) | Expert reviews aggregated from Lonely Planet, NYT, Fodor's, Condé Nast, Michelin | API key required | Normalized scores across 100+ publications; best for "is this place actually good?" |
| **Fallback** | **Static JSON cache** | 20 cities × top 15 POIs each, pre-curated | None | Bundled with app; always available offline; refreshed monthly |

**Wikivoyage is the anchor.** It contains over 142,000 articles, is built by 2.7 million users, human-curated and non-commercial — a clean dataset free from travel advertising, ideal for AI applications generating genuine user-focused advice. Every article follows a fixed subheading structure (Understand / Get In / See / Do / Eat / Sleep), making parsing deterministic.

```python
# search_server.py — tiered fetch pattern
async def get_destination_content(city: str, category: str) -> DestinationContent:
    try:
        return await wikivoyage_fetch(city, category)      # tier 1
    except WikivoyageError:
        try:
            return await lonely_planet_fetch(city, category)  # tier 2
        except LonelyPlanetError:
            return await static_cache_lookup(city, category)  # tier 3 — never fails
```

---

### MCP Server 2: `geo_server` — Location & Routing

| Tier | Source | What it provides | Cost | Notes |
|---|---|---|---|---|
| **Primary** | **OpenStreetMap Nominatim** | Geocoding: city → lat/lon, address lookup | Free | Run own instance for rate-limit freedom or use public API (1 req/s limit) |
| **Primary** | **OSM Overpass API** | POI queries: temples in Kyoto within 5km, restaurants near a hotel | Free | SQL-like query language; returns tagged nodes with GPS coordinates |
| **Secondary** | **GraphHopper Routing API** | Road distances, walking/transit time estimates between two points | Free tier (500 req/day) | Open source, self-hostable; uses OSM data |
| **Secondary** | **OpenTripPlanner** | Multi-modal trip planning (walk + transit + rail) | Free, self-hosted | Ideal for "how to get from Tokyo to Kyoto with options" |
| **Tertiary** | **Geofabrik regional extracts** | Pre-processed OSM data for specific regions (Japan, Europe etc.) | Free | Downloaded once, queried locally — zero API latency |
| **Fallback** | **Static distance matrix** | Pre-computed city-to-city transit times + recommended transport modes | None | Bundled JSON: 50 common city pairs |

OSM data forms the foundation for downstream services like routing (OSRM, GraphHopper), geocoding (Nominatim), and structured spatial datasets. Overpass API enables targeted queries extracting specific features — every temple in a region, cycling paths, building footprints.

---

### MCP Server 3: `pricing_server` — Budget Data

| Tier | Source | What it provides | Cost | Notes |
|---|---|---|---|---|
| **Primary** | **Open-Meteo** (weather, not pricing) | Seasonal crowd context by month/city — "April in Kyoto = peak cherry blossom = extreme crowds" | Free, no key | Informs crowd_level and "avoid this month" signals |
| **Primary** | **OpenTravelData (OPTD)** | Airports, airlines, routes, base pricing bands for air transport | Free (GitHub) | `opentraveldata/opentraveldata` — CSV datasets for offline use |
| **Secondary** | **Static pricing tables** (bundled JSON) | Hotel cost bands (budget/mid/luxury) × city × season; meal cost averages; activity entry prices | None | Researched and bundled; accurate enough for "illustrative" demo tier |
| **Secondary** | **FX: Open Exchange Rates API** | Live currency conversion (USD ↔ JPY, EUR, etc.) | Free tier (1000 req/mo) | Fallback: static rates refreshed weekly |
| **Fallback** | **Hardcoded band estimates** | Budget trip = $80/night hotel + $30/day food + $15/day activities (per city tier) | None | Last-resort budget math that always produces a result |

---

### MCP Server 4: `weather_server` — Seasonal Context

| Tier | Source | What it provides | Cost | Notes |
|---|---|---|---|---|
| **Primary** | **Open-Meteo Historical + Forecast API** | Temperature, rainfall, "comfortable travel months" per destination | Free, no API key | REST API, no auth, no rate limit abuse |
| **Secondary** | **Wikipedia Climate Data** (via Wikimedia API) | Climate tables per city (avg temp/rain by month) | Free | Parsed from Wikipedia infoboxes; good enough for "avoid rainy season" |
| **Fallback** | **Static seasonal guide JSON** | Bundled: 50 cities × 12 months × (crowd_level, weather_rating, notes) | None | e.g., Kyoto in April → `{crowd: "extreme", weather: "excellent", note: "cherry blossom peak"}` |

---

## 2. Static Fallback Cache Design

The app ships with a bundled `data/` folder. Every MCP server falls through to it when all live sources fail.

```
backend/data/
  destinations/
    tokyo.json          # top 20 POIs: name, type, crowd_level, cost_band, coords, rationale
    kyoto.json
    paris.json
    ...  (50 cities)
  logistics/
    transit_matrix.json  # {from, to, mode, duration_minutes, cost_band}
  pricing/
    city_cost_bands.json # {city, hotel_budget/mid/luxury, meal_avg, activity_avg}
    fx_rates.json        # updated weekly, fallback if Open Exchange Rates is down
  seasonal/
    crowd_calendar.json  # {city, month, crowd_level, weather_note}
```

**Cache rules:**
- Cache is read-only. It is never mutated by agents.
- Cache entries have a `data_vintage` field (when last verified). Review agent surfaces this as an advisory if vintage > 6 months.
- Cache is the final fallback — it always returns a value. Zero null propagation.

---

## 3. Instrumentation Stack

### Standard: OpenTelemetry → Langfuse

Every trace in the system uses **OpenTelemetry (OTEL)** as the instrumentation standard — not a proprietary SDK. This means zero vendor lock-in. One SDK in your code (OpenTelemetry), many backends to choose from — Langfuse, LangSmith, Datadog, New Relic. Switching observability backends is a configuration change, not a code rewrite.

**Recommended backend: Langfuse** — open-source, free tier of 50k observations/month, no credit card required, works with any model and any framework, with a ClickHouse backend that queries millions of traces in milliseconds.

```python
# backend/instrumentation.py — one-time setup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

LANGFUSE_AUTH = base64.b64encode(
    f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()
).decode()

exporter = OTLPSpanExporter(
    endpoint=f"{LANGFUSE_BASE_URL}/api/public/otel",
    headers={"Authorization": f"Basic {LANGFUSE_AUTH}"}
)
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)
```

---

### What Every Span Must Capture

**Mandatory attributes on every span (propagate to all child spans via OTel Baggage):**

```python
# Trace-level (propagated to ALL spans in the trace)
trace_id:          str     # UUID, generated at request entry
session_id:        str     # same user session
user_request_hash: str     # hash of raw input (for grouping similar requests)
plan_version:      int     # repair loop iteration count

# Span-level (per operation)
span.agent_name:   str     # "orchestrator" | "destination" | "logistics" | "budget" | "review"
span.operation:    str     # "extract_constraints" | "fetch_pois" | "merge_artifacts" | ...
span.data_source:  str     # "wikivoyage" | "lonely_planet" | "static_cache" | ...
span.data_tier:    int     # 1=primary | 2=secondary | 3=fallback

# LLM call spans
gen_ai.system:           str     # "google" | "anthropic"
gen_ai.request.model:    str     # "gemini-2.5-flash-lite"
gen_ai.usage.input_tokens:  int
gen_ai.usage.output_tokens: int
gen_ai.request.temperature: float
llm.prompt_template_id:  str     # version-pinned prompt ID (stored in Langfuse Prompt Management)
llm.schema_validation:   bool    # did Pydantic AI pass?
llm.retry_count:         int     # how many times this call was retried

# MCP tool call spans
mcp.server:      str     # "search_server" | "geo_server" | "pricing_server"
mcp.tool:        str     # "wikivoyage_fetch" | "nominatim_geocode" | ...
mcp.latency_ms:  int
mcp.cache_hit:   bool
mcp.tier_used:   int     # 1 | 2 | 3
```

---

### Metrics to Track in Langfuse Dashboard

| Metric | How to measure | Alert threshold |
|---|---|---|
| E2E latency (P50/P95/P99) | Trace duration | P95 > 45s → alert |
| LLM call latency per agent | Span duration on gen_ai spans | Any agent > 10s → warn |
| Schema validation failure rate | `llm.schema_validation=false` count | > 5% of traces → alert |
| MCP tool fallback rate | `mcp.tier_used` > 1 | > 20% of calls → warn |
| Review pass rate (first attempt) | `review.passed=true AND plan_version=1` | < 60% → alert |
| Repair loop exhaustion rate | `error_code=REPAIR_EXHAUSTED` | > 2% → alert |
| Budget accuracy | `budget.within_budget` vs actual sum | Any mismatch → alert |
| Token cost per request | Sum of `gen_ai.usage.*_tokens` × model price | > $0.05/request → warn |

---

### LLM-as-Judge Eval (Production Continuous Quality)

Every 20th production trace (5%) is sent to a stronger judge model for quality scoring:

```python
# backend/evals/production_judge.py
JUDGE_PROMPT = """
You are evaluating a travel itinerary against the original user request.
Score 0–10 on each dimension:
1. constraint_adherence: Does it match duration, cities, budget?
2. preference_satisfaction: Does it reflect the traveler's stated preferences?
3. avoidance_respect: Does it avoid the stated avoidances (e.g. crowds)?
4. logistics_realism: Are the travel times and sequences physically possible?
5. plan_coherence: Is the day-by-day narrative logical and useful?

User request: {request}
Itinerary: {itinerary}
Review report: {review_report}

Return JSON only: {"scores": {...}, "overall": float, "flags": [...]}
"""
```

Store judge scores in Langfuse as `score` objects on the trace. Surface regressions when overall score drops > 0.5 points week-over-week.

---

## 4. Prompt Version Control

All LLM prompts are managed in **Langfuse Prompt Management**, not hardcoded in source files.

```python
# backend/prompts.py
from langfuse import get_client

langfuse = get_client()

def get_prompt(name: str, version: int = None) -> str:
    """Fetch versioned prompt from Langfuse. Falls back to local file if Langfuse is down."""
    try:
        prompt = langfuse.get_prompt(name, version=version)
        return prompt.compile()
    except Exception:
        return load_local_prompt(name)  # local .txt fallback
```

**Prompts to version-control:**
- `orchestrator.extract_constraints` — extraction prompt
- `destination.research_pois` — destination research prompt
- `logistics.build_skeleton` — day skeleton prompt  
- `budget.validate_breakdown` — budget narrative prompt
- `review.qualitative_check` — Review Layer 2 prompt
- `orchestrator.merge_narrative` — final itinerary prose prompt

Benefits: A/B test prompt versions, roll back bad prompts without a code deploy, see which prompt version produced which trace.

---

## 5. Fallback Decision Tree (complete)

```
For any agent output request:
│
├─ Is live API available? (health check on startup)
│   ├─ YES → use primary source
│   │         if primary fails (timeout / error) → use secondary
│   │         if secondary fails → use static cache
│   │         log mcp.tier_used on every call
│   │
│   └─ NO (startup health check failed) → skip to static cache immediately
│                                         log WARN: "degraded mode, tier=3"
│
├─ Did agent return null for any required field?
│   └─ YES → return AgentResult(success=False, error_code="NULL_FIELD", partial_data=...)
│            DO NOT pass null downstream — Review will block it but better to catch early
│
└─ Did schema validation fail?
    └─ YES → retry LLM call once with explicit repair prompt
             if still fails → return AgentResult(success=False, error_code="SCHEMA_FAIL")
             Orchestrator routes to structured error response, not hallucinated content
```

---

## 6. Data Attribution Rules

- Wikivoyage data requires attribution: "Travel information from Wikivoyage, CC BY-SA 3.0"
- OSM data requires attribution: "Map data © OpenStreetMap contributors"
- Both attributions must appear in the UI footer on every itinerary screen
- Lonely Planet content requires commercial license (B2B API) — check ToS before shipping
- All prices marked as "estimated ranges" — never presented as guaranteed rates
- `data_vintage` surfaced on itinerary when static cache is used: "Based on data from [month/year]"
