# S-Tier Master Blueprint: Autonomous Multi-Agent Travel Planner
> Version 2.0 — Production-Grade, Eval-Gated, Failure-Proof

---

## 1. Golden Rules (Non-Negotiable)

These cannot be violated by any sprint, agent, or shortcut:

1. **TravelConstraints is immutable** — extracted once by Orchestrator, read-only for all workers. Workers never re-parse raw user input.
2. **Hub-and-spoke is absolute** — workers never call each other. No mesh. No swarm. Violation = infinite loop.
3. **Review is a hard gate** — the user never sees output that hasn't passed Review. Never bypass for speed.
4. **LLM keys stay server-side** — zero secrets in browser, zero secrets in frontend build artifacts.
5. **Typed artifacts over free-form text** — every agent returns a validated Pydantic schema, not a prose string.
6. **Evals gate every sprint** — no sprint is "done" unless its eval suite passes. No silent failures.
7. **Repair loops are bounded** — max 3 retries. On third failure, return a structured error with diagnostics, not a hallucinated plan.
8. **Every LLM call is logged** — prompt sent, raw response, parsed artifact, validation result. No black boxes.

---

## 2. Technology Stack

### Backend (Python Route — Recommended)
| Layer | Choice | Why |
|---|---|---|
| API framework | **FastAPI** | Async, OpenAPI auto-gen, clean dependency injection |
| Orchestration | **LangGraph** | Stateful graph, native parallel execution, time-travel interrupts, bounded retry loops |
| Schema validation | **Pydantic v2 + Pydantic AI** | Mathematically enforces LLM output schemas; blocks hallucinated keys |
| LLM provider | **Gemini 2.5 Flash Lite** (primary) | Fast, cheap, good structured output |
| LLM fallback | **Claude claude-sonnet-4-6** | Richer reasoning for merge + Review qualitative pass |
| External tools | **MCP servers** | Isolated, swappable, auditable tool execution |
| Observability | **LangSmith** (or self-hosted Langfuse) | Full trace per request: every prompt, tool call, artifact |
| Evals | **Pytest + custom eval harness** | Sprint-gated, golden dataset, regression-blocking |

### Frontend
| Layer | Choice | Why |
|---|---|---|
| Framework | **React + Vite** | Fast, decoupled, no secrets |
| Styling | **Tailwind CSS + custom design tokens** | Utility-first, consistent |
| State | **Zustand** | Lightweight, no Redux overhead |
| Streaming | **SSE (Server-Sent Events)** | Show agent progress in real-time without polling |
| Admin viz | **React Flow** | Agent graph visualization for /admin route |

### TypeScript Alternative
Replace FastAPI + LangGraph + Pydantic AI with **Mastra** — native `.then()/.branch()/.parallel()` graph primitives + built-in 4-tier memory. Same principles apply.

---

## 3. Agent Architecture

### Pipeline
```
User Input
    ↓
[Orchestrator] — extracts TravelConstraints (Pydantic AI, low temp)
    ↓
[Parallel: Destination | Logistics | Budget] — all consume same read-only TravelConstraints
    ↓
[Orchestrator Merge] — produces DraftItinerary
    ↓
[Review / Sentinel] — Layer 1: programmatic checks → Layer 2: LLM qualitative pass
    ↓ pass          ↓ fail (max 3 retries → route to specific failing agent)
[Human-in-the-Loop Interrupt] — user approves DraftItinerary + ReviewReport
    ↓
[Final Itinerary] → User
```

### Agent Contracts

**Orchestrator (Hub)**
- Input: raw user string
- Step 1: extract → `TravelConstraints` (Pydantic AI, temp=0.1)
- Step 2: dispatch to 3 workers in parallel
- Step 3: merge artifacts → `DraftItinerary`
- Step 4: send to Review
- Step 5: on pass → trigger human interrupt → compile `FinalItinerary`

**Destination Research Agent**
- Input: `TravelConstraints`
- Tools (via MCP): `web_search`, `places_api`, `reviews_scraper`
- Output: `ActivityCatalog` — per city: activities[], crowd_level, cost_band, must_do flag, rationale

**Logistics Agent**
- Input: `TravelConstraints`
- Tools (via MCP): `transit_api`, `geo_distance`, `hotel_search`
- Output: `LodgingPlan` + `MovementPlan` + `DaySkeleton[]`

**Budget Agent**
- Input: `TravelConstraints` + `ActivityCatalog` (cost bands from Destination)
- Tools (via MCP): `fx_converter`, `price_estimator`
- Output: `BudgetBreakdown` — per category totals, within_budget bool, violations[], suggested_swaps[]

