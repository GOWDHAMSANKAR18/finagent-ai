"""
Agent 4 — Financial Research & Knowledge Agent (RAG Engine)
Queries the domain knowledge base to provide educational concepts, standard financial benchmarks,
and explicit citations to support decision-making.
Uses explicit specialized LLM prompt and tool tracking.
"""

from typing import Optional
from backend.agents.base_agent import BaseAgent
from backend.models.agent_messages import AgentMessage, SharedContext
from backend.tools.knowledge_retriever import KnowledgeRetriever

RESEARCH_SYSTEM_PROMPT = """
You are the specialized Financial Research & Knowledge Agent (RAG Engine) in a Multi-Agent AI System.
Your sole responsibility is retrieving verified domain financial principles, educational benchmarks,
and explicit citations from the local Knowledge Base.
Do NOT perform direct numerical budget calculations or validation belonging to other agents.
Synthesize retrieved guidelines into actionable educational citations.
"""

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="research_agent",
            role="Financial Research & Knowledge Agent",
            description="Retrieves domain financial rules, educational disclaimers, and standard benchmarks via RAG."
        )
        self.retriever = KnowledgeRetriever()

    def execute(self, shared_context: SharedContext, input_message: Optional[AgentMessage] = None) -> AgentMessage:
        self.log_state(shared_context, status="running")

        budget_info = shared_context.budget_analysis
        goal_info = shared_context.goal_analysis
        debt_info = shared_context.debt_risk_analysis

        # Formulate query text based on findings
        query_terms = []
        if debt_info.get('dti_ratio', 0) > 20:
            query_terms.append("Debt to income DTI ratio Avalanche Snowball")
        if not debt_info.get('emergency_fund_status', {}).get('is_adequate', True):
            query_terms.append("Emergency fund liquid savings threshold")
        if goal_info.get('total_gap_monthly', 0) > 0:
            query_terms.append("Goal feasibility monthly savings gap")

        query_terms.append("50/30/20 budgeting rule savings rate inflation")
        combined_query = " ".join(query_terms)

        # Retrieve knowledge items via RAG tool using execute_tool
        retrieved_docs = self.execute_tool(
            shared_context, "KnowledgeRetriever.query", self.retriever.query,
            combined_query, top_k=4
        )

        # Distinguish source origins for academic clarity
        categorized_facts = {
          "user_provided_facts": [
              f"Monthly Income: {shared_context.user_profile.get('monthly_income')}",
              f"Fixed Expenses: {shared_context.user_profile.get('fixed_expenses')}",
              f"Variable Expenses: {shared_context.user_profile.get('variable_expenses')}"
          ],
          "calculated_metrics": [
              f"Monthly Surplus: {budget_info.get('monthly_surplus')}",
              f"Savings Rate: {budget_info.get('savings_rate')}%",
              f"Debt-to-Income Ratio: {debt_info.get('dti_ratio')}%"
          ],
          "retrieved_kb_sources": retrieved_docs
        }

        # LLM Synthesis of RAG knowledge
        task_prompt = (
            f"Synthesize the following retrieved financial rules for recommendations:\n"
            f"- Query: {combined_query}\n"
            f"- Retrieved Sources: {retrieved_docs}\n"
            f"Provide a 2-sentence summary of applicable financial standards and rules of thumb."
        )
        llm_reasoning = self.llm_service.generate_completion(
            prompt=task_prompt,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            agent_name=self.name
        )

        research_data = {
            "query_used": combined_query,
            "retrieved_knowledge": retrieved_docs,
            "data_classification": categorized_facts,
            "llm_analysis": llm_reasoning
        }

        # Store in shared context
        shared_context.research_results = research_data

        summary = f"Retrieved {len(retrieved_docs)} financial rules & standards from local Knowledge Base."
        self.log_state(shared_context, status="completed", summary=summary)

        # Send message to Recommendation Agent
        output_msg = self.create_message(
            receiver="recommendation_agent",
            message_type="knowledge_and_citations",
            data=research_data,
            summary=summary,
            step_id=4,
            confidence=0.99
        )
        shared_context.messages.append(output_msg)
        return output_msg

