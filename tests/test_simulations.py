import pytest
from backend.tools.simulation_engine import run_what_if_simulation, compare_debt_payoff_strategies

def test_what_if_simulation():
    profile = {
        "monthly_income": 50000,
        "fixed_expenses": 20000,
        "variable_expenses": 15000,
        "goals": [{"name": "Laptop", "target_amount": 60000, "deadline_months": 6, "current_allocated": 0}]
    }

    sim = run_what_if_simulation(profile, {"extra_savings_monthly": 5000})
    assert sim["simulated_surplus"] == 20000.0
    assert sim["surplus_delta"] == 5000.0

def test_debt_strategy_comparison():
    debts = [
        {"name": "Credit Card", "total_balance": 100000, "monthly_emi": 10000, "interest_rate_annual": 24.0},
        {"name": "Personal Loan", "total_balance": 200000, "monthly_emi": 8000, "interest_rate_annual": 12.0}
    ]

    res = compare_debt_payoff_strategies(debts, extra_monthly_allocation=5000)
    assert "avalanche" in res["strategies"]
    assert "snowball" in res["strategies"]
    assert res["strategies"]["avalanche"]["total_interest_paid"] <= res["strategies"]["snowball"]["total_interest_paid"]