**Review Agent (Sentinel)**
- Input: `DraftItinerary` + `TravelConstraints`
- Layer 1 (programmatic, cheap): day count matches, cities included, budget ≤ cap, no null fields
- Layer 2 (LLM qualitative, small model): preference alignment, crowd avoidance effort, logistics realism
- Output: `ReviewReport` — boolean checklist, severity per issue (blocking vs advisory), RepairHints[]

### System Prompt Rules (per Odyssey principles)
- Every agent prompt lists exactly what tools it has and **what it cannot do**
- Hub prompt: explicit routing logic for all 5 spokes
- Sub-agent `maxIterations: 6` (never unbounded)
- All prompts end with: "Return ONLY valid JSON matching the schema. Do not add prose."

---

## 4. Typed Data Contracts (Pydantic Schemas)

```python
# Every agent I/O is a strict Pydantic v2 model

class TravelConstraints(BaseModel):
    destination_region: str
    cities: list[str]
    duration_days: int
    budget_total: float
    currency: str = "USD"
    preferences: list[str]        # ["food", "temples"]
    avoidances: list[str]         # ["crowds"]
    hard_requirements: list[str]  # non-negotiable
    soft_preferences: list[str]   # nice-to-have

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

class ReviewReport(BaseModel):
    passed: bool
    days_match: bool
    cities_included: bool
    within_budget: bool
    preference_alignment_score: float  # 0.0–1.0
    crowd_avoidance_effort: bool
    logistics_realistic: bool
    blocking_issues: list[str]
    advisory_issues: list[str]
    repair_hints: list[str]
```

---

## 5. MCP Server Architecture

All external tool calls are isolated inside MCP servers. Agents never call external APIs directly.

```
backend/
  mcp_servers/
    search_server.py       # Wikivoyage (primary) → Lonely Planet → Tripexpert → static cache
    geo_server.py          # OSM Nominatim + Overpass → GraphHopper → static distance matrix
    pricing_server.py      # OpenTravelData + FX API → static cost bands
    weather_server.py      # Open-Meteo → Wikipedia climate → static seasonal guide
  data/                    # bundled static fallback datasets (never null)
    destinations/          # 50 cities × top 20 POIs
    logistics/             # transit matrix
    pricing/               # city cost bands + FX rates
    seasonal/              # crowd calendar
```

**Every MCP server uses a 3-tier strategy: Primary → Secondary → Static Cache.**
Agents receive the same typed response regardless of which tier served them.
`mcp.tier_used` is logged on every call. If tier > 1 appears > 20% of calls → alert.

**Full data source registry and fallback decision tree: see `DATA_AND_INSTRUMENTATION.md`**

**MCP golden rules:**
- Each server has one domain (single-responsibility)
- Every tool call logged: server, tool, input, output, latency, tier_used, cache_hit
- Timeouts enforced per tool call (max 10s)
- Identical queries within a session → cached (same query = same snippet)
- Mock servers for tests, real servers for prod — swappable via env var
- Static cache ships with app — zero network dependency at fallback tier
- Data attribution (Wikivoyage CC BY-SA 3.0, OSM ODbL) displayed in UI footer

---

## 6. Eval Framework

### Eval Suite Structure
```
tests/
  evals/
    test_constraint_extraction.py   # Sprint 1 gate
    test_destination_agent.py       # Sprint 2 gate
    test_logistics_agent.py         # Sprint 3 gate
    test_budget_agent.py            # Sprint 3 gate
    test_parallel_merge.py          # Sprint 4 gate
    test_review_agent.py            # Sprint 5 gate
    test_repair_loop.py             # Sprint 5 gate
    test_e2e_golden.py              # Sprint 6+ regression suite
```

### Golden Dataset (10 test cases minimum)
```json
[
  {
    "input": "5 days Japan, Tokyo + Kyoto, $3000, love food and temples, hate crowds",
    "expect": {
      "cities": ["Tokyo", "Kyoto"],
      "duration_days": 5,
      "budget_total": 3000,
      "preferences_include": ["food", "temples"],
      "avoidances_include": ["crowds"]
    }
  },
  {
    "input": "Weekend in Paris, €500, art museums, no queues",
    ...
  }
]
```

### Eval Metrics Per Agent
| Agent | Metric | Threshold |
|---|---|---|
| Orchestrator extraction | Schema validation pass rate | 100% on golden set |
| Destination | Crowd_level populated, must_do present | 100% |
| Budget | within_budget bool accurate vs actual sum | 100% |
| Review | False positive rate (passes bad plans) | <5% |
| E2E | Full pipeline under 45s | >90% of runs |
| E2E | Review pass on first attempt | >70% of runs |

