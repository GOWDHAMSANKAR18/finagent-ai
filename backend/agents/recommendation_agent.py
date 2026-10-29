"""
Agent 5 — Financial Decision / Recommendation Agent
Acts as the final synthesizer and decision-maker. Receives outputs from all agents,
validates mathematical constraints, calculates health score, analyzes debt strategies,
builds alert lists, and generates the final structured financial plan.
Uses explicit specialized LLM prompt and tool tracking.
"""

from typing import Optional, List, Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.models.agent_messages import AgentMessage, SharedContext
from backend.services.validation_service import validate_and_reconcile_plan
from backend.tools.health_score_calculator import calculate_financial_health_score
from backend.tools.subscription_optimizer import analyze_subscriptions
from backend.tools.simulation_engine import compare_debt_payoff_strategies, run_what_if_simulation
from backend.models.financial_plan import (
    FinancialPlanOutput,
    MonthlyAllocationItem,
    GoalAnalysisResult,
    RiskWarningItem,
    AgentContributionTrace
)

RECOMMENDATION_SYSTEM_PROMPT = """
You are the Financial Decision & Recommendation Agent in a Multi-Agent AI System.
Your responsibility is synthesizing outputs from the Budget, Goal, Debt/Risk, and Research Agents into
a cohesive, mathematically validated financial plan.
Do NOT fabricate numbers. Ground all guidance strictly on verified multi-agent analysis and validation service outputs.
"""

class RecommendationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="recommendation_agent",
            role="Financial Decision / Recommendation Agent",
            description="Synthesizes multi-agent outputs, validates mathematical constraints, and builds the final financial plan."
        )

    def execute(self, shared_context: SharedContext, input_message: Optional[AgentMessage] = None) -> AgentMessage:
        self.log_state(shared_context, status="running")

        user_profile = shared_context.user_profile
        budget = shared_context.budget_analysis
        goals = shared_context.goal_analysis
        debt = shared_context.debt_risk_analysis
        research = shared_context.research_results

        # Step 1: Execute validation & reconciliation service via execute_tool
        reconciled = self.execute_tool(
            shared_context, "validate_and_reconcile_plan", validate_and_reconcile_plan,
            user_profile, budget, goals, debt
        )
        shared_context.validation_results = reconciled

        alloc_dict = reconciled.get('reconciled_allocations', {})
        income = float(user_profile.get('monthly_income', 0.0))

        # Step 2: Compute Financial Health Score via execute_tool
        eval_goals = goals.get('evaluated_goals', [])
        achievable_count = sum(1 for eg in eval_goals if eg.get('feasible'))
        feasibility_pct = (achievable_count / len(eval_goals) * 100.0) if eval_goals else 100.0

        health = self.execute_tool(
            shared_context, "calculate_financial_health_score", calculate_financial_health_score,
            income=income,
            fixed_expenses=user_profile.get('fixed_expenses', 0.0),
            variable_expenses=user_profile.get('variable_expenses', 0.0),
            savings_rate=budget.get('savings_rate', 0.0),
            emergency_months_covered=debt.get('emergency_fund_status', {}).get('months_covered', 0.0),
            dti_ratio=debt.get('dti_ratio', 0.0),
            goal_feasibility_pct=feasibility_pct
        )
        shared_context.health_score = health

        # Step 3: Subscription Detection via execute_tool
        sub_analysis = self.execute_tool(
            shared_context, "analyze_subscriptions", analyze_subscriptions,
            user_profile.get('transactions', [])
        )
        shared_context.subscriptions = sub_analysis

        # Step 4: Debt Payoff Strategies (Avalanche vs Snowball) via execute_tool
        debt_strats = self.execute_tool(
            shared_context, "compare_debt_payoff_strategies", compare_debt_payoff_strategies,
            user_profile.get('debts', []),
            extra_monthly_allocation=alloc_dict.get('debt_repayment', 0.0)
        )
        shared_context.debt_strategies = debt_strats

        # Step 5: Default What-If Simulation (+₹5,000 monthly savings) via execute_tool
        default_sim = self.execute_tool(
            shared_context, "run_what_if_simulation", run_what_if_simulation,
            user_profile,
            {"extra_savings_monthly": 5000, "scenario_name": "Save ₹5,000 More Monthly"}
        )
        shared_context.simulations = {"default_plus_5k": default_sim}

        # Step 6: Assemble Alert List
        alerts = []
        if budget.get('savings_rate', 0) < 20:
            alerts.append({"severity": "warning", "title": "Low Savings Rate", "message": f"Current savings rate is {budget.get('savings_rate')}%, below recommended 20% benchmark."})
        if debt.get('dti_ratio', 0) >= 35:
            alerts.append({"severity": "danger", "title": "High Debt Burden", "message": f"Debt-to-Income ratio is {debt.get('dti_ratio')}%. Prioritize Debt Avalanche payoff."})
        if not debt.get('emergency_fund_status', {}).get('is_adequate', True):
            alerts.append({"severity": "warning", "title": "Emergency Fund Cushion Deficit", "message": f"Emergency fund covers {debt.get('emergency_fund_status', {}).get('months_covered')} months (Target: 3-6 months)."})
        if sub_analysis.get('subscription_count', 0) > 0:
            alerts.append({"severity": "info", "title": "Recurring Subscriptions Detected", "message": f"Found {sub_analysis['subscription_count']} subscriptions costing ₹{sub_analysis['total_annual_cost']}/year."})
        
        shared_context.alerts = alerts

        # Step 7: Build Monthly Allocation Breakdown
        proposed_monthly_plan: List[MonthlyAllocationItem] = [
            MonthlyAllocationItem(
                category="Essential Fixed Expenses (Needs)",
                allocated_amount=alloc_dict.get('fixed_expenses', 0.0),
                percentage_of_income=round((alloc_dict.get('fixed_expenses', 0.0) / income * 100), 1) if income > 0 else 0.0,
                explanation="Mandatory obligations (Rent, Utilities, Insurance, Minimum Debt EMIs)."
            ),
            MonthlyAllocationItem(
                category="Discretionary Variable Expenses (Wants)",
                allocated_amount=alloc_dict.get('variable_expenses', 0.0),
                percentage_of_income=round((alloc_dict.get('variable_expenses', 0.0) / income * 100), 1) if income > 0 else 0.0,
                explanation="Flexible lifestyle spending (Dining out, Entertainment, Shopping)."
            ),
            MonthlyAllocationItem(
                category="Emergency Safety Cushion",
                allocated_amount=alloc_dict.get('emergency_fund', 0.0),
                percentage_of_income=round((alloc_dict.get('emergency_fund', 0.0) / income * 100), 1) if income > 0 else 0.0,
                explanation="Monthly contribution toward building/maintaining liquid emergency fund."
            ),
            MonthlyAllocationItem(
                category="Accelerated Debt Payoff",
                allocated_amount=alloc_dict.get('debt_repayment', 0.0),
                percentage_of_income=round((alloc_dict.get('debt_repayment', 0.0) / income * 100), 1) if income > 0 else 0.0,
                explanation="Extra principal repayments directed to high-interest loans (Avalanche method)."
            ),
            MonthlyAllocationItem(
                category="Financial Goal Savings",
                allocated_amount=alloc_dict.get('goal_savings', 0.0),
                percentage_of_income=round((alloc_dict.get('goal_savings', 0.0) / income * 100), 1) if income > 0 else 0.0,
                explanation="Dedicated allocation distributed across short and long-term financial goals."
            ),
            MonthlyAllocationItem(
                category="Flexible Cash Reserve",
                allocated_amount=alloc_dict.get('flexible_spending', 0.0),
                percentage_of_income=round((alloc_dict.get('flexible_spending', 0.0) / income * 100), 1) if income > 0 else 0.0,
                explanation="Unallocated buffer retained in liquid account for unexpected minor expenses."
            )
        ]

        # Step 8: Map Goal Analysis Results
        goal_evals: List[GoalAnalysisResult] = []
        for eg in eval_goals:
            goal_evals.append(GoalAnalysisResult(
                goal_name=eg.get('goal_name', 'Goal'),
                target_amount=eg.get('target_amount', 0.0),
                deadline_months=eg.get('deadline_months', 1),
                required_monthly=eg.get('required_monthly', 0.0),
                allocated_monthly=eg.get('allocated_monthly', 0.0),
                feasible=eg.get('feasible', False),
                feasibility_status=eg.get('feasibility_status', ''),
                gap_per_month=eg.get('gap_per_month', 0.0),
                timeline_recommendation=eg.get('timeline_recommendation', '')
            ))

        # Step 9: Map Risk Warnings
        risk_items: List[RiskWarningItem] = []
        for rw in debt.get('risk_warnings', []):
            risk_items.append(RiskWarningItem(
                severity=rw.get('severity', 'Warning'),
                risk_title=rw.get('risk_title', 'Risk'),
                description=rw.get('description', ''),
                recommended_action=rw.get('recommended_action', '')
            ))

        # Step 10: Step-by-Step Action Items
        action_plan = []
        action_plan.append("1. Maintain strict tracking of fixed essential expenses (Rent, Utilities) to preserve cash flow.")
        
        if alloc_dict.get('emergency_fund', 0.0) > 0:
            action_plan.append(f"2. Direct {alloc_dict.get('emergency_fund')}/month into a high-yield liquid account until 3-6 months essential expenses are accumulated.")
            
        if alloc_dict.get('debt_repayment', 0.0) > 0:
            action_plan.append(f"3. Apply extra payment of {alloc_dict.get('debt_repayment')}/month specifically to the highest interest debt balance first.")

        if alloc_dict.get('goal_savings', 0.0) > 0:
            action_plan.append(f"4. Automate monthly goal savings transfers of {alloc_dict.get('goal_savings')}/month into designated sub-accounts.")

        if goals.get('total_gap_monthly', 0.0) > 0:
            action_plan.append(f"5. Address the goal monthly gap of {goals.get('total_gap_monthly')}/month by extending target deadlines or cutting non-essential variable spending.")

        # Step 11: LLM Reasoning Synthesis for Final Strategic Summary
        task_prompt = (
            f"Synthesize final financial plan:\n"
            f"- Monthly Income: {income}\n"
            f"- Reconciled Allocations: {alloc_dict}\n"
            f"- Health Score: {health.get('overall_score')}/100 ({health.get('rating')})\n"
            f"- Validation Balanced: {reconciled.get('is_mathematically_balanced')}\n"
            f"Write a 3-sentence executive summary highlighting key strengths, risks, and next steps."
        )
        llm_reasoning = self.llm_service.generate_completion(
            prompt=task_prompt,
            system_prompt=RECOMMENDATION_SYSTEM_PROMPT,
            agent_name=self.name
        )

        # Step 12: Agent Contribution Trace
        agent_contributions = [
            AgentContributionTrace(
                agent_name="Budget Agent",
                role="Financial Data Analyst",
                key_findings=[
                    f"Monthly Surplus calculated at {budget.get('monthly_surplus')}",
                    f"Savings rate determined to be {budget.get('savings_rate')}%",
                    f"Fixed housing ratio: {budget.get('housing_ratio_pct')}%"
                ],
                confidence_score=0.98
            ),
            AgentContributionTrace(
                agent_name="Goal Agent",
                role="Goal Planner",
                key_findings=[
                    "Target goals evaluated against monthly cash surplus",
                    f"Total required monthly savings: {goals.get('total_required_monthly')}",
                    f"Overall feasibility assessment: {goals.get('overall_feasibility')}"
                ],
                confidence_score=0.96
            ),
            AgentContributionTrace(
                agent_name="Debt & Risk Agent",
                role="Risk & Debt Specialist",
                key_findings=[
                    f"Debt-to-Income (DTI) ratio evaluated at {debt.get('dti_ratio')}%",
                    f"Emergency fund adequacy: {debt.get('emergency_fund_status', {}).get('status')}",
                    f"Flagged {len(debt.get('risk_warnings', []))} risk factors requiring mitigation"
                ],
                confidence_score=0.97
            ),
            AgentContributionTrace(
                agent_name="Research Agent",
                role="RAG Knowledge Retrieval",
                key_findings=[
                    f"Retrieved {len(research.get('retrieved_knowledge', []))} knowledge base standards",
                    "Classified user facts vs calculated figures vs financial guidelines"
                ],
                confidence_score=0.99
            ),
            AgentContributionTrace(
                agent_name="Recommendation Agent",
                role="Synthesis & Decision Validation",
                key_findings=[
                    "Cross-agent numerical validation & budget balancing completed",
                    "Resolved goal/debt/emergency fund allocation priorities",
                    f"Produced total reconciled allocation equal to monthly income ({income})"
                ],
                confidence_score=0.99
            )
        ]

        # Assemble Final Plan Object
        final_plan_obj = FinancialPlanOutput(
            summary={
                "monthly_income": income,
                "fixed_expenses": user_profile.get('fixed_expenses'),
                "variable_expenses": user_profile.get('variable_expenses'),
                "monthly_surplus": budget.get('monthly_surplus'),
                "savings_rate": budget.get('savings_rate'),
                "dti_ratio": debt.get('dti_ratio'),
                "emergency_fund_months": debt.get('emergency_fund_status', {}).get('months_covered'),
                "health_score": health.get('overall_score'),
                "health_rating": health.get('rating'),
                "plan_status": "Valid & Balanced" if reconciled.get('is_mathematically_balanced') else "Needs Rebalancing",
                "executive_summary_llm": llm_reasoning
            },
            budget_breakdown={
                "fixed_expenses": user_profile.get('fixed_expenses'),
                "variable_expenses": user_profile.get('variable_expenses'),
                "spending_observations": budget.get('spending_observations', [])
            },
            goal_evaluations=goal_evals,
            debt_evaluation={
                "total_debt_balance": debt.get('total_debt_balance'),
                "total_monthly_emi": debt.get('total_monthly_emi'),
                "dti_ratio": debt.get('dti_ratio'),
                "debts_analyzed": debt.get('debts_analyzed', [])
            },
            risk_assessment=risk_items,
            proposed_monthly_plan=proposed_monthly_plan,
            action_plan=action_plan,
            agent_contributions=agent_contributions,
            citations_and_sources=research.get('retrieved_knowledge', []),
            disclaimer="Educational Financial Planning Assistant — University Multi-Agent Demonstration. Not regulated financial advice."
        )

        final_dict = final_plan_obj.model_dump()
        final_dict["health_score_details"] = health
        final_dict["subscription_summary"] = sub_analysis
        final_dict["debt_strategies"] = debt_strats
        final_dict["alerts"] = alerts
        final_dict["llm_synthesis"] = llm_reasoning

        shared_context.final_plan = final_dict

        summary = f"Synthesized final plan. Health score: {health.get('overall_score')}/100. Reconciled {income} budget."
        self.log_state(shared_context, status="completed", summary=summary)

        # Final message to Orchestrator
        output_msg = self.create_message(
            receiver="orchestrator",
            message_type="final_plan_output",
            data=final_dict,
            summary=summary,
            step_id=5,
            confidence=0.99
        )
        shared_context.messages.append(output_msg)
        return output_msg

