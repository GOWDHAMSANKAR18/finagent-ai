"""
FinAgent AI — Unified Tool Registry & Action Execution Engine
Exposes structured financial data tools, goal & debt planning tools, simulation tools,
RAG knowledge retrieval tools, and Web Application Navigation/Control tools.
"""

from typing import Dict, Any, List, Optional
from backend.tools.financial_calculator import calculate_50_30_20_budget, detect_spending_anomalies
from backend.tools.goal_calculator import evaluate_goal_feasibility
from backend.tools.health_score_calculator import calculate_financial_health_score
from backend.tools.simulation_engine import run_what_if_simulation, compare_debt_payoff_strategies
from backend.tools.knowledge_retriever import KnowledgeRetriever
from backend.tools.transaction_analyzer import analyze_transaction_list
from backend.tools.subscription_optimizer import detect_recurring_subscriptions

knowledge_retriever = KnowledgeRetriever()

# Page Mapping Dictionary connecting human-friendly target names to UI view IDs
PAGE_MAP = {
    "overview": "overview-view",
    "dashboard": "overview-view",
    "home": "overview-view",
    "financial overview": "overview-view",
    "analysis": "analysis-view",
    "budget": "analysis-view",
    "budget planner": "analysis-view",
    "profile": "analysis-view",
    "simulator": "simulator-view",
    "simulation": "simulator-view",
    "what-if": "simulator-view",
    "chat": "chat-view",
    "advisor": "chat-view",
    "ai advisor": "chat-view",
    "agents": "agents-view",
    "agent swarm": "agents-view",
    "multi-agent": "agents-view",
    "goals": "goals-view",
    "goal": "goals-view",
    "milestones": "goals-view",
    "debt": "debt-view",
    "debt planner": "debt-view",
    "loans": "debt-view",
    "transactions": "transactions-view",
    "csv": "transactions-view",
    "reports": "reports-view",
    "knowledge": "knowledge-view",
    "knowledge base": "knowledge-view",
    "rag": "knowledge-view",
    "evaluation": "eval-view",
    "benchmark": "eval-view",
    "settings": "settings-view"
}

