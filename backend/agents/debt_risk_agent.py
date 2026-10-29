"""
Agent 3 — Debt & Risk Analysis Agent
Analyzes outstanding loans, calculates Debt-to-Income (DTI) ratio, identifies high-interest debt,
evaluates emergency fund adequacy, and detects dangerous risk situations.
Uses explicit specialized LLM prompt and tool tracking.
"""

from typing import Optional
from backend.agents.base_agent import BaseAgent
from backend.models.agent_messages import AgentMessage, SharedContext
from backend.tools.financial_calculator import (
    calculate_debt_to_income,
    calculate_emergency_fund_status,
    calculate_loan_payoff_estimate
)

DEBT_RISK_SYSTEM_PROMPT = """
You are the specialized Debt & Risk Analysis Agent in a Multi-Agent AI System.
Your sole responsibility is assessing user debt obligations, DTI ratios, emergency safety net adequacy,
and identifying debt traps or insolvency exposure.
Do NOT perform budget category allocation or knowledge citation belonging to other agents.
Deliver a rigorous risk rating and recommended debt payoff acceleration strategy.
"""

class DebtRiskAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="debt_risk_agent",
            role="Debt & Risk Analysis Agent",
            description="Evaluates debt obligations, DTI ratios, emergency safety nets, and identifies financial risks."
        )

    def execute(self, shared_context: SharedContext, input_message: Optional[AgentMessage] = None) -> AgentMessage:
        self.log_state(shared_context, status="running")

        user_profile = shared_context.user_profile
        income = float(user_profile.get('monthly_income', 0.0))
        fixed_expenses = float(user_profile.get('fixed_expenses', 0.0))
        existing_emergency_fund = float(user_profile.get('emergency_fund', 0.0))
        raw_debts = user_profile.get('debts', [])

        # Step 1: Analyze Debts & EMIs via execute_tool
        total_debt_balance = 0.0
        total_monthly_emi = 0.0
        debt_items_analyzed = []
        has_high_interest = False

        for d in raw_debts:
            bal = float(d.get('total_balance', 0.0))
            emi = float(d.get('monthly_emi', 0.0))
            rate = float(d.get('interest_rate_annual', 0.0))
            name = d.get('name', 'Loan')

            total_debt_balance += bal
            total_monthly_emi += emi

            if rate >= 12.0:
                has_high_interest = True

            payoff_est = self.execute_tool(
                shared_context, "calculate_loan_payoff_estimate", calculate_loan_payoff_estimate,
                bal, emi, rate
            )
            debt_items_analyzed.append({
                "name": name,
                "total_balance": bal,
                "monthly_emi": emi,
                "interest_rate_annual": rate,
                "is_high_interest": rate >= 12.0,
                "payoff_estimate": payoff_est
            })

        # Step 2: DTI Ratio & Emergency Fund Adequacy via execute_tool
        dti_ratio = self.execute_tool(
            shared_context, "calculate_debt_to_income", calculate_debt_to_income,
            total_monthly_emi, income
        )
        emergency_status = self.execute_tool(
            shared_context, "calculate_emergency_fund_status", calculate_emergency_fund_status,
            existing_emergency_fund, fixed_expenses
        )

        # Step 3: Risk Identification Engine
        risk_warnings = []
        
        # Risk 1: DTI Check
        if dti_ratio >= 40.0:
            risk_warnings.append({
                "severity": "Critical",
                "risk_title": "Severe Debt Burden (DTI >= 40%)",
                "description": f"Debt payments absorb {dti_ratio}% of gross monthly income, putting you at high risk of insolvency.",
                "recommended_action": "Prioritize aggressive debt repayment using Debt Avalanche method; avoid new credit."
            })
        elif dti_ratio >= 25.0:
            risk_warnings.append({
                "severity": "Warning",
                "risk_title": "Moderate Debt Load (DTI >= 25%)",
                "description": f"DTI ratio is {dti_ratio}%. Manageable, but restricts monthly cash flexibility.",
                "recommended_action": "Accelerate principal repayments where possible to reduce monthly EMI burden."
            })

        # Risk 2: Emergency Fund Check
        if not emergency_status['is_adequate']:
            risk_warnings.append({
                "severity": "Warning" if emergency_status['months_covered'] >= 1.5 else "Critical",
                "risk_title": "Inadequate Emergency Fund",
                "description": f"Current emergency savings cover only {emergency_status['months_covered']} months of essential expenses (minimum 3-6 months required).",
                "recommended_action": f"Build emergency fund cushion of at least {emergency_status['shortfall']} before taking speculative investments."
            })

        # Risk 3: High Interest Debt Alert
        if has_high_interest:
            risk_warnings.append({
                "severity": "Warning",
                "risk_title": "High-Interest Debt Trap",
                "description": "Portion of debt carries an annual interest rate >= 12%. Interest costs compound quickly.",
                "recommended_action": "Allocate extra monthly cash surplus directly to high-interest balance first."
            })

        # Step 4: LLM Risk Assessment Reasoning
        task_prompt = (
            f"Analyze debt and risk profile for user:\n"
            f"- Total Debt Balance: {total_debt_balance} (EMI: {total_monthly_emi})\n"
            f"- Debt-to-Income (DTI) Ratio: {dti_ratio}%\n"
            f"- Emergency Fund Months Covered: {emergency_status.get('months_covered')}\n"
            f"- High Interest Debt Present: {has_high_interest}\n"
            f"Formulate a 2-sentence risk synthesis outlining urgency and recommended payoff strategy."
        )
        llm_reasoning = self.llm_service.generate_completion(
            prompt=task_prompt,
            system_prompt=DEBT_RISK_SYSTEM_PROMPT,
            agent_name=self.name
        )

        debt_risk_data = {
            "total_debt_balance": round(total_debt_balance, 2),
            "total_monthly_emi": round(total_monthly_emi, 2),
            "dti_ratio": dti_ratio,
            "has_high_interest_debt": has_high_interest,
            "debts_analyzed": debt_items_analyzed,
            "emergency_fund_status": emergency_status,
            "risk_warnings": risk_warnings,
            "llm_analysis": llm_reasoning
        }

        # Store in shared context
        shared_context.debt_risk_analysis = debt_risk_data

        summary = (
            f"Total Debt: {total_debt_balance} | DTI: {dti_ratio}% | "
            f"Emergency Fund: {emergency_status['months_covered']} months covered | Risks Flagged: {len(risk_warnings)}"
        )
        self.log_state(shared_context, status="completed", summary=summary)

        # Send message to Research Agent
        output_msg = self.create_message(
            receiver="research_agent",
            message_type="risk_and_debt_assessment",
            data=debt_risk_data,
            summary=summary,
            step_id=3,
            confidence=0.97
        )
        shared_context.messages.append(output_msg)
        return output_msg

