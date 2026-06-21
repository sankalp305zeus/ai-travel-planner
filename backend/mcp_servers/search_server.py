import os
import json
import time
import httpx
from pathlib import Path
from typing import Dict, Any
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def get_mock_activity_catalog(city: str) -> Dict[str, Any]:
    with tracer.start_as_current_span("search_server.get_mock_activity_catalog") as span:
        start_time = time.time()
        span.set_attribute("mcp.server", "search_server")
        span.set_attribute("mcp.tool", "get_mock_activity_catalog")
        
        tier_used = "json"
        cache_hit = False

        wiki_summary = ""
        try:
            r = httpx.get(f"https://en.wikivoyage.org/api/rest_v1/page/summary/{city}", timeout=5.0)
            if r.status_code == 200:
                wiki_summary = r.json().get("extract", "")
                tier_used = "wikivoyage"
        except Exception:
            pass

        cleaned_city = city.lower().strip().replace(" ", "_")
        json_path = Path(__file__).resolve().parent.parent / "data" / "destinations" / f"{cleaned_city}.json"
        
        if json_path.exists():
            try:
                with open(json_path, "r") as f:
                    activities = json.load(f)
                for act in activities:
                    act["city"] = city
                
                span.set_attribute("mcp.tier_used", tier_used)
                span.set_attribute("mcp.cache_hit", cache_hit)
                span.set_attribute("mcp.latency_ms", (time.time() - start_time) * 1000)
                return {
                    "activities": activities,
                    "crowd_level_summary": "medium",
                    "cost_band_summary": "medium",
                    "rationale": wiki_summary if wiki_summary else f"Loaded realistic mock data for {city}."
                }
            except Exception:
                pass
                
        span.set_attribute("mcp.tier_used", tier_used)
        span.set_attribute("mcp.cache_hit", cache_hit)
        span.set_attribute("mcp.latency_ms", (time.time() - start_time) * 1000)
        return {
            "activities": [
                {
                    "id": f"{cleaned_city}_attraction_1",
                    "city": city,
                    "name": f"Famous Landmark in {city}",
                    "type": "landmark",
                    "estimated_duration_hours": 2.0,
                    "crowd_level": "high",
                    "cost_band": "free",
                    "must_do": True,
                    "rationale": wiki_summary if wiki_summary else f"The main historical landmark of {city}."
                }
            ],
            "crowd_level_summary": "medium",
            "cost_band_summary": "low",
            "rationale": wiki_summary if wiki_summary else f"Mock attractions for {city}."
        }
