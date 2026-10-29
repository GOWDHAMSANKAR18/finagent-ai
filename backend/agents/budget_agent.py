"""
Agent 1 — Financial Data & Budget Analyst
Analyzes user cash flow, categorizes expenses, calculates savings rate,
processes transaction CSV streams using Pandas, and identifies spending anomalies.
Uses explicit specialized LLM prompt and tool tracking.
"""

from typing import Optional
from backend.agents.base_agent import BaseAgent
from backend.models.agent_messages import AgentMessage, SharedContext
from backend.tools.financial_calculator import calculate_monthly_surplus, calculate_savings_rate
from backend.tools.transaction_analyzer import analyze_transaction_list

BUDGET_SYSTEM_PROMPT = """
You are the specialized Budget & Financial Analyst Agent in a Multi-Agent AI System.
Your sole responsibility is analyzing user income, expenses, cash flow surplus, savings rate,
and transaction spending patterns.
Do NOT perform debt evaluation or goal planning belonging to other specialized agents.
Provide a clear, structured financial data analysis based on verified calculation outputs.
"""

class BudgetAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="budget_agent",
            role="Financial Data & Budget Analyst",
            description="Analyzes income, expense categories, monthly surplus, savings rate, and spending patterns."
        )

    def execute(self, shared_context: SharedContext, input_message: Optional[AgentMessage] = None) -> AgentMessage:
        self.log_state(shared_context, status="running")

        user_profile = shared_context.user_profile
        income = float(user_profile.get('monthly_income', 0.0))
        fixed_expenses = float(user_profile.get('fixed_expenses', 0.0))
        variable_expenses = float(user_profile.get('variable_expenses', 0.0))
        raw_transactions = user_profile.get('transactions', [])

        # Step 1: Run deterministic tool calculations via execute_tool
        surplus = self.execute_tool(
            shared_context, "calculate_monthly_surplus", calculate_monthly_surplus,
            income, fixed_expenses, variable_expenses
        )
        savings_rate = self.execute_tool(
            shared_context, "calculate_savings_rate", calculate_savings_rate,
            surplus, income
        )

        # Step 2: Analyze transactions using Pandas if present
        tx_analysis = {}
        if raw_transactions:
            tx_analysis = self.execute_tool(
                shared_context, "analyze_transaction_list", analyze_transaction_list,
                raw_transactions
            )
            shared_context.transaction_analysis = tx_analysis

        # Step 3: Spending Observations
        housing_pct = round((fixed_expenses / income * 100), 1) if income > 0 else 0.0
        variable_pct = round((variable_expenses / income * 100), 1) if income > 0 else 0.0

        observations = []
        if housing_pct > 40:
            observations.append(f"Housing & fixed obligations represent a high share ({housing_pct}%) of monthly income.")
        else:
            observations.append(f"Fixed essential expenses are well-managed at {housing_pct}% of total income.")

        if savings_rate >= 20.0:
            observations.append(f"Healthy savings rate of {savings_rate}% (above recommended 20% benchmark).")
        elif savings_rate > 0:
            observations.append(f"Savings rate of {savings_rate}% is below the ideal 20% benchmark.")
        else:
            observations.append(f"CRITICAL: Monthly expenses exceed income by {abs(surplus)} (Negative Cash Flow).")

        if tx_analysis.get('recurring_subscriptions'):
            sub_count = len(tx_analysis['recurring_subscriptions'])
            observations.append(f"Detected {sub_count} recurring subscription drains in transactions.")

        # Step 4: LLM Reasoning Synthesis
        task_prompt = (
            f"Analyze cash flow for User:\n"
            f"- Monthly Income: {income}\n"
            f"- Fixed Expenses: {fixed_expenses} ({housing_pct}%)\n"
            f"- Variable Expenses: {variable_expenses} ({variable_pct}%)\n"
            f"- Calculated Monthly Surplus: {surplus}\n"
            f"- Savings Rate: {savings_rate}%\n"
            f"Formulate a concise 2-sentence summary of cash flow health and key risk factors."
        )
        llm_reasoning = self.llm_service.generate_completion(
            prompt=task_prompt,
            system_prompt=BUDGET_SYSTEM_PROMPT,
            agent_name=self.name
        )

        # Step 5: Construct structured payload
        budget_data = {
            "monthly_income": income,
            "fixed_expenses": fixed_expenses,
            "variable_expenses": variable_expenses,
            "total_expenses": round(fixed_expenses + variable_expenses, 2),
            "monthly_surplus": surplus,
            "savings_rate": savings_rate,
            "housing_ratio_pct": housing_pct,
            "variable_ratio_pct": variable_pct,
            "spending_observations": observations,
            "transaction_summary": tx_analysis,
            "llm_analysis": llm_reasoning
        }

        # Store result in shared context
        shared_context.budget_analysis = budget_data

        summary = (
            f"Income: {income} | Expenses: {fixed_expenses + variable_expenses} | "
            f"Surplus: {surplus} | Savings Rate: {savings_rate}%"
        )
        self.log_state(shared_context, status="completed", summary=summary)

        # Emit structured message to Goal Agent & Orchestrator
        output_msg = self.create_message(
            receiver="goal_agent",
            message_type="financial_analysis",
            data=budget_data,
            summary=summary,
            step_id=1,
            confidence=0.98
        )
        shared_context.messages.append(output_msg)
        return output_msg

