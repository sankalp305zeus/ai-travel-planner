import asyncio, os, json
from dotenv import load_dotenv
load_dotenv()
from backend.graph import run_travel_planner_graph
from backend.schemas import TravelConstraints, ActivityCatalog

async def main():
    result = await run_travel_planner_graph("5 days Amsterdam, fun things to do, less crowd, 200000")
    if result.get('draft_itinerary'):
        d = result['draft_itinerary']
        print(f"\nDRAFT ITINERARY:")
        print(f"  days: {len(d.day_skeletons)}")
        for i, day in enumerate(d.day_skeletons):
            activities = day.activities if hasattr(day, 'activities') else []
            print(f"  Day {i+1}: {len(activities)} activities")

asyncio.run(main())
