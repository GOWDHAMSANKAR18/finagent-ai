import pytest
from backend.services.validation_service import validate_and_reconcile_plan

def test_budget_deficit_conflict_detection():
    """
    Test validation service detects budget deficit where expenses exceed income.
    """
    profile = {
        "monthly_income": 50000,
        "fixed_expenses": 34000,
        "variable_expenses": 18000
    }
    budget = {"monthly_surplus": -2000.0}
    goal = {"total_required_monthly": 5000.0, "total_allocated_monthly": 0.0}
    debt = {"emergency_fund_status": {"months_covered": 0.5}, "dti_ratio": 0.0}

    val = validate_and_reconcile_plan(profile, budget, goal, debt)

    assert val["has_conflict"] is True
    assert val["is_valid"] is False
    assert val["delegate_to"] == "budget_agent"
    assert "deficit" in val["delegation_reason"].lower()

def test_goal_exceeds_surplus_conflict_resolution():
    """
    Test validation service detects goal allocation exceeding surplus and provides reconciliation.
    """
    profile = {
        "monthly_income": 60000,
        "fixed_expenses": 20000,
        "variable_expenses": 10000
    }
    budget = {"monthly_surplus": 30000.0}
    goal = {"total_required_monthly": 40000.0, "total_allocated_monthly": 40000.0}
    debt = {"emergency_fund_status": {"months_covered": 6.0}, "dti_ratio": 0.0}

    val = validate_and_reconcile_plan(profile, budget, goal, debt)

    assert val["has_conflict"] is True
    assert val["delegate_to"] == "goal_agent"
    # Reconciled goal savings must be capped to available surplus
    assert val["reconciled_allocations"]["goal_savings"] <= 30000.0
    assert val["is_mathematically_balanced"] is True
