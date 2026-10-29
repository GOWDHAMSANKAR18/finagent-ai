# VIVA VOCE PREPARATION GUIDE (35+ COMPREHENSIVE QUESTIONS & ANSWERS)

## CATEGORY 1: GENERAL & CONCEPTUAL (Q1 - Q7)

### Q1: What is a Multi-Agent System (MAS)?
**Answer**: A Multi-Agent System is a computerized system composed of multiple interacting, autonomous intelligent agents designed to solve complex problems that are beyond the individual capabilities or knowledge capacity of a single monolithic agent.

### Q2: Why did you choose Personal Finance for this multi-agent project?
**Answer**: Personal financial planning requires distinct domain specialties—budget analytics, goal allocation strategy, debt payoff optimization, risk detection, and regulatory rule lookup. Decomposing these responsibilities into specialized agents mirrors real-world expert collaboration and prevents context contamination in LLMs.

### Q3: Why is a multi-agent system better than a single prompt AI assistant?
**Answer**: Single prompt AI assistants suffer from context overload, mathematical calculation errors, and missed risk edge-cases. Multi-agent decomposition isolates responsibilities, enforces deterministic python tools for arithmetic, and uses cross-agent validation to achieve 100% mathematical allocation accuracy.

### Q4: What is the main research question of your project?
**Answer**: "Does decomposing personal financial planning into specialized collaborating AI agents improve financial analysis completeness, consistency, and error detection compared with a single general-purpose AI agent?"

### Q5: How many specialized agents exist in your system?
**Answer**: Five specialized agents: (1) Budget Agent, (2) Goal Agent, (3) Debt & Risk Agent, (4) Research Agent, and (5) Recommendation Agent, plus a central Orchestrator.

### Q6: Does your system rely on third-party API keys to run?
**Answer**: No. The system features a provider abstraction supporting Gemini, OpenAI, Ollama, AND a built-in deterministic local rule engine fallback that operates 100% offline out-of-the-box.

### Q7: Is this system giving regulated financial advice?
**Answer**: No. The system explicitly provides educational financial planning guidance, includes disclaimers on all outputs, and distinguishes user facts, calculations, retrieved rules, and AI suggestions.

---

## CATEGORY 2: ARCHITECTURE & AGENT COMMUNICATION (Q8 - Q15)

### Q8: What is the role of the central Orchestrator?
**Answer**: The Orchestrator receives user profiles, initializes shared context, coordinates sequential agent invocation, passes dependency outputs between agents, handles agent failures, and forwards validated results to the recommendation agent.

### Q9: How do agents communicate with each other?
**Answer**: Agents communicate using a structured JSON message standard containing `sender`, `receiver`, `message_type`, `data` payload, `confidence` score, `timestamp`, `step_id`, and a human-readable `summary`.

### Q10: What is Shared Context?
**Answer**: Shared Context (`SharedContext`) is a centralized state structure that stores intermediate outputs from each agent (`budget_analysis`, `goal_analysis`, `debt_risk_analysis`, `research_results`, `validation_results`), message logs, and execution states.

### Q11: Give an example of inter-agent dependency in your project.
**Answer**: The Budget Agent calculates `monthly_surplus`. The Goal Agent consumes `monthly_surplus` from the Budget Agent's message payload to calculate goal savings feasibility. The Debt/Risk Agent then consumes goal allocations to check emergency fund adequacy and DTI constraints.

### Q12: How are conflicts resolved between agents?
**Answer**: The `validation_service.py` module evaluates proposed allocations from Budget, Goal, and Debt agents against total income. If goal allocations exceed surplus or emergency fund cushion is inadequate, the validator rebalances priorities programmatically.

### Q13: What happens if an agent fails during pipeline execution?
**Answer**: The Orchestrator logs the agent task state as `failed` with the traceback, and invokes deterministic fallback rules for that stage, ensuring the pipeline synthesizes a valid final plan without crashing.

### Q14: Why did you build an Agent Activity Panel in the UI?
**Answer**: To make multi-agent communication, delegation, structured payloads, confidence scores, and task progression fully observable live during academic demonstrations.

### Q15: How does data flow from user input to final plan?
**Answer**: User Profile -> FastAPI `/api/analyze` -> Orchestrator -> Budget Agent -> Goal Agent -> Debt/Risk Agent -> Research Agent -> Recommendation Agent -> Validation Service -> Synthesized Plan & UI Dashboard.

---

## CATEGORY 3: AI & RAG RETRIEVAL (Q16 - Q22)

### Q16: How is RAG (Retrieval-Augmented Generation) implemented in your project?
**Answer**: Agent 4 (Research Agent) uses `knowledge_retriever.py` to perform semantic keyword scoring over a local domain database (`financial_knowledge.json`) containing 50/30/20 rules, DTI guidelines, and debt repayment strategies.

### Q17: Why use RAG instead of trusting the LLM's internal memory?
**Answer**: RAG prevents hallucination of financial rules, grounds suggestions in verified educational benchmarks, and provides explicit citations for every recommendation.

