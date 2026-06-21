import re

with open("tests/evals/test_sprint_5.py", "r") as f:
    content = f.read()

# Replace test_repair_loop_capped_at_3
old_test_1 = """@pytest.mark.asyncio
async def test_repair_loop_capped_at_3():
    # Mock review report to always fail
    mock_report = ReviewReport(
        passed=False, days_match=False, cities_included=True, within_budget=True,
        preference_alignment_score=0.9, crowd_avoidance_effort=True, logistics_realistic=True,
        blocking_issues=["Day count mismatch"], advisory_issues=[], repair_hints=["Fix day count"]
    )
    with patch("backend.agents.review.review_destination_itinerary", return_value=mock_report):
        state = await run_travel_planner_graph("5 days Japan, Tokyo + Kyoto, $3000")
        assert state.get("error_code") == "REPAIR_EXHAUSTED"
        assert state.get("success") is False
        assert state.get("repair_count") >= 3"""

new_test_1 = """@pytest.mark.asyncio
async def test_repair_loop_capped_at_3():
    # Mock review report to always fail
    mock_report = ReviewReport(
        passed=False, days_match=False, cities_included=True, within_budget=True,
        preference_alignment_score=0.9, crowd_avoidance_effort=True, logistics_realistic=True,
        blocking_issues=["Day count mismatch"], advisory_issues=[], repair_hints=["Fix day count"]
    )
    draft, constraints = get_base_draft_and_constraints()
    with patch("backend.graph.extract_constraints", return_value=constraints), \\
         patch("backend.graph.research_destination", return_value=draft.activity_catalog), \\
         patch("backend.graph.plan_logistics", return_value=(draft.lodging_plan, draft.movement_plan, draft.day_skeletons)), \\
         patch("backend.graph.calculate_budget", return_value=draft.budget_breakdown), \\
         patch("backend.graph.get_fx_rate", return_value=1.0), \\
         patch("backend.graph.review_destination_itinerary", return_value=mock_report):
        
        state = await run_travel_planner_graph("5 days Japan, Tokyo + Kyoto, $3000")
        assert state.get("error_code") == "REPAIR_EXHAUSTED"
        assert state.get("success") is False
        assert state.get("repair_count") >= 3"""

content = content.replace(old_test_1, new_test_1)

# Replace test_repair_routes_to_correct_agent
old_test_2 = """@pytest.mark.asyncio
async def test_repair_routes_to_correct_agent():
    # Test budget failure: re-runs only budget agent
    # We patch review agent: first call has a budget failure. Second call passes.
    mock_fail_report = ReviewReport(
        passed=False, days_match=True, cities_included=True, within_budget=False,
        preference_alignment_score=0.9, crowd_avoidance_effort=True, logistics_realistic=True,
        blocking_issues=["Over budget"], advisory_issues=[], repair_hints=["Downgrade lodging"]
    )
    mock_pass_report = ReviewReport(
        passed=True, days_match=True, cities_included=True, within_budget=True,
        preference_alignment_score=0.9, crowd_avoidance_effort=True, logistics_realistic=True,
        blocking_issues=[], advisory_issues=[], repair_hints=[]
    )
    
    # Return fail first, then pass
    review_side_effect = [mock_fail_report, mock_pass_report]
    
    # We want to verify that node_budget_agent is called, but node_logistics_agent and node_destination_agent are NOT called during repair
    with patch("backend.graph.review_destination_itinerary", side_effect=review_side_effect):
        with patch("backend.graph.node_budget_agent", return_value={"budget_breakdown": None}) as mock_budget:
            with patch("backend.graph.node_logistics_agent") as mock_logistics:
                with patch("backend.graph.node_destination_agent") as mock_destination:
                    state = await run_travel_planner_graph("5 days Japan, Tokyo + Kyoto, $3000")
                    # Initial run runs all of them (1 call each)
                    # The repair run should call only the budget agent (so mock_budget.call_count should be 2, others 1)
                    assert mock_budget.call_count == 2
                    assert mock_logistics.call_count == 1
                    assert mock_destination.call_count == 1"""

new_test_2 = """@pytest.mark.asyncio
async def test_repair_routes_to_correct_agent():
    mock_fail_report = ReviewReport(
        passed=False, days_match=True, cities_included=True, within_budget=False,
        preference_alignment_score=0.9, crowd_avoidance_effort=True, logistics_realistic=True,
        blocking_issues=["Over budget"], advisory_issues=[], repair_hints=["Downgrade lodging"]
    )
    mock_pass_report = ReviewReport(
        passed=True, days_match=True, cities_included=True, within_budget=True,
        preference_alignment_score=0.9, crowd_avoidance_effort=True, logistics_realistic=True,
        blocking_issues=[], advisory_issues=[], repair_hints=[]
    )
    
    draft, constraints = get_base_draft_and_constraints()
    
    with patch("backend.graph.extract_constraints", return_value=constraints), \\
         patch("backend.graph.research_destination", return_value=draft.activity_catalog) as mock_dest, \\
         patch("backend.graph.plan_logistics", return_value=(draft.lodging_plan, draft.movement_plan, draft.day_skeletons)) as mock_log, \\
         patch("backend.graph.calculate_budget", return_value=draft.budget_breakdown) as mock_budg, \\
         patch("backend.graph.get_fx_rate", return_value=1.0), \\
         patch("backend.graph.review_destination_itinerary", side_effect=[mock_fail_report, mock_pass_report]):
        
        state = await run_travel_planner_graph("5 days Japan, Tokyo + Kyoto, $3000")
        assert mock_budg.call_count == 2
        assert mock_log.call_count == 1
        assert mock_dest.call_count == 1"""

content = content.replace(old_test_2, new_test_2)

with open("tests/evals/test_sprint_5.py", "w") as f:
    f.write(content)
