import asyncio, os
from dotenv import load_dotenv
load_dotenv()
from backend.graph import run_travel_planner_graph
r1 = asyncio.run(run_travel_planner_graph("5 days Tokyo + Kyoto, food and temples, 250000"))
print("TOKYO RESULT cities:", r1.get('constraints').cities if r1.get('constraints') else "FAILED")
if r1.get('budget_breakdown'):
    print("TOKYO budget total:", getattr(r1.get('budget_breakdown'), 'total_in_usd', "N/A"))

r2 = asyncio.run(run_travel_planner_graph("Weekend Amsterdam, fun things, 200000"))
print("AMS RESULT cities:", r2.get('constraints').cities if r2.get('constraints') else "FAILED")
if r2.get('budget_breakdown'):
    print("AMS budget total:", getattr(r2.get('budget_breakdown'), 'total_in_usd', "N/A"))
