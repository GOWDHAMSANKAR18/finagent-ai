import pytest
from backend.agents.orchestrator import MultiAgentOrchestrator
from backend.models.agent_messages import SharedContext

def test_delegation_feedback_loop_trigger():
    """
    Test case where goal allocation exceeds monthly surplus.
    Validation flags conflict, specifies delegate_to = 'goal_agent',
    and orchestrator executes delegation & re-execution feedback loop.
    """
    orchestrator = MultiAgentOrchestrator()
    profile = {
        "monthly_income": 50000,
        "fixed_expenses": 22000,
        "variable_expenses": 10000,
        "existing_savings": 20000,
        "emergency_fund": 15000,
        "goals": [{"name": "Aggressive Investment", "target_amount": 25000, "deadline_months": 1, "priority": 1}],
        "debts": [{"name": "Store Card", "total_balance": 30000, "monthly_emi": 2000, "interest_rate_annual": 18.0}]
    }

    context = orchestrator.run_pipeline(profile, enable_feedback=True)

    # Verify delegation history was populated
    assert len(context.delegation_history) > 0
    delegation = context.delegation_history[0]
    assert delegation["trigger"] == "Validation Conflict Detected"
    assert delegation["target_agent"] == "goal_agent"
    assert delegation["status"] == "resolved"

    # Verify final plan is reconciled and mathematically balanced
    assert context.final_plan is not None
    assert context.validation_results["is_mathematically_balanced"] is True
