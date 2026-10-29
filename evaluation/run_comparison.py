"""
CLI Benchmark Runner
Executes empirical ground-truth benchmark tests comparing Single-Agent Baseline vs Multi-Agent System vs Ablation.
"""

import json
from evaluation.multi_agent_evaluation import run_benchmark_evaluation

def main():
    print("=" * 85)
    print("      ACADEMIC BENCHMARK EVALUATION: SINGLE-AGENT VS MULTI-AGENT SYSTEM")
    print("=" * 85)

    results = run_benchmark_evaluation()
    summary = results.get("evaluation_summary", {})

    sa = summary.get("single_agent_baseline", {})
    ma = summary.get("multi_agent_system", {})
    ab = summary.get("ablation_without_validation", {})

    print(f"\n{'METRIC':<35} | {'SINGLE AGENT':<14} | {'MULTI-AGENT':<14} | {'NO VALIDATION':<14}")
    print("-" * 85)
    print(f"{'Overall Plan Accuracy (%)':<35} | {sa.get('average_accuracy_pct'):<14} | {ma.get('average_accuracy_pct'):<14} | {ab.get('average_accuracy_pct'):<14}")
    print(f"{'Average Response Time (s)':<35} | {sa.get('average_latency_seconds'):<14} | {ma.get('average_latency_seconds'):<14} | {ab.get('average_latency_seconds'):<14}")
    print(f"{'Average LLM Calls':<35} | {sa.get('average_llm_calls'):<14} | {ma.get('average_llm_calls'):<14} | {ab.get('average_llm_calls'):<14}")
    print(f"{'Average Tool Calls':<35} | {sa.get('average_tool_calls'):<14} | {ma.get('average_tool_calls'):<14} | {ab.get('average_tool_calls'):<14}")
    print(f"{'Delegation Feedback Loops':<35} | {'0':<14} | {ma.get('total_delegation_loops_triggered'):<14} | {'0':<14}")
    print("=" * 85)
    print("Full empirical results saved to evaluation/results/evaluation_summary.json and evaluation_report.md")

if __name__ == "__main__":
    main()
