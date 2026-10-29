import pytest
from backend.tools.knowledge_retriever import KnowledgeRetriever
from backend.tools.subscription_optimizer import analyze_subscriptions
from backend.tools.transaction_analyzer import analyze_transaction_list
from backend.tools.report_generator import generate_text_report
from backend.tools.health_score_calculator import calculate_financial_health_score
from backend.tools.simulation_engine import run_what_if_simulation, compare_debt_payoff_strategies

def test_knowledge_retriever():
    kr = KnowledgeRetriever()
    results = kr.query("emergency fund 50/30/20 rule", top_k=3)
    assert isinstance(results, list)
    assert len(results) > 0
    assert "topic" in results[0]

def test_knowledge_retriever_empty_query():
    kr = KnowledgeRetriever()
    results = kr.query("", top_k=2)
    assert isinstance(results, list)
    assert len(results) > 0

def test_subscription_optimizer():
    txs = [
        {"description": "Netflix Subscription", "amount": 499},
        {"description": "Spotify Monthly", "amount": 119},
        {"description": "Grocery Store", "amount": 2500}
    ]
    res = analyze_subscriptions(txs)
    assert res["subscription_count"] >= 2
    assert res["total_monthly_cost"] >= 618

def test_subscription_optimizer_empty():
    res = analyze_subscriptions([])
    assert res["subscription_count"] == 0
    assert res["total_monthly_cost"] == 0.0

def test_transaction_analyzer():
    txs = [
        {"category": "Dining Out", "amount": 1500, "type": "expense"},
        {"category": "Dining Out", "amount": 2000, "type": "expense"},
        {"category": "Utilities", "amount": 3000, "type": "expense"}
    ]
    res = analyze_transaction_list(txs)
    assert res["total_expenses"] == 6500.0
    assert "Dining Out" in res["category_breakdown"]
    assert res["category_breakdown"]["Dining Out"] == 3500.0

def test_report_generator():
    dummy_plan = {
        "summary": {
            "monthly_income": 60000,
            "monthly_surplus": 25000,
            "health_score": 85,
            "health_rating": "Strong",
            "plan_status": "Valid & Balanced"
        },
        "proposed_monthly_plan": [
            {"category": "Fixed Needs", "allocated_amount": 25000, "percentage_of_income": 41.7}
        ],
        "action_plan": ["1. Maintain emergency fund"]
    }
    report = generate_text_report(dummy_plan)
    assert "FINANCIAL" in report
    assert "60,000" in report
    assert "Strong" in report

def test_health_score_calculator_edge_cases():
    score_high = calculate_financial_health_score(
        income=100000, fixed_expenses=30000, variable_expenses=20000,
        savings_rate=30.0, emergency_months_covered=6.0, dti_ratio=10.0, goal_feasibility_pct=100.0
    )
    assert score_high["overall_score"] >= 80

    score_low = calculate_financial_health_score(
        income=30000, fixed_expenses=25000, variable_expenses=10000,
        savings_rate=-16.7, emergency_months_covered=0.0, dti_ratio=55.0, goal_feasibility_pct=0.0
    )
    assert score_low["overall_score"] <= 45

def test_simulation_engine():
    profile = {
        "monthly_income": 60000,
        "fixed_expenses": 20000,
        "variable_expenses": 10000
    }
    sim = run_what_if_simulation(profile, {"extra_savings_monthly": 5000})
    assert sim["simulated_surplus"] == 35000.0

def test_debt_payoff_strategies_comparison():
    debts = [
        {"name": "Credit Card", "total_balance": 50000, "monthly_emi": 5000, "interest_rate_annual": 24.0},
        {"name": "Personal Loan", "total_balance": 100000, "monthly_emi": 4000, "interest_rate_annual": 12.0}
    ]
    comparison = compare_debt_payoff_strategies(debts, extra_monthly_allocation=3000)
    assert "avalanche" in comparison["strategies"]
    assert "snowball" in comparison["strategies"]
    assert comparison["strategies"]["avalanche"]["total_interest_paid"] <= comparison["strategies"]["snowball"]["total_interest_paid"]
