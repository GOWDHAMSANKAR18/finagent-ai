import pytest
from backend.models.agent_messages import SharedContext
from backend.agents.budget_agent import BudgetAgent
from backend.agents.goal_agent import GoalAgent
from backend.agents.debt_risk_agent import DebtRiskAgent

def test_budget_agent_execution():
    agent = BudgetAgent()
    profile = {
        "monthly_income": 60000,
        "fixed_expenses": 22000,
        "variable_expenses": 15000
    }
    context = SharedContext(user_profile=profile)
    msg = agent.execute(context)
    
    assert msg.sender == "budget_agent"
    assert context.budget_analysis['monthly_surplus'] == 23000.0
    assert context.budget_analysis['savings_rate'] == 38.33

def test_inter_agent_communication_dependency():
    budget_agent = BudgetAgent()
    goal_agent = GoalAgent()

    profile = {
        "monthly_income": 60000,
        "fixed_expenses": 20000,
        "variable_expenses": 10000,
        "goals": [{"name": "Laptop", "target_amount": 60000, "deadline_months": 6, "priority": 1}]
    }
    context = SharedContext(user_profile=profile)
    
    b_msg = budget_agent.execute(context)
    g_msg = goal_agent.execute(context, input_message=b_msg)

    assert len(context.messages) == 2
    assert g_msg.data['available_surplus_input'] == 30000.0
    assert context.goal_analysis['evaluated_goals'][0]['feasible'] is True
