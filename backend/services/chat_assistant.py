"""
FinAgent AI — Conversational AI Assistant & Intent Orchestrator
Handles natural conversation, multi-turn session history, intent routing, structured tool execution,
and web application UI actions.
"""

import json
import re
from typing import Dict, Any, List, Optional
from backend.services.llm_service import LLMService, sanitize_prompt
from backend.tools.tool_registry import ToolRegistry, PAGE_MAP
from backend.agents.orchestrator import MultiAgentOrchestrator

# Session In-Memory History Storage
SESSION_HISTORIES: Dict[str, List[Dict[str, str]]] = {}

INTENTS = {
    "GENERAL_CHAT": "General greeting, pleasantry, or capability question",
    "FINANCIAL_QUESTION": "Educational financial concept or general advice query",
    "FINANCIAL_ANALYSIS": "Request to review profile, cash flow, spending, or financial health",
    "CREATE_OR_UPDATE": "Request to create or update goals, budgets, or debts",
    "SIMULATION": "What-if financial scenario request",
    "KNOWLEDGE_SEARCH": "Explicit rule or RAG knowledge lookup",
    "NAVIGATION": "Request to open, view, or navigate to an application page",
    "CLARIFICATION": "Ambiguous input requiring more context",
    "UNSUPPORTED": "Unsupported query"
}

