import pytest
from backend.tools.financial_calculator import calculate_debt_to_income, calculate_emergency_fund_status, calculate_loan_payoff_estimate

def test_debt_to_income():
    dti = calculate_debt_to_income(15000, 50000)
    assert dti == 30.0

def test_emergency_fund_status():
    status = calculate_emergency_fund_status(50000, 20000, target_months=6)
    assert status['months_covered'] == 2.5
    assert status['is_adequate'] is False
    assert status['shortfall'] == 70000.0

def test_loan_payoff_estimate():
    est = calculate_loan_payoff_estimate(100000, 10000, 12.0)
    assert est['months_to_payoff'] > 0
    assert est['status'] == "Calculated"
