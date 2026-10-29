"""
Central Multi-Agent Orchestrator
Manages lifecycle, agent selection, task delegation, dependency sequence, feedback loops,
parallel execution, bounded retries, timeouts, max step constraints, and traceable logs.
"""

import time
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as ExecTimeoutError
from backend.models.agent_messages import SharedContext, AgentMessage, AgentTaskState
from backend.agents.budget_agent import BudgetAgent
from backend.agents.goal_agent import GoalAgent
from backend.agents.debt_risk_agent import DebtRiskAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.recommendation_agent import RecommendationAgent
from backend.services.llm_service import LLMService

MAX_COORDINATION_STEPS = 10
DEFAULT_AGENT_TIMEOUT_SECONDS = 10.0

class MultiAgentOrchestrator:
    def __init__(self):
        self.budget_agent = BudgetAgent()
        self.goal_agent = GoalAgent()
        self.debt_risk_agent = DebtRiskAgent()
        self.research_agent = ResearchAgent()
        self.recommendation_agent = RecommendationAgent()

    def select_agents(self, task_intent: str = "full_plan") -> List[str]:
        """
        Dynamically selects participating agents based on user request intent.
        Ensures a minimum of 3 specialized agents collaborate for any workflow.
        """
        intent = task_intent.lower()
        if "goal" in intent:
            # Collaboration among Budget, Goal, and Recommendation Agents
            return ["budget_agent", "goal_agent", "recommendation_agent"]
        elif "debt" in intent or "risk" in intent:
            # Collaboration among Budget, Debt/Risk, Research, and Recommendation Agents
            return ["budget_agent", "debt_risk_agent", "research_agent", "recommendation_agent"]
        else:
            # Complete 5-agent multi-agent pipeline
            return ["budget_agent", "goal_agent", "debt_risk_agent", "research_agent", "recommendation_agent"]

    def run_pipeline(
        self,
        user_profile: Dict[str, Any],
        parallel_mode: bool = False,
        enable_feedback: bool = True,
        task_intent: str = "full_plan"
    ) -> SharedContext:
        """
        Executes the multi-agent pipeline with dynamic selection, explicit dependency sequence,
        bounded retries, timeouts, and max coordination step constraints.
        """
        shared_context = SharedContext(user_profile=user_profile)
        selected_agents = self.select_agents(task_intent)

        shared_context.agent_states["orchestrator"] = AgentTaskState(
            agent_name="orchestrator",
            status="running",
            started_at=time.time(),
            output_summary=f"Task intent '{task_intent}' selecting agents: {', '.join(selected_agents)}"
        )

        coordination_steps = 0

        try:
            # Step 1: Budget Agent Execution (Foundation)
            if "budget_agent" in selected_agents and coordination_steps < MAX_COORDINATION_STEPS:
                coordination_steps += 1
                budget_msg = self.budget_agent.execute(shared_context)
            else:
                budget_msg = None

            # Step 2: Goal, Debt, and Research Execution
            if not parallel_mode:
                goal_msg = None
                debt_msg = None
                research_msg = None

                if "goal_agent" in selected_agents and coordination_steps < MAX_COORDINATION_STEPS:
                    coordination_steps += 1
                    goal_msg = self.goal_agent.execute(shared_context, input_message=budget_msg)

                if "debt_risk_agent" in selected_agents and coordination_steps < MAX_COORDINATION_STEPS:
                    coordination_steps += 1
                    input_for_debt = goal_msg if goal_msg else budget_msg
                    debt_msg = self.debt_risk_agent.execute(shared_context, input_message=input_for_debt)

                if "research_agent" in selected_agents and coordination_steps < MAX_COORDINATION_STEPS:
                    coordination_steps += 1
                    input_for_research = debt_msg if debt_msg else budget_msg
                    research_msg = self.research_agent.execute(shared_context, input_message=input_for_research)
            else:
                # Parallel Execution Mode for non-dependent branches
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = {}
                    if "goal_agent" in selected_agents:
                        futures["goal_agent"] = executor.submit(self.goal_agent.execute, shared_context, budget_msg)
                    if "debt_risk_agent" in selected_agents:
                        futures["debt_risk_agent"] = executor.submit(self.debt_risk_agent.execute, shared_context, budget_msg)
                    if "research_agent" in selected_agents:
                        futures["research_agent"] = executor.submit(self.research_agent.execute, shared_context, budget_msg)

                    for name, f in futures.items():
                        try:
                            f.result(timeout=DEFAULT_AGENT_TIMEOUT_SECONDS)
                        except ExecTimeoutError:
                            print(f"[Orchestrator] Agent {name} timed out after {DEFAULT_AGENT_TIMEOUT_SECONDS}s.")

            # Step 3: Synthesis via Recommendation Agent
            if "recommendation_agent" in selected_agents and coordination_steps < MAX_COORDINATION_STEPS:
                coordination_steps += 1
                self.recommendation_agent.execute(shared_context)

            # Step 4: Delegation & Validation Feedback Loop with Bounded Retries
            if enable_feedback and coordination_steps < MAX_COORDINATION_STEPS:
                val_res = shared_context.validation_results
                if val_res.get("has_conflict") or not val_res.get("is_valid"):
                    target_agent_name = val_res.get("delegate_to", "goal_agent")
                    reason = val_res.get("delegation_reason", "Validation constraint violation detected.")

                    coordination_steps += 1
                    delegation_entry = {
                        "trigger": "Validation Conflict Detected",
                        "step_number": coordination_steps,
                        "target_agent": target_agent_name,
                        "reason": reason,
                        "action": "Re-evaluating agent calculations and regenerating recommendations",
                        "timestamp": time.time()
                    }
                    shared_context.delegation_history.append(delegation_entry)

                    # Trigger delegated agent re-execution
                    if target_agent_name == "goal_agent":
                        self.goal_agent.execute(shared_context)
                    elif target_agent_name == "budget_agent":
                        self.budget_agent.execute(shared_context)
                    elif target_agent_name == "debt_risk_agent":
                        self.debt_risk_agent.execute(shared_context)

                    # Re-run Recommendation Agent to synthesize updated plan
                    self.recommendation_agent.execute(shared_context)

                    delegation_entry["status"] = "resolved"
                    delegation_entry["resolved_at"] = time.time()

            shared_context.agent_states.pop("orchestrator", None)

        except Exception as e:
            print(f"[Orchestrator] Pipeline execution error: {e}")
            error_state = AgentTaskState(
                agent_name="orchestrator",
                status="failed",
                error=str(e)
            )
            shared_context.agent_states["orchestrator"] = error_state
            try:
                self.recommendation_agent.execute(shared_context)
            except Exception as inner_e:
                print(f"[Orchestrator] Fallback recovery failed: {inner_e}")

        return shared_context

    def run_single_agent_baseline(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Baseline Single-Agent system for evaluation.
        Executes a monolithic single prompt process without agent breakdown or validation loops.
        """
        t0 = time.perf_counter()
        llm = LLMService()

        system_prompt = (
            "You are a monolithic personal finance assistant. Analyze the user's financial profile "
            "and provide monthly cash flow surplus, DTI ratio, goal feasibility, debt risks, and "
            "a monthly budget allocation plan."
        )
        user_prompt = f"User Profile Data: {user_profile}"

        completion_text = llm.generate_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            agent_name="single_agent_baseline"
        )
        elapsed = round(time.perf_counter() - t0, 4)

        income = float(user_profile.get('monthly_income', 0.0))
        fixed = float(user_profile.get('fixed_expenses', 0.0))
        var = float(user_profile.get('variable_expenses', 0.0))
        surplus = income - (fixed + var)

        return {
            "system_type": "Single-Agent Monolithic Baseline",
            "monthly_income": income,
            "total_expenses": fixed + var,
            "monthly_surplus": surplus,
            "completion_summary": completion_text,
            "execution_time_seconds": elapsed,
            "llm_calls": 1,
            "tool_calls": 0
        }
