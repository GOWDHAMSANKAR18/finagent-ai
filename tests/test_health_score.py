import pytest
from backend.tools.health_score_calculator import calculate_financial_health_score

def test_financial_health_score_healthy():
    score = calculate_financial_health_score(
        income=60000,
        fixed_expenses=20000,
        variable_expenses=12000,
        savings_rate=38.3,
        emergency_months_covered=6.0,
        dti_ratio=10.0,
        goal_feasibility_pct=100.0
    )
    assert score["overall_score"] >= 80
    assert score["rating"] == "Excellent" or score["rating"] == "Healthy"
    assert len(score["score_breakdown"]) == 5

def test_financial_health_score_critical():
    score = calculate_financial_health_score(
        income=30000,
        fixed_expenses=25000,
        variable_expenses=10000,
        savings_rate=-16.6,
        emergency_months_covered=0.5,
        dti_ratio=50.0,
        goal_feasibility_pct=0.0
    )
    assert score["overall_score"] < 40
    assert score["rating"] == "Critical Action Required"