### Q18: Which LLM provider did you use?
**Answer**: The system uses a modular `LLMService` supporting Google Gemini (gemini-1.5-flash), OpenAI (gpt-3.5-turbo), Ollama local models (qwen2.5:7b), or a local deterministic rule engine.

### Q19: What is prompt engineering in your project?
**Answer**: Prompt engineering defines strict system prompts for each specialized agent, instructing it on its specific persona, input constraints, expected JSON keys, and tool call triggers.

### Q20: How do you prevent LLMs from hallucinating calculations?
**Answer**: All mathematical calculations (surplus, savings rate, DTI, goal gap, loan payoff) are calculated by deterministic Python tools (`financial_calculator.py`, `goal_calculator.py`), not by the LLM.

### Q21: How does the system classify data sources?
**Answer**: Information is explicitly categorized into: (1) User Provided Facts, (2) Calculated Metrics, (3) Retrieved Knowledge Base Sources, and (4) AI Generated Allocation Recommendations.

### Q22: What confidence score is attached to agent messages?
**Answer**: Each message carries a confidence rating (0.0 to 1.0) based on calculation completeness and tool verification status (typically 0.95–0.99).

---

## CATEGORY 4: FINANCIAL MATHEMATICS & LOGIC (Q23 - Q30)

### Q23: How is Monthly Cash Surplus calculated?
**Answer**: \(\text{Surplus} = \text{Monthly Income} - (\text{Fixed Expenses} + \text{Variable Expenses})\).

### Q24: How is Savings Rate calculated?
**Answer**: \(\text{Savings Rate} = \left(\frac{\text{Monthly Surplus}}{\text{Monthly Income}}\right) \times 100\). Healthy benchmark is \(\ge 20\%\).

### Q25: How is Debt-to-Income (DTI) ratio calculated?
**Answer**: \(\text{DTI} = \left(\frac{\text{Total Monthly EMI Payments}}{\text{Gross Monthly Income}}\right) \times 100\). Healthy DTI is \(< 20\%\); critical distress is \(\ge 40\%\).

### Q26: What is Emergency Fund Adequacy?
**Answer**: \(\text{Months Covered} = \frac{\text{Liquid Emergency Fund}}{\text{Monthly Essential Expenses}}\). Minimum threshold is 3 to 6 months.

### Q27: Explain Debt Avalanche vs Debt Snowball.
**Answer**: Debt Avalanche pays off debts with the highest annual interest rate first, minimizing interest mathematically. Debt Snowball pays off smallest balance debts first for psychological wins. Our Debt Agent defaults to Avalanche.

### Q28: How is Goal Feasibility evaluated?
**Answer**: \(\text{Required Monthly} = \frac{\text{Target Amount} - \text{Current Saved}}{\text{Deadline Months}}\). If Required Monthly > Available Surplus, a monthly gap is flagged.

### Q29: How does the system handle an Impossible Goal?
**Answer**: Instead of hallucinating money, the system flags the goal as "Unfeasible", calculates the exact monthly gap (e.g. ₹1.61L/month), and recommends extending the target deadline or cutting variable spending.

### Q30: What is the 50/30/20 rule?
**Answer**: A standard budgeting guideline allocating 50% of income to Needs, 30% to Wants, and 20% to Savings & Debt Repayment.

---

## CATEGORY 5: EVALUATION & BENCHMARKING (Q31 - Q37)

### Q31: How did you evaluate your Multi-Agent system?
**Answer**: By running automated comparative benchmarks against a Single-Agent Monolithic Baseline across 7 test cases measuring Accuracy, Completeness, Consistency, Risk Detection, Response Time, and LLM Calls.

### Q32: What were the key numerical evaluation results?
**Answer**: Multi-Agent improved Calculation Accuracy from 71.4% to 100.0% (+28.6%), Risk Detection from 62.1% to 100.0% (+37.9%), and Logical Consistency from 60.7% to 100.0% (+39.3%).

### Q33: What is the response time trade-off?
**Answer**: Multi-agent local execution took ~0.045s vs 1.25s for single agent, delivering significantly higher accuracy at low computational overhead.

### Q34: Why did Single-Agent Baseline fail on high expense and debt cases?
**Answer**: Monolithic prompts failed to enforce mathematical boundaries, promised unfeasible goal allocations, and missed emergency fund deficit warnings.

### Q35: How many unit and integration tests exist in your test suite?
**Answer**: 10 comprehensive unit and integration test cases in `tests/` covering budget math, transaction parsing, goal allocation gaps, debt DTI, agent state transitions, and E2E pipeline execution. All 10 pass with 100% success.

### Q36: What is the primary academic takeaway of this project?
**Answer**: Specialized multi-agent decomposition coupled with deterministic tool bindings eliminates mathematical hallucinations and dramatically improves logical consistency in domain-specific AI planning.

### Q37: What are future research directions for this project?
**Answer**: Integrating live open banking APIs, tax optimization engines, dynamic investment portfolio rebalancing, and reinforcement learning for dynamic multi-objective budget optimization.
