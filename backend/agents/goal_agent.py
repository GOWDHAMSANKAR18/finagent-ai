"""
Agent 2 — Goal & Financial Planning Agent
Evaluates short-term and long-term financial goals, calculates required monthly savings,
checks allocation feasibility against available monthly cash surplus, and plans allocations.
Uses explicit specialized LLM prompt and tool tracking.
"""

from typing import Optional
from backend.agents.base_agent import BaseAgent
from backend.models.agent_messages import AgentMessage, SharedContext
from backend.tools.goal_calculator import evaluate_financial_goals

GOAL_SYSTEM_PROMPT = """
You are the specialized Goal & Financial Planning Agent in a Multi-Agent AI System.
Your sole responsibility is assessing user financial goals, calculating required monthly contributions,
and determining deadline feasibility against available monthly surplus.
Do NOT perform budget breakdown or risk evaluation belonging to other specialized agents.
Provide clear feasibility reasoning and deadline adjustments where monthly gaps exist.
"""

class GoalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="goal_agent",
            role="Goal & Financial Planning Agent",
            description="Prioritizes financial goals, computes required monthly savings, and evaluates target deadline feasibility."
        )

    def execute(self, shared_context: SharedContext, input_message: Optional[AgentMessage] = None) -> AgentMessage:
        self.log_state(shared_context, status="running")

        user_profile = shared_context.user_profile
        budget_analysis = shared_context.budget_analysis

        # Read dependency data from budget_agent message if available
        if input_message and input_message.data:
            available_surplus = float(input_message.data.get('monthly_surplus', 0.0))
        else:
            available_surplus = float(budget_analysis.get('monthly_surplus', 0.0))

        raw_goals = user_profile.get('goals', [])

        # Step 1: Run deterministic goal evaluation tool via execute_tool
        goal_eval_results = self.execute_tool(
            shared_context, "evaluate_financial_goals", evaluate_financial_goals,
            raw_goals, available_surplus
        )

        # Step 2: Formulate planning observations
        goals_summary = []
        for eg in goal_eval_results.get('evaluated_goals', []):
            status_str = "FEASIBLE" if eg['feasible'] else f"GAP ({eg['gap_per_month']}/mo)"
            goals_summary.append(
                f"Goal '{eg['goal_name']}': Target {eg['target_amount']} in {eg['deadline_months']}m -> "
                f"Required: {eg['required_monthly']}/mo | Allocated: {eg['allocated_monthly']}/mo [{status_str}]"
            )

        # Step 3: LLM Reasoning & Goal Prioritization Strategy
        task_prompt = (
            f"Evaluate goal portfolio for user with available surplus of {available_surplus}:\n"
            f"- Evaluated Goals: {goal_eval_results.get('evaluated_goals')}\n"
            f"- Total Required: {goal_eval_results.get('total_required_monthly')}\n"
            f"- Total Allocated: {goal_eval_results.get('total_allocated_monthly')}\n"
            f"- Total Monthly Gap: {goal_eval_results.get('total_gap_monthly')}\n"
            f"Provide a 2-sentence tactical recommendation on prioritization and deadline extensions."
        )
        llm_reasoning = self.llm_service.generate_completion(
            prompt=task_prompt,
            system_prompt=GOAL_SYSTEM_PROMPT,
            agent_name=self.name
        )

        goal_data = {
            "available_surplus_input": available_surplus,
            "total_required_monthly": goal_eval_results.get("total_required_monthly", 0.0),
            "total_allocated_monthly": goal_eval_results.get("total_allocated_monthly", 0.0),
            "total_gap_monthly": goal_eval_results.get("total_gap_monthly", 0.0),
            "surplus_remaining": goal_eval_results.get("surplus_remaining", 0.0),
            "overall_feasibility": goal_eval_results.get("overall_feasibility", "Unknown"),
            "evaluated_goals": goal_eval_results.get("evaluated_goals", []),
            "summary_statements": goals_summary,
            "llm_analysis": llm_reasoning
        }

        # Store in shared context
        shared_context.goal_analysis = goal_data

        summary = (
            f"Evaluated {len(raw_goals)} goals | Required: {goal_data['total_required_monthly']} | "
            f"Allocated: {goal_data['total_allocated_monthly']} | Status: {goal_data['overall_feasibility']}"
        )
        self.log_state(shared_context, status="completed", summary=summary)

        # Send message to Debt & Risk Agent
        output_msg = self.create_message(
            receiver="debt_risk_agent",
            message_type="goal_feasibility_analysis",
            data=goal_data,
            summary=summary,
            step_id=2,
            confidence=0.96
        )
        shared_context.messages.append(output_msg)
        return output_msg

