import pytest
from backend.tools.financial_calculator import calculate_monthly_surplus, calculate_savings_rate
from backend.tools.transaction_analyzer import analyze_transaction_list

def test_monthly_surplus_and_savings_rate():
    surplus = calculate_monthly_surplus(60000, 22000, 15000)
    assert surplus == 23000.0

    rate = calculate_savings_rate(surplus, 60000)
    assert rate == 38.33

def test_transaction_analyzer():
    sample_txs = [
        {"date": "2026-09-01", "description": "Salary", "category": "Income", "amount": 60000, "type": "income"},
        {"date": "2026-09-02", "description": "Rent", "category": "Housing", "amount": 15000, "type": "expense"},
        {"date": "2026-09-05", "description": "Netflix", "category": "Subscriptions", "amount": 1200, "type": "expense"}
    ]
    res = analyze_transaction_list(sample_txs)
    assert res['total_income'] == 60000.0
    assert res['total_expenses'] == 16200.0
    assert "Housing" in res['category_breakdown']
    assert len(res['recurring_subscriptions']) == 1
