"""
Goal Calculator Tool
Determines required monthly allocations for short-term and long-term financial goals,
assesses feasibility against monthly cash surplus, and computes allocation gaps.
"""

from typing import List, Dict, Any

def evaluate_financial_goals(
    goals: List[Dict[str, Any]],
    available_monthly_surplus: float
) -> Dict[str, Any]:
    """
    Evaluates financial goals against available monthly surplus.
    Prioritizes goals by explicit priority rank and deadline.
    """
    if not goals:
        return {
            "total_required_monthly": 0.0,
            "allocated_goals": [],
            "surplus_remaining": available_monthly_surplus,
            "overall_feasibility": "No goals specified"
        }

    # Sort goals by priority ASC (1 is highest), then deadline_months ASC
    sorted_goals = sorted(goals, key=lambda g: (g.get('priority', 3), g.get('deadline_months', 12)))

    evaluated_goals = []
    total_required = 0.0
    remaining_surplus = available_monthly_surplus

    for g in sorted_goals:
        name = g.get('name', 'Goal')
        target = float(g.get('target_amount', 0.0))
        deadline = max(1, int(g.get('deadline_months', 1)))
        current_saved = float(g.get('current_allocated', 0.0))
        net_needed = max(0.0, target - current_saved)
        required_monthly = round(net_needed / deadline, 2)
        total_required += required_monthly

        if remaining_surplus >= required_monthly:
            allocated = required_monthly
            feasible = True
            gap = 0.0
            status = "Feasible"
            timeline_rec = f"On track to achieve target in {deadline} months with {allocated}/month allocation."
            remaining_surplus -= allocated
        elif remaining_surplus > 0:
            allocated = round(remaining_surplus, 2)
            feasible = False
            gap = round(required_monthly - allocated, 2)
            revised_months = round(net_needed / allocated, 1) if allocated > 0 else 999
            status = f"Partially Feasible (Gap: {gap}/month)"
            timeline_rec = f"Surplus shortfall of {gap}/month. At current surplus, goal will require ~{revised_months} months instead of {deadline} months."
            remaining_surplus = 0.0
        else:
            allocated = 0.0
            feasible = False
            gap = required_monthly
            status = "Unfeasible (Deficit)"
            timeline_rec = f"No surplus available. Requires {required_monthly}/month. Reduce expenses or extend target deadline."

        evaluated_goals.append({
            "goal_name": name,
            "target_amount": target,
            "deadline_months": deadline,
            "current_allocated": current_saved,
            "net_amount_needed": net_needed,
            "required_monthly": required_monthly,
            "allocated_monthly": allocated,
            "feasible": feasible,
            "feasibility_status": status,
            "gap_per_month": gap,
            "timeline_recommendation": timeline_rec
        })

    is_all_feasible = all(eg['feasible'] for eg in evaluated_goals)
    total_gap = max(0.0, round(total_required - available_monthly_surplus, 2))

    return {
        "total_required_monthly": round(total_required, 2),
        "total_allocated_monthly": round(available_monthly_surplus - remaining_surplus, 2),
        "total_gap_monthly": total_gap,
        "surplus_remaining": round(remaining_surplus, 2),
        "overall_feasibility": "Fully Achievable" if is_all_feasible else "Requires Allocation Trade-offs",
        "evaluated_goals": evaluated_goals
    }

def evaluate_goal_feasibility(goal: Dict[str, Any], monthly_surplus: float) -> Dict[str, Any]:
    """Alias/single goal feasibility calculation wrapper."""
    res = evaluate_financial_goals([goal], monthly_surplus)
    evals = res.get("evaluated_goals", [])
    return evals[0] if evals else {}

