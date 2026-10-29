# MULTI-AGENT SYSTEM ARCHITECTURE SPECIFICATION

## 1. System Overview
The **AI Personal Finance & Financial Planning Multi-Agent Assistant** is engineered using a modular multi-agent architecture with centralized orchestration and cross-agent validation.

## 2. Multi-Agent Execution Pipeline

```text
Sequence Flow Diagram:

User / API -> FastAPI Backend: Submit UserProfile JSON
FastAPI -> Orchestrator: run_pipeline(profile)

Orchestrator -> BudgetAgent: execute(shared_context)
BudgetAgent -> FinancialCalculator: calculate_monthly_surplus(), calculate_savings_rate()
BudgetAgent -> TransactionAnalyzer: analyze_transaction_list() (Pandas)
BudgetAgent -> SharedContext: update budget_analysis & emit AgentMessage (Step 1)

Orchestrator -> GoalAgent: execute(shared_context, budget_msg)
GoalAgent -> GoalCalculator: evaluate_financial_goals()
GoalAgent -> SharedContext: update goal_analysis & emit AgentMessage (Step 2)

Orchestrator -> DebtRiskAgent: execute(shared_context, goal_msg)
DebtRiskAgent -> FinancialCalculator: calculate_debt_to_income(), calculate_emergency_fund_status()
DebtRiskAgent -> SharedContext: update debt_risk_analysis & emit AgentMessage (Step 3)

Orchestrator -> ResearchAgent: execute(shared_context, debt_msg)
ResearchAgent -> KnowledgeRetriever: query() (RAG over local JSON)
ResearchAgent -> SharedContext: update research_results & emit AgentMessage (Step 4)

Orchestrator -> RecommendationAgent: execute(shared_context, research_msg)
RecommendationAgent -> ValidationService: validate_and_reconcile_plan()
RecommendationAgent -> SharedContext: update final_plan & emit AgentMessage (Step 5)

Orchestrator -> FastAPI: Return SharedContext
FastAPI -> User: Render Dashboard & Live Activity Log
```

## 3. Agent Responsibilities & Isolation Boundaries

1. **Budget Agent (`budget_agent.py`)**:
   - Scope: Income, essential fixed costs, variable costs, cash flow surplus, savings rate, spending patterns.
   - Outputs: `monthly_income`, `fixed_expenses`, `variable_expenses`, `monthly_surplus`, `savings_rate`.

2. **Goal Agent (`goal_agent.py`)**:
   - Scope: Goal prioritization, required monthly allocation, deadline feasibility, gap analysis.
   - Outputs: `total_required_monthly`, `total_allocated_monthly`, `total_gap_monthly`, `evaluated_goals`.

3. **Debt & Risk Agent (`debt_risk_agent.py`)**:
   - Scope: Loan balances, EMIs, interest rates, DTI ratio, emergency fund adequacy, risk alerts.
   - Outputs: `total_debt_balance`, `dti_ratio`, `emergency_fund_status`, `risk_warnings`.

4. **Research Agent (`research_agent.py`)**:
   - Scope: RAG query, rule of thumb retrieval, educational disclaimers, data classification.
   - Outputs: `retrieved_knowledge`, `data_classification`.

5. **Recommendation Agent (`recommendation_agent.py`)**:
   - Scope: Cross-agent validation, budget balancing, monthly allocation synthesis, step-by-step action plan.
   - Outputs: `FinancialPlanOutput` object with 100% mathematical balance.

## 4. Shared Context Schema
The `SharedContext` class maintains mutable state passed safely across agents:
```python
class SharedContext(BaseModel):
    user_profile: Dict[str, Any]
    transaction_analysis: Dict[str, Any]
    budget_analysis: Dict[str, Any]
    goal_analysis: Dict[str, Any]
    debt_risk_analysis: Dict[str, Any]
    research_results: Dict[str, Any]
    validation_results: Dict[str, Any]
    final_plan: Dict[str, Any]
    messages: List[AgentMessage]
    agent_states: Dict[str, AgentTaskState]
```
