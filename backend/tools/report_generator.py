"""
Financial Report Generator Tool
Exports synthesized financial plans as JSON, CSV summary, or plain text Markdown reports.
"""

import json
from typing import Dict, Any

def generate_text_report(final_plan: Dict[str, Any]) -> str:
    """Generates a clean text Markdown report from the final plan."""
    if not final_plan:
        return "No financial plan available for report generation."

    summary = final_plan.get("summary", {})
    budget = final_plan.get("budget_breakdown", {})
    goals = final_plan.get("goal_evaluations", [])
    debt = final_plan.get("debt_evaluation", {})
    risks = final_plan.get("risk_assessment", [])
    allocations = final_plan.get("proposed_monthly_plan", [])
    action_items = final_plan.get("action_plan", [])

    lines = []
    lines.append("=" * 70)
    lines.append("       FINANCIAL PLANNING MULTI-AGENT ASSISTANT - REPORT")
    lines.append("=" * 70)
    lines.append(f"Plan Status: {summary.get('plan_status', 'N/A')}")
    lines.append(f"Monthly Income: ₹{summary.get('monthly_income', 0):,.2f}")
    lines.append(f"Fixed Expenses: ₹{summary.get('fixed_expenses', 0):,.2f}")
    lines.append(f"Variable Expenses: ₹{summary.get('variable_expenses', 0):,.2f}")
    lines.append(f"Monthly Surplus: ₹{summary.get('monthly_surplus', 0):,.2f}")
    lines.append(f"Savings Rate: {summary.get('savings_rate', 0)}%")
    lines.append(f"Debt-to-Income (DTI): {summary.get('dti_ratio', 0)}%")
    lines.append(f"Emergency Fund: {summary.get('emergency_fund_months', 0)} months covered")
    lines.append(f"Health Rating: {summary.get('health_rating', 'N/A')}")
    lines.append("-" * 70)
    lines.append("\n[PROPOSED MONTHLY BUDGET ALLOCATION]")

    for item in allocations:
        lines.append(f"  • {item.get('category')}: ₹{item.get('allocated_amount', 0):,.2f} ({item.get('percentage_of_income', 0)}%)")

    lines.append("\n[GOAL EVALUATIONS]")
    for g in goals:
        status = "FEASIBLE" if g.get("feasible") else "UNFEASIBLE"
        lines.append(f"  • {g.get('goal_name')}: Target ₹{g.get('target_amount', 0):,.2f} in {g.get('deadline_months')}m | Required: ₹{g.get('required_monthly', 0):,.2f}/mo [{status}]")

    lines.append("\n[IDENTIFIED RISKS & WARNINGS]")
    if not risks:
        lines.append("  • No major financial risks detected.")
    else:
        for r in risks:
            lines.append(f"  • [{r.get('severity')}] {r.get('risk_title')}: {r.get('description')}")

    lines.append("\n[PRIORITY ACTION PLAN]")
    for act in action_items:
        lines.append(f"  {act}")

    lines.append("\n" + "=" * 70)
    lines.append("Disclaimer: University Multi-Agent Academic Demonstration. Not regulated financial advice.")
    lines.append("=" * 70)

    return "\n".join(lines)