class ChatAssistant:
    def __init__(self):
        self.llm_service = LLMService()
        self.orchestrator = MultiAgentOrchestrator()

    @staticmethod
    def get_session_history(session_id: str) -> List[Dict[str, str]]:
        """Retrieve stored message history for a session."""
        if session_id not in SESSION_HISTORIES:
            SESSION_HISTORIES[session_id] = []
        return SESSION_HISTORIES[session_id]

    @staticmethod
    def clear_session_history(session_id: str):
        """Clear session message history."""
        if session_id in SESSION_HISTORIES:
            SESSION_HISTORIES[session_id] = []

    def classify_intent(self, query: str) -> str:
        """
        Classify user query intent into defined categories.
        Uses fast rule classification with LLM fallback for nuanced queries.
        """
        q = query.lower().strip()

        # Navigation Intent
        if any(kw in q for kw in ["open ", "go to ", "show me ", "navigate ", "switch to ", "take me to "]):
            for page_kw in PAGE_MAP.keys():
                if page_kw in q:
                    return "NAVIGATION"

        # General Chat / Greetings
        if q in ["hi", "hello", "hey", "greetings", "good morning", "good evening", "thanks", "thank you", "bye"]:
            return "GENERAL_CHAT"
        if "what can you do" in q or "who are you" in q or "help me" in q:
            return "GENERAL_CHAT"

        # Goal Creation / Profile Modification
        if any(act in q for act in ["create", "add", "set", "save", "update", "change"]) and any(entity in q for entity in ["goal", "budget", "income", "expense", "debt", "loan"]):
            return "CREATE_OR_UPDATE"


        # What-if Simulation
        if any(kw in q for kw in ["what if", "simulate", "increase income", "reduce expense"]):
            return "SIMULATION"

        # Financial Analysis
        if any(kw in q for kw in ["analyze", "health score", "spending", "dti", "report", "overview"]):
            return "FINANCIAL_ANALYSIS"

        # Knowledge Base Search
        if any(kw in q for kw in ["50/30/20", "avalanche", "snowball", "emergency fund rule", "rule of 72"]):
            return "KNOWLEDGE_SEARCH"

        return "FINANCIAL_QUESTION"

    def process_message(
        self,
        query: str,
        profile_data: Optional[Dict[str, Any]] = None,
        session_id: str = "default_session"
    ) -> Dict[str, Any]:
        """
        Main processing pipeline for conversational AI chat.
        Tracks session context, executes intent routing, performs tool calling, and outputs UI actions.
        """
        raw_query = query.strip()
        safe_query = sanitize_prompt(raw_query)
        profile = profile_data or {}
        history = self.get_session_history(session_id)

        intent = self.classify_intent(safe_query)

        # ----------------------------------------------------
        # 1. GENERAL_CHAT (0 Heavy Agents Called)
        # ----------------------------------------------------
        if intent == "GENERAL_CHAT":
            answer = self._handle_general_chat(safe_query, history=history)
            self._append_to_history(session_id, safe_query, answer)
            return {
                "answer": answer,
                "intent": intent,
                "action": None,
                "explainability": {
                    "why": "Handled by Conversational Layer with real LLM inference without unnecessary financial agent execution.",
                    "agents_involved": ["conversational_assistant"],
                    "confidence_score": 0.99,
                    "active_engine": self.llm_service.last_engine,
                    "is_live_llm": self.llm_service.is_last_live
                }
            }

        # ----------------------------------------------------
        # 2. NAVIGATION (Web App UI Control)
        # ----------------------------------------------------
        if intent == "NAVIGATION":
            q_lower = safe_query.lower()
            matched_page = "overview"
            for k in PAGE_MAP.keys():
                if k in q_lower:
                    matched_page = k
                    break

            nav_res = ToolRegistry.execute_tool("navigate_to_page", {"target_page": matched_page})
            action_obj = nav_res.get("action")
            target_name = action_obj.get("target_name", matched_page.title()) if action_obj else matched_page.title()
            answer = f"I've switched your view to **{target_name}**. You can now interact with this feature directly."
            self._append_to_history(session_id, safe_query, answer)
            return {
                "answer": answer,
                "intent": intent,
                "action": action_obj,
                "explainability": {
                    "why": "Executed UI Navigation tool to update active application view.",
                    "agents_involved": ["ui_controller"],
                    "confidence_score": 1.0,
                    "active_engine": "UI Controller Engine",
                    "is_live_llm": False
                }
            }

        # ----------------------------------------------------
        # 3. CREATE_OR_UPDATE (Action-Capable Web Control)
        # ----------------------------------------------------
        if intent == "CREATE_OR_UPDATE":
            if "goal" in safe_query.lower():
                goal_name = "Savings Goal"
                target_amount = 50000.0
                deadline = 12

                amt_match = re.search(r"₹?\s*([\d,]+)", safe_query)
                if amt_match:
                    try:
                        target_amount = float(amt_match.group(1).replace(",", ""))
                    except ValueError:
                        pass

                deadline_match = re.search(r"(\d+)\s*(?:months?|mo)", safe_query, re.IGNORECASE)
                if deadline_match:
                    try:
                        deadline = int(deadline_match.group(1))
                    except ValueError:
                        pass

                name_match = re.search(r"goal (?:for|of|named) ([a-zA-Z0-9\s]+)", safe_query, re.IGNORECASE)
                if name_match:
                    goal_name = name_match.group(1).strip()
                elif "emergency" in safe_query.lower():
                    goal_name = "Emergency Fund"
                elif "laptop" in safe_query.lower():
                    goal_name = "Laptop Purchase"

                tool_res = ToolRegistry.execute_tool("create_financial_goal", {
                    "name": goal_name,
                    "target_amount": target_amount,
                    "deadline_months": deadline
                }, profile_data=profile)

                action_obj = tool_res.get("action")
                answer = f"I have created a new savings goal: **{goal_name}** with a target of **₹{target_amount:,.2f}** over {deadline} months."
                self._append_to_history(session_id, safe_query, answer)
                return {
                    "answer": answer,
                    "intent": intent,
                    "action": action_obj,
                    "explainability": {
                        "why": "Executed Goal Creation tool and generated UI action payload.",
                        "agents_involved": ["goal_agent"],
                        "confidence_score": 0.96,
                        "active_engine": "Deterministic Goal Tool",
                        "is_live_llm": False
                    }
                }

        # ----------------------------------------------------
        # 4. SIMULATION
        # ----------------------------------------------------
        if intent == "SIMULATION":
            inc_delta = 0.0
            exp_red = 2000.0
            
            amt_matches = re.findall(r"₹?\s*([\d,]+)", safe_query)
            if "income" in safe_query.lower() and amt_matches:
                try:
                    inc_delta = float(amt_matches[0].replace(",", ""))
                except ValueError:
                    pass
            if "expense" in safe_query.lower() and len(amt_matches) > 1:
                try:
                    exp_red = float(amt_matches[1].replace(",", ""))
                except ValueError:
                    pass

            tool_res = ToolRegistry.execute_tool("run_savings_simulation", {
                "income_delta": inc_delta,
                "expense_reduction": exp_red,
                "extra_savings": 5000.0
            }, profile_data=profile)

            action_obj = tool_res.get("action")
            sim_data = tool_res.get("result", {}).get("simulation", {})
            surplus = sim_data.get("simulated_surplus", 0)

            answer = f"Simulation completed! With an income adjustment of +₹{inc_delta:,.2f} and expense reduction of ₹{exp_red:,.2f}, your projected monthly surplus increases to **₹{surplus:,.2f}**."
            self._append_to_history(session_id, safe_query, answer)
            return {
                "answer": answer,
                "intent": intent,
                "action": action_obj,
                "explainability": {
                    "why": "Ran What-If Simulation Engine with requested parameter adjustments.",
                    "agents_involved": ["simulation_agent"],
                    "confidence_score": 0.98,
                    "active_engine": "Deterministic Simulation Tool",
                    "is_live_llm": False
                }
            }

        # ----------------------------------------------------
        # 5. FINANCIAL_ANALYSIS / FINANCIAL_QUESTION (Grounded Execution)
        # ----------------------------------------------------
        income = profile.get("monthly_income", 60000)
        fixed = profile.get("fixed_expenses", 22000)
        variable = profile.get("variable_expenses", 15000)
        expenses = fixed + variable
        surplus = income - expenses

        system_prompt = (
            "You are FinAgent AI, a helpful, precise personal financial assistant. "
            "Answer the user's question in a clear, encouraging, and structured way. "
            "Consider the user's available context and financial situation. "
            "If asked about a specific expense (e.g. food spending), interpret the amount in context of income and budget. "
            "Ask clarifying questions if key information like income or household size is missing before judging an expense as excessive."
        )

        hist_str = ""
        if history:
            hist_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-4:]]) + "\n"

        context_str = f"User Profile Facts: Income = ₹{income:,.2f}, Fixed Needs = ₹{fixed:,.2f}, Variable Wants = ₹{variable:,.2f}, Net Surplus = ₹{surplus:,.2f}."
        prompt = f"Context: {context_str}\n{hist_str}User Question: {safe_query}"

        llm_response = self.llm_service.generate_completion(prompt, system_prompt=system_prompt, agent_name="chat_assistant")
        answer = llm_response if llm_response else f"Based on your profile, your monthly income is ₹{income:,.2f} and total expenses are ₹{expenses:,.2f}, giving a net surplus of ₹{surplus:,.2f}."

        self._append_to_history(session_id, safe_query, answer)
        return {
            "answer": answer,
            "intent": intent,
            "action": None,
            "explainability": {
                "why": "Grounded in conversational financial reasoning and user profile data.",
                "agents_involved": ["budget_agent", "recommendation_agent"],
                "confidence_score": 0.98,
                "active_engine": self.llm_service.last_engine,
                "is_live_llm": self.llm_service.is_last_live
            }
        }

    def _handle_general_chat(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """Formulate natural conversational response using LLM inference."""
        system_prompt = (
            "You are FinAgent AI, a friendly, intelligent personal financial assistant. "
            "Respond naturally, warmly, and concisely to greetings, pleasantries, or capability questions. "
            "Explain your supported capabilities (budgeting, goal tracking, debt payoff, what-if simulations, CSV transaction analysis, application navigation) clearly when asked."
        )
        hist_str = ""
        if history:
            hist_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-4:]]) + "\n"

        prompt = f"{hist_str}User: {query}"
        res = self.llm_service.generate_completion(prompt, system_prompt=system_prompt, agent_name="chat_assistant")
        if res and len(res.strip()) > 0 and "Processed multi-agent query" not in res:
            return res

        q = query.lower()
        if any(kw in q for kw in ["hi", "hello", "hey", "greetings", "good morning", "good evening"]):
            return "Hi! I'm your FinAgent AI assistant. I can help you understand your finances, analyze spending, plan budgets, track goals, and explore ways to improve your financial health. What would you like to work on?"
        if "what can you do" in q or "who are you" in q:
            return "I can analyze your financial data, review spending, help build budgets, track savings goals, evaluate debt payoff strategies, run what-if simulations, and navigate application pages for you. How can I help today?"
        if any(kw in q for kw in ["thanks", "thank you"]):
            return "You're very welcome! Let me know if you need anything else to optimize your financial goals."
        return "I'm here to assist with your financial planning, budgeting, goal tracking, and what-if simulations. How can I assist you?"

    def _append_to_history(self, session_id: str, user_msg: str, assistant_msg: str):
        """Append message turn to session history with window cap of 20 messages."""
        history = self.get_session_history(session_id)
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_msg})
        if len(history) > 20:
            SESSION_HISTORIES[session_id] = history[-20:]

