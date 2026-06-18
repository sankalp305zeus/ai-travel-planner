# Problem Statement: Autonomous Multi-Agent Travel Planner

---

## The Problem

Planning a trip sounds simple. It is not.

A traveler says:

> **"Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples, hate crowds."**

To fulfill that well requires combining five distinct kinds of work simultaneously:
- **Semantic understanding** — what does "hate crowds" actually mean for activity selection?
- **Domain research** — which temples in Kyoto are genuinely less crowded?
- **Logistics sequencing** — how do you order 5 days to minimize backtracking?
- **Budget enforcement** — does the plan actually fit $3,000 once hotels + transport + food are summed?
- **Quality validation** — does the final plan actually match all the stated constraints?

No single LLM call does all five well. It either hallucinates costs, ignores the crowd constraint, or produces a structurally impossible itinerary (e.g., 3 cities in 1 day).

The result: travelers either over-rely on broken AI output, or spend 6–10 hours doing the work manually across 8+ browser tabs.

---

## The Objective

Build a **multi-agent system** where specialized AI agents collaborate — each owning one domain — to produce a validated, constraint-respecting travel plan from a single natural-language request.

This is an **educational + PM-demo** system, not a production booking platform. The goal is to demonstrate:
- How hub-and-spoke agent topology prevents hallucination cascades
- How typed data contracts enforce correctness between agents
- How a Review gate blocks bad output from reaching users
- How parallel execution reduces latency without sacrificing accuracy

---

## System Output

Given: one natural-language travel request
Produce:
- **Day-by-day itinerary** with AM/PM/Evening slots
- **Suggested neighborhoods** to stay in each city
- **Inter-city logistics** (transport mode, timing, cost)
- **Budget breakdown** by category (stay / transport / food / activities)
- **Validation report** — which constraints were met and how

---

## Constraints

- Plan must respect all hard constraints (duration, cities, budget cap)
- Plan must attempt all soft preferences (food, temples, crowd avoidance)
- Budget cannot be exceeded — budget agent flags and the review agent blocks
- Output is illustrative — all prices are estimates, no real bookings are made
- A legal disclaimer is mandatory on every delivered itinerary

---

## Agent System Design

### Architecture Pattern: Hub-and-Spoke
```
User Request
     ↓
[Orchestrator] — single source of TravelConstraints
     ↓ (parallel dispatch)
[Destination]  [Logistics]  [Budget]   ← workers never talk to each other
     ↓
[Orchestrator Merge] → DraftItinerary
     ↓
[Review / Sentinel] — hard gate
     ↓ pass
[Human Interrupt] — user approves before final delivery
     ↓
[FinalItinerary] → User
```

### Why Hub-and-Spoke (not Mesh or Swarm)
Agents communicating directly with each other create unbounded dialogue loops — Agent A asks Agent B for clarification, B asks A back, tokens burn infinitely. Hub-and-spoke makes this structurally impossible: workers can only receive tasks from the Orchestrator and return one typed artifact. No horizontal communication path exists.

### The Five Agents

**1. Orchestrator**
- Parses raw user request → extracts `TravelConstraints` (typed, validated, immutable)
- Dispatches to 3 workers in parallel
- Merges typed artifacts into `DraftItinerary`
- Sends to Review; on pass, triggers human interrupt; on fail, routes repair to specific failing agent (max 3 retries)

**2. Destination Research Agent**
- Consumes: `TravelConstraints`
- Uses: web search, places API (via MCP)
- Produces: `ActivityCatalog` — activities per city with crowd level, cost band, must-do flag, rationale

**3. Logistics Agent**
- Consumes: `TravelConstraints`
- Uses: transit API, geo distance, hotel search (via MCP)
- Produces: `LodgingPlan` + `MovementPlan` + `DaySkeleton[]`

**4. Budget Agent**
- Consumes: `TravelConstraints` + cost bands from `ActivityCatalog`
- Uses: FX converter, price estimator (via MCP)
- Produces: `BudgetBreakdown` — category totals, within_budget bool, violations, suggested_swaps

**5. Review Agent (Sentinel)**
- Consumes: `DraftItinerary` + `TravelConstraints`
- Layer 1: programmatic constraint checks (budget math, day count, city inclusion) — cannot be overridden by LLM
- Layer 2: LLM qualitative checks (preference alignment, crowd avoidance, narrative coherence)
- Produces: `ReviewReport` — pass/fail, blocking vs advisory issues, repair hints

---

## Technical Approach

- **Orchestration:** LangGraph (Python) — stateful graph, native parallel execution, time-travel checkpointing, bounded repair loops
- **Schema enforcement:** Pydantic AI — LLM outputs are validated against strict Pydantic v2 models before any downstream agent consumes them
- **External tools:** MCP servers — isolated, swappable, logged. Agents never call external APIs directly.
- **Observability:** Full trace per request (every prompt, tool call, artifact, Review result)
- **Evals:** Sprint-gated — no sprint closes unless its eval suite passes on the golden dataset

---

## Success Criteria

| Metric | Target |
|---|---|
| Constraint extraction accuracy | 100% on 10-case golden set |
| Review false positive rate | <5% (bad plans passed as good) |
| E2E pipeline latency | <45 seconds |
| Review pass on first attempt | >70% of runs |
| Budget accuracy | 100% (programmatic check, not LLM) |
| Repair resolution | 100% within 3 cycles or structured error returned |