class ToolRegistry:
    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """Return schema definitions for all available AI tools."""
        return [
            {
                "name": "navigate_to_page",
                "description": "Switch the web application main view to a specified page (e.g. overview, budget planner, goals, debt planner, simulator, chat, agents, transactions, reports, knowledge base, settings).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_page": {
                            "type": "string",
                            "description": "Name of the target page: 'overview', 'analysis', 'simulator', 'chat', 'agents', 'goals', 'debt', 'transactions', 'reports', 'knowledge', 'eval', or 'settings'."
                        }
                    },
                    "required": ["target_page"]
                }
            },
            {
                "name": "get_financial_overview",
                "description": "Calculate cash flow breakdown, monthly surplus, savings rate, and overall health score from profile data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "monthly_income": {"type": "number"},
                        "fixed_expenses": {"type": "number"},
                        "variable_expenses": {"type": "number"}
                    },
                    "required": ["monthly_income", "fixed_expenses", "variable_expenses"]
                }
            },
            {
                "name": "create_financial_goal",
                "description": "Create or add a new financial goal to the active profile.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Goal title e.g. Emergency Fund, Laptop, Vacation"},
                        "target_amount": {"type": "number", "description": "Target financial goal amount in rupees"},
                        "deadline_months": {"type": "integer", "description": "Timeline in months"},
                        "priority": {"type": "integer", "description": "Goal priority level (1=highest)"}
                    },
                    "required": ["name", "target_amount", "deadline_months"]
                },
                "requires_confirmation": False
            },
            {
                "name": "update_budget",
                "description": "Update monthly income and expense allocations in the user profile.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "monthly_income": {"type": "number"},
                        "fixed_expenses": {"type": "number"},
                        "variable_expenses": {"type": "number"}
                    },
                    "required": ["monthly_income", "fixed_expenses", "variable_expenses"]
                },
                "requires_confirmation": True
            },
            {
                "name": "analyze_debt",
                "description": "Evaluate debt-to-income ratio and compare Debt Avalanche vs Debt Snowball strategies.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "debts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "total_balance": {"type": "number"},
                                    "monthly_emi": {"type": "number"},
                                    "interest_rate_annual": {"type": "number"}
                                }
                            }
                        },
                        "extra_monthly_allocation": {"type": "number"}
                    },
                    "required": ["debts"]
                }
            },
            {
                "name": "run_savings_simulation",
                "description": "Simulate what-if scenario adjusting income, expenses, or savings delta.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "income_delta": {"type": "number"},
                        "expense_reduction": {"type": "number"},
                        "extra_savings": {"type": "number"}
                    },
                    "required": []
                }
            },
            {
                "name": "search_financial_knowledge",
                "description": "Query local RAG knowledge base for educational rules, 50/30/20 guidelines, or debt payoff advice.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        ]

    @staticmethod
    def execute_tool(tool_name: str, arguments: Dict[str, Any], profile_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Safely execute a registered tool and return structured execution result.
        """
        profile = profile_data or {}
        
        if tool_name == "navigate_to_page":
            raw_target = str(arguments.get("target_page", "overview")).lower().strip()
            view_id = PAGE_MAP.get(raw_target, "overview-view")
            # Fallback search if target name is contained in key
            if view_id == "overview-view" and raw_target != "overview":
                for k, v in PAGE_MAP.items():
                    if k in raw_target:
                        view_id = v
                        break
            return {
                "success": True,
                "action": {
                    "type": "navigate",
                    "target": view_id,
                    "target_name": raw_target.title()
                },
                "result": f"Switched UI view to '{raw_target.title()}' ({view_id})."
            }

        elif tool_name == "get_financial_overview":
            income = float(arguments.get("monthly_income", profile.get("monthly_income", 60000)))
            fixed = float(arguments.get("fixed_expenses", profile.get("fixed_expenses", 22000)))
            variable = float(arguments.get("variable_expenses", profile.get("variable_expenses", 15000)))
            
            budget_res = calculate_50_30_20_budget(income, fixed, variable)
            health_res = calculate_financial_health_score(
                income=income,
                fixed_expenses=fixed,
                variable_expenses=variable,
                existing_savings=float(profile.get("existing_savings", 50000)),
                emergency_fund=float(profile.get("emergency_fund", 30000)),
                debts=profile.get("debts", [])
            )
            return {
                "success": True,
                "result": {
                    "budget": budget_res,
                    "health_score": health_res
                }
            }

        elif tool_name == "create_financial_goal":
            goal_name = arguments.get("name", "New Goal")
            target = float(arguments.get("target_amount", 50000))
            deadline = int(arguments.get("deadline_months", 12))
            priority = int(arguments.get("priority", 1))

            new_goal = {
                "name": goal_name,
                "target_amount": target,
                "deadline_months": deadline,
                "priority": priority,
                "current_allocated": 0.0
            }

            return {
                "success": True,
                "action": {
                    "type": "create_goal",
                    "goal": new_goal
                },
                "result": f"Goal '{goal_name}' for ₹{target:,.2f} over {deadline} months created successfully."
            }

        elif tool_name == "update_budget":
            inc = float(arguments.get("monthly_income", profile.get("monthly_income", 60000)))
            fix = float(arguments.get("fixed_expenses", profile.get("fixed_expenses", 22000)))
            var = float(arguments.get("variable_expenses", profile.get("variable_expenses", 15000)))

            return {
                "success": True,
                "action": {
                    "type": "update_budget",
                    "data": {
                        "monthly_income": inc,
                        "fixed_expenses": fix,
                        "variable_expenses": var
                    }
                },
                "result": f"Budget updated: Income ₹{inc:,.2f}, Fixed ₹{fix:,.2f}, Variable ₹{var:,.2f}."
            }

        elif tool_name == "analyze_debt":
            debts = arguments.get("debts", profile.get("debts", []))
            extra = float(arguments.get("extra_monthly_allocation", 3000))
            comp = compare_debt_payoff_strategies(debts, extra)
            return {
                "success": True,
                "result": comp
            }

        elif tool_name == "run_savings_simulation":
            inc_delta = float(arguments.get("income_delta", 0))
            exp_red = float(arguments.get("expense_reduction", 0))
            extra_sav = float(arguments.get("extra_savings", 0))

            sim_res = run_what_if_simulation(profile, {
                "income_delta": inc_delta,
                "expense_reduction": exp_red,
                "extra_savings": extra_sav
            })
            return {
                "success": True,
                "action": {
                    "type": "run_simulation",
                    "params": {"income_delta": inc_delta, "expense_reduction": exp_red, "extra_savings": extra_sav}
                },
                "result": sim_res
            }

        elif tool_name == "search_financial_knowledge":
            query = str(arguments.get("query", ""))
            results = knowledge_retriever.query(query, top_k=3)
            return {
                "success": True,
                "result": results
            }

        else:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' is not supported."
            }
