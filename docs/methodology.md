# RESEARCH METHODOLOGY & MULTI-AGENT DESIGN THEORY

## 1. Problem Identification & Academic Rationale
Monolithic Large Language Models (LLMs) suffer from significant failure modes when applied to complex financial planning:
1. **Mathematical Calculation Drift**: LLMs frequently produce inaccurate rounding or hallucinated arithmetic.
2. **Context Contamination**: Mixing debt payoff, emergency cushion allocation, and goal timelines in a single prompt causes prompt interference.
3. **Lack of Observable Audit Trail**: Users and evaluators cannot see why a specific allocation was recommended.

The Multi-Agent architecture solves this by decomposing tasks into specialized agents bound to deterministic Python mathematical tools.

## 2. Tool & Reasoning Separation
```text
           +---------------------------------------------------+
           |                 SPECIALIZED AGENT                 |
           +-------------------------+-------------------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               v                                           v
    +--------------------+                       +--------------------+
    | DETERMINISTIC TOOL |                       |   LLM SERVICE      |
    | (Python / Pandas / |                       | (Prompt Reasoning  |
    |  Math Calculations)|                       |   & Synthesizer)   |
    +--------------------+                       +--------------------+
```

## 3. Validation & Conflict Resolution Logic
The `validation_service.py` module enforces strict boundary conditions:
- Priority 1: Mandatory Needs (Fixed essential expenses).
- Priority 2: Minimum Debt EMIs & Emergency Fund top-up if months covered < 3.
- Priority 3: High-interest debt payoff acceleration (Debt Avalanche).
- Priority 4: Goal allocations (sorted by priority rank and target deadline).
- Priority 5: Flexible Cash Reserve buffer.