### TDD Protocol (RED-GREEN-REFACTOR)
Every feature: **write failing test first → implement → confirm green → commit**
Sprint is blocked from closing if any eval is red.

---

## 7. Failure-Proofing

### Pre-Mortem: Top 10 Ways This System Fails

| # | Failure Mode | Cause | Prevention |
|---|---|---|---|
| 1 | Orchestrator extracts wrong duration | LLM parses "weekend" as 2 days incorrectly | Pydantic AI with explicit duration normalization prompt |
| 2 | Budget agent doesn't catch over-budget plan | Destination agent returns wrong cost_bands | Review Layer 1 programmatic check catches this independently |
| 3 | Infinite repair loop | Review keeps failing, repair hints are bad | Hard cap: 3 retries, then structured error returned |
| 4 | Parallel agents return inconsistent city names | "Kyoto" vs "Kyōto" | Normalize city names in TravelConstraints before dispatch |
| 5 | MCP tool timeout causes silent null | Network delay, API rate limit | Per-tool timeout + fallback value + log warning |
| 6 | LLM hallucinates activity IDs | Model invents fake stable IDs | IDs are generated by code, not LLM |
| 7 | Review passes a bad plan | Qualitative check too lenient | Separate programmatic Layer 1 runs first; it cannot be overridden by LLM |
| 8 | User sees partial/broken itinerary | Frontend renders before Review passes | Frontend only receives response after Review gate + human interrupt |
| 9 | Context window overload in Orchestrator merge | All 3 agent outputs dumped into one prompt | Structured artifact merging in code, not in a single LLM prompt |
| 10 | Session state lost mid-execution | Server restart, timeout | LangGraph checkpointing persists state to SQLite/Redis |

### Error Handling Protocol
```python
# Every agent returns either artifact OR structured error — never raises uncaught exception
class AgentResult(BaseModel):
    success: bool
    artifact: Optional[Any]
    error_code: Optional[str]     # "TIMEOUT" | "SCHEMA_FAIL" | "TOOL_ERROR"
    error_detail: Optional[str]
    partial_data: Optional[Any]   # what we got before failure
```

### Circuit Breaker Pattern
- If an MCP tool fails 3 times in a session → mark it degraded, use fallback data
- If an agent fails → return partial plan with explicit "missing [section]" rather than hallucinating

---

## 8. Observability Stack

**Standard: OpenTelemetry → Langfuse**
Instrument once with OpenTelemetry (vendor-neutral standard). Point at Langfuse (open-source, 50k obs/month free, self-hostable). Switch backends with a config change — no code rewrite. LangGraph has native Langfuse integration.

**Full OTEL span schema, all metric thresholds, LLM-as-Judge eval setup, and prompt version control strategy: see `DATA_AND_INSTRUMENTATION.md` section 3–5.**

Every request gets a `trace_id` propagated to all child spans via OTel Baggage. Every trace captures:
- Raw user input + TravelConstraints extraction (prompt + raw response + validation result)
- Per-agent: input, all MCP tool calls (server/tool/params/result/tier_used), output artifact, latency
- Merge artifact, Review report (all layer 1 + layer 2 checks), repair attempts
- Final itinerary + total tokens + estimated cost per request

**Langfuse Dashboard Alerts:**
- P95 E2E latency > 45s → alert
- Schema validation failure > 5% → alert  
- MCP fallback tier > 1 on > 20% of calls → warn
- Review pass rate (first attempt) < 60% → alert
- Any `error_code=REPAIR_EXHAUSTED` → alert immediately

**Log levels:**
- `INFO`: request received, agent dispatched, artifact returned, data tier used
- `WARN`: MCP tool slow (>5s), repair loop triggered, static cache used, data vintage > 6 months
- `ERROR`: schema validation fail, agent timeout, Review hard block, null field propagated

---

## 9. UI Design System

### Visual Identity
**Concept:** "Precision travel intelligence" — not a consumer travel app, not a bland dashboard. Think: an architect's travel journal. Clean, purposeful, with one bold typographic moment.

**Color Tokens**
```
--color-bg:        #0F0F0F      /* near-black base */
--color-surface:   #1A1A1A      /* card / panel */
--color-border:    #2A2A2A      /* subtle dividers */
--color-accent:    #E8C547      /* amber gold — warmth of travel */
--color-accent-2:  #4ECDC4      /* teal — agent pipeline nodes */
--color-text:      #F0EDE8      /* warm white — not harsh */
--color-muted:     #888580      /* secondary labels */
--color-success:   #5CB85C
--color-warn:      #E8A547
--color-error:     #E85C47
```

