# CLAUDE.md

## Project
AI Travel Planner — multi-agent system that turns a natural-language travel request into a validated itinerary.

## Stack
- **Backend:** Python (FastAPI) — agents, orchestration, LLM calls
- **Frontend:** React + Vite — request UI + itinerary display
- **LLM:** Gemini 2.5 Flash Lite (cheap, fast) via API
- **Agent pattern:** Hub-and-spoke (Orchestrator → parallel workers → Review)

## Docs (read before coding)
- `docs/problemStatement.md` — what we're building and why
- `docs/architecture.md` — agent topology, data contracts, deployment
- `docs/implementation-plan.md` — phase-wise plan with sprint boundaries
- `docs/PRD.md` — product requirements (generated in Sprint 1)

## Agents
| Agent | File | Input | Output |
|---|---|---|---|
| Orchestrator | `backend/agents/orchestrator.py` | raw user string | FinalItinerary |
| Destination | `backend/agents/destination.py` | TravelConstraints | ActivityCatalog |
| Logistics | `backend/agents/logistics.py` | TravelConstraints | LodgingPlan + MovementPlan |
| Budget | `backend/agents/budget.py` | TravelConstraints + ActivityCatalog | BudgetBreakdown |
| Review | `backend/agents/review.py` | DraftItinerary + TravelConstraints | ReviewReport |

## Key rules
1. `TravelConstraints` is the single source of truth — workers never re-parse the raw string
2. Workers are stateless — no shared mutable state between agents
3. Review is a hard gate — never skip it
4. LLM keys live only in `backend/.env` — never in frontend
5. Update `docs/implementation-plan.md` sprint status at the end of every session

## API contract
`POST /api/plan` — body: `{ "request": "..." }` → returns `FinalItinerary` JSON

## End of session checklist
- [ ] Update implementation-plan.md with what was completed this sprint
- [ ] Note any broken state or partial work in implementation-plan.md
- [ ] Commit with message: `sprint-N: <summary>`
