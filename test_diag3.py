import asyncio, os, json
from dotenv import load_dotenv
load_dotenv()
from backend.graph import run_travel_planner_graph

async def main():
    result = await run_travel_planner_graph("5 days Amsterdam, fun things to do, less crowd, 200000")

    print("=" * 60)
    print("FINAL STATE DIAGNOSTIC")
    print("=" * 60)
    print(f"success: {result.get('success')}")
    print(f"error_code: {result.get('error_code')}")
    print(f"repair_count: {result.get('repair_count')}")
    print()

    if result.get('constraints'):
        c = result['constraints']
        print(f"CONSTRAINTS:")
        print(f"  cities: {c.cities}")
        print(f"  duration_days: {c.duration_days}")
        print(f"  requested_currency: {c.requested_currency}")
        print(f"  budget_in_inr: {c.budget_in_inr}")
        print(f"  budget_in_usd: {c.budget_in_usd}")

    if result.get('activity_catalog'):
        a = result['activity_catalog']
        print(f"\nACTIVITY CATALOG:")
        print(f"  total items: {len(a.activities)}")
        for item in a.activities[:10]:
            print(f"  - {item.city}: {item.name}")

    if result.get('review_report'):
        r = result['review_report']
        print(f"\nREVIEW:")
        print(f"  passed: {r.passed}")
        print(f"  blocking_issues: {r.blocking_issues}")
        print(f"  advisory_issues: {r.advisory_issues}")

    if result.get('draft_itinerary'):
        d = result['draft_itinerary']
        print(f"\nDRAFT ITINERARY:")
        print(f"  days: {len(d.day_skeletons)}")
        for i, day in enumerate(d.day_skeletons):
            activities = day.activities if hasattr(day, 'activities') else []
            print(f"  Day {i+1}: {len(activities)} activities")

asyncio.run(main())
