# FRONTEND_BLUEPRINT.md

## APP OVERVIEW
**Name:** Navigo — AI Travel Planner
**Stack:** React 19, Vite, Tailwind CSS, Recharts, Lucide React, ReactBits
**Deployment Target:** Vercel (frontend/dist)

## 1. DESIGN SYSTEM (STRICT TOKENS)
- Background: #0F0F0F
- Surface: #1A1A1A
- Border: #2A2A2A
- Text Primary: #F0EDE8
- Text Muted: #888580
- Accent Amber: #E8C547
- Accent Teal: #4ECDC4
- Accent Red: #EF4444
- font-heading: 'Playfair Display', serif
- font-body: 'Inter', sans-serif
- font-mono: 'JetBrains Mono', monospace

## 2. REACT BITS INSTALLATION
npx shadcn@latest add @react-bits/aurora-ts-tw
npx shadcn@latest add @react-bits/shiny-text-ts-tw
npx shadcn@latest add @react-bits/splash-cursor-ts-tw
npx shadcn@latest add @react-bits/blur-text-ts-tw

## 3. SCREENS

### SCREEN 1 — Request
- 100vh, 100vw, center-aligned
- Aurora component as fixed background (dark, subtle)
- ShinyText heading: "Where do you want to go?"
- Surface card #1A1A1A with border #2A2A2A over Aurora
- Large textarea, placeholder cycles every 3000ms through:
  "5 days Japan. Tokyo + Kyoto. $3,000. Love food and temples, hate crowds."
  "Weekend in Paris. €800. Art museums, no queues."
  "2 weeks Southeast Asia. Bangkok + Bali. $4,000. Beaches and food."
- Char counter in JetBrains Mono (e.g. 120/500)
- CTA button: bg #E8C547, text #0F0F0F, "Plan My Trip →"
- Disabled if length === 0 or > 500

### SCREEN 2 — Generating
- NO spinners anywhere
- SplashCursor active
- PipelineGraph showing 5 nodes:
  Row 1: Orchestrator
  Row 2: Destination | Logistics | Budget
  Row 3: Review
- Node states:
  waiting: border #888580, text #888580
  active: border #E8C547, text #E8C547, amber pulse animation
  complete: solid #4ECDC4, text #0F0F0F
  error: solid #EF4444, text #F0EDE8
- Right sidebar #1A1A1A: "Agent Outputs" heading, artifact preview in JetBrains Mono
- Poll GET /api/plan/{id}/status every 2000ms

### SCREEN 3 — Itinerary
- BlurText fade-in for day headers
- ActivityCard stack (left), BudgetChart sidebar (right)
- Fixed bottom disclaimer: bg #E8C547, text #0F0F0F, non-dismissable
  "AI-generated estimates. Confirm all prices, availability, and bookings independently."
- Footer: "Data attribution: OpenStreetMap & Wikivoyage (CC BY-SA 3.0)" text-muted text-xs

## 4. COMPONENTS

### TravelRequestForm.jsx
- State: text, charCount
- Props: onSubmit(text)
- Manages 3s cycling placeholder

### PipelineGraph.jsx
- Props: agents (object: name → {state, artifact})
- Renders 5 AgentNode components in hub-and-spoke layout

### AgentNode.jsx
- Props: name, state ('waiting'|'active'|'complete'|'error'), artifact
- Circular element, switch on state for colors

### ActivityCard.jsx
- Props: name, duration, crowd_level, cost_band, rationale
- Surface #1A1A1A, border #2A2A2A
- crowd_level badge: low=#4ECDC4, medium=#E8C547, high=#EF4444

### BudgetChart.jsx
- Props: budgetData (array of {category, amount})
- Recharts PieChart, innerRadius=60 (donut)
- Colors: #E8C547, #4ECDC4, #F0EDE8, #888580

## 5. STATE MANAGEMENT
useState and useEffect only. No Redux, Zustand, localStorage.

const [view, setView] = useState('request'); // 'request'|'generating'|'itinerary'
const [planId, setPlanId] = useState(null);
const [agentStatus, setAgentStatus] = useState({
  Orchestrator: { state: 'waiting', artifact: null },
  Destination: { state: 'waiting', artifact: null },
  Logistics: { state: 'waiting', artifact: null },
  Budget: { state: 'waiting', artifact: null },
  Review: { state: 'waiting', artifact: null }
});
const [itinerary, setItinerary] = useState(null);

## 6. API INTEGRATION
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

POST /api/plan → {plan_id}
GET /api/plan/{id}/status → {status, agents: {name: {state, artifact}}}
GET /api/plan/{id}/result → FinalItinerary JSON