**Typography**
```
Display:  "Playfair Display" — used for destination names, itinerary day headers only
Body:     "Inter" — all UI text, labels, data
Mono:     "JetBrains Mono" — agent debug logs, JSON artifacts in /admin
Scale:    12 / 14 / 16 / 20 / 28 / 40px
```

**Signature element:** The agent pipeline visualization (visible on main page during generation) — each agent node pulses amber when active, fills teal when complete. This IS the loading state. Not a spinner.

### Key Screens

**1. Request Screen**
- Full-width dark canvas
- Single large textarea: "Describe your trip..." — placeholder cycles through example requests
- Amber "Plan My Trip →" CTA
- No clutter. Just the input.

**2. Generation Screen (replaces loading spinner)**
- Live agent pipeline visualization (React Flow)
- 5 nodes: Orchestrator → [Destination | Logistics | Budget] → Review
- Each node: status (waiting/active/complete/error), live token count, elapsed time
- SSE stream feeds node state in real-time
- Partial artifact preview appears as agents complete (right sidebar)

**3. Itinerary Screen**
- Day-by-day tabs (Day 1, Day 2...)
- Each day: AM / PM / Evening slots with activity cards
- Activity card: name, duration, cost band, crowd level badge, rationale
- Budget breakdown sticky sidebar (donut chart by category)
- "Review passed" badge with score
- Disclaimer: "AI-generated plan — verify all bookings independently"

**4. /admin Route (Hackathon Demo)**
- Full agent workflow replay for last run
- Step-through (← →) or Play mode (0.5x / 1x / 2x speed)
- Each step shows: agent name, input params, LLM prompt, raw LLM response, parsed artifact, validation result
- Highlighted: which steps called LLM, which called MCP tools, where repair loop triggered
- Export trace as JSON button

---

## 10. Security & Safety

- API keys in `.env` only — never committed, never in frontend
- `.gitignore` enforced from Sprint 0: `.env`, `*.key`, `/node_modules`, `__pycache__`
- Rate limiting on `POST /api/plan`: 10 req/min per IP
- Input sanitization: max 500 chars on user travel request
- Output disclaimer mandatory: displayed on every itinerary, non-removable
- No PII required — system works entirely on destination/preference data
- MCP servers run in isolated subprocesses (not in main API process)

---

## 11. Sprint Map

| Sprint | Focus | Eval Gate |
|---|---|---|
| 0 | Skeleton: FastAPI + LangGraph + folder structure + .env + CLAUDE.md | Server starts, `/health` returns 200, .env gitignored |
| 1 | TravelConstraints Pydantic schema + Orchestrator extraction node | 10/10 golden set extractions pass schema validation |
| 2 | Destination agent + MCP search server (mock) | ActivityCatalog schema valid, crowd_level always populated |
| 3 | Logistics + Budget agents + MCP geo/pricing servers (mock) | LodgingPlan + BudgetBreakdown valid, within_budget accurate |
| 4 | LangGraph parallel execution + Orchestrator merge → DraftItinerary | Parallel runs < 15s, DraftItinerary passes structural checks |
| 5 | Review agent (Layer 1 + Layer 2) + bounded repair loop | Review catches injected bad plans (100%), repair resolves in ≤ 3 cycles |
| 6 | Human-in-the-loop interrupt + LangGraph checkpointing | Execution pauses, resumes after approval, state survives server restart |
| **7** | **Real data sources + tiered fallback + OTEL instrumentation** | **Wikivoyage/OSM live, static cache fallback works, full Langfuse trace visible** |
| 8 | Frontend: request form + SSE agent pipeline viz + itinerary screen | UI renders itinerary, pipeline nodes update live, mobile responsive |
| 9 | /admin route: agent workflow replay with step-through + play mode | All 5 agents visible, prompts + responses inspectable, export works |
| 10 | Product signoff: eval audit + PRD deviation report | PRODUCT_QUALITY_SIGNOFF.md generated, all blocking issues resolved |

**Sprint 7 detail:** Wire Wikivoyage API (primary), OSM Nominatim + Overpass (geo), Open-Meteo (weather), OpenTravelData + FX API (pricing). Confirm 3-tier fallback by killing each primary and asserting static cache responds. Wire OTEL → Langfuse: every span has mandatory attributes, every LLM call has `gen_ai.*` attributes, mcp.tier_used logged on every tool call. Confirm full trace visible in Langfuse dashboard for a golden test run.
