import pytest
from backend.agents.orchestrator import MultiAgentOrchestrator
from backend.tools.transaction_analyzer import analyze_transaction_list

def test_pipeline_recovers_from_partial_failure():
    orchestrator = MultiAgentOrchestrator()
    # Missing optional goal fields
    profile = {
        "monthly_income": 60000,
        "fixed_expenses": 20000,
        "variable_expenses": 10000,
        "goals": [{"name": "Partial Goal", "target_amount": 50000}], # Missing deadline
        "debts": []
    }

    context = orchestrator.run_pipeline(profile)
    assert context.final_plan is not None
    assert context.final_plan["summary"]["plan_status"] == "Valid & Balanced"

def test_invalid_csv_handling():
    malformed_txs = [
        {"description": "Unknown", "amount": "invalid_number"}
    ]
    res = analyze_transaction_list(malformed_txs)
    assert res["total_expenses"] == 0.0
