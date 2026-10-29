import pytest
from backend.tools.goal_calculator import evaluate_financial_goals

def test_feasible_goal():
    goals = [{"name": "Laptop", "target_amount": 60000, "deadline_months": 6, "priority": 1}]
    surplus = 15000.0
    res = evaluate_financial_goals(goals, surplus)
    assert res['total_required_monthly'] == 10000.0
    assert res['overall_feasibility'] == "Fully Achievable"
    assert res['evaluated_goals'][0]['feasible'] is True

def test_unfeasible_impossible_goal():
    goals = [{"name": "House Down Payment", "target_amount": 500000, "deadline_months": 5, "priority": 1}]
    surplus = 10000.0
    res = evaluate_financial_goals(goals, surplus)
    assert res['total_required_monthly'] == 100000.0
    assert res['total_gap_monthly'] == 90000.0
    assert res['evaluated_goals'][0]['feasible'] is False
