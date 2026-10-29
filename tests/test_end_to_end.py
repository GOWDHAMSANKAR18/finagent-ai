import pytest
from backend.agents.orchestrator import MultiAgentOrchestrator

def test_full_multi_agent_pipeline_e2e():
    orchestrator = MultiAgentOrchestrator()
    profile = {
        "monthly_income": 60000,
        "fixed_expenses": 22000,
        "variable_expenses": 15000,
        "existing_savings": 50000,
        "emergency_fund": 30000,
        "goals": [{"name": "Laptop", "target_amount": 80000, "deadline_months": 8, "priority": 1}],
        "debts": [{"name": "Personal Loan", "total_balance": 240000, "monthly_emi": 7000, "interest_rate_annual": 12.5}]
    }

    context = orchestrator.run_pipeline(profile)

    assert len(context.messages) >= 5
    assert "budget_agent" in context.agent_states
    assert "goal_agent" in context.agent_states
    assert "debt_risk_agent" in context.agent_states
    assert "research_agent" in context.agent_states
    assert "recommendation_agent" in context.agent_states

    final_plan = context.final_plan
    assert final_plan['summary']['plan_status'] == "Valid & Balanced"
    assert len(final_plan['proposed_monthly_plan']) == 6
    assert len(final_plan['agent_contributions']) == 5
