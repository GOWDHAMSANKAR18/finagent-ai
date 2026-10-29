"""
Financial Health Score Calculator
Calculates a 0-100 deterministic financial health score based on 5 core metrics:
1. Savings Rate Score (20 pts)
2. Emergency Fund Cushion Score (20 pts)
3. Debt-to-Income (DTI) Score (20 pts)
4. Goal Feasibility Score (20 pts)
5. Fixed Expense Burden Score (20 pts)
"""

from typing import Dict, Any

def calculate_financial_health_score(
    income: float,
    fixed_expenses: float,
    variable_expenses: float,
    savings_rate: float,
    emergency_months_covered: float,
    dti_ratio: float,
    goal_feasibility_pct: float
) -> Dict[str, Any]:
    """Calculate deterministic financial health score out of 100."""
    
    # Factor 1: Savings Rate (Target >= 20%)
    if savings_rate >= 25.0:
        savings_score = 20.0
    elif savings_rate >= 20.0:
        savings_score = 18.0
    elif savings_rate >= 10.0:
        savings_score = 12.0
    elif savings_rate > 0.0:
        savings_score = 6.0
    else:
        savings_score = 0.0

    # Factor 2: Emergency Fund Cushion (Target >= 6 months)
    if emergency_months_covered >= 6.0:
        emergency_score = 20.0
    elif emergency_months_covered >= 3.0:
        emergency_score = 15.0
    elif emergency_months_covered >= 1.0:
        emergency_score = 8.0
    else:
        emergency_score = 2.0

    # Factor 3: Debt-to-Income (Target < 20%)
    if dti_ratio == 0.0:
        dti_score = 20.0
    elif dti_ratio <= 15.0:
        dti_score = 18.0
    elif dti_ratio <= 30.0:
        dti_score = 12.0
    elif dti_ratio <= 45.0:
        dti_score = 6.0
    else:
        dti_score = 0.0

    # Factor 4: Goal Feasibility (% achievable goals)
    goal_score = round((min(100.0, max(0.0, goal_feasibility_pct)) / 100.0) * 20.0, 1)

    # Factor 5: Fixed Expense Burden (Needs <= 50% income)
    fixed_ratio = (fixed_expenses / income * 100.0) if income > 0 else 100.0
    if fixed_ratio <= 40.0:
        fixed_score = 20.0
    elif fixed_ratio <= 50.0:
        fixed_score = 16.0
    elif fixed_ratio <= 65.0:
        fixed_score = 10.0
    else:
        fixed_score = 4.0

    total_score = int(round(savings_score + emergency_score + dti_score + goal_score + fixed_score))
    total_score = min(100, max(0, total_score))

    if total_score >= 80:
        rating = "Excellent"
        status_color = "emerald"
    elif total_score >= 65:
        rating = "Healthy"
        status_color = "cyan"
    elif total_score >= 50:
        rating = "Moderate Risk"
        status_color = "amber"
    else:
        rating = "Critical Action Required"
        status_color = "red"

    return {
        "overall_score": total_score,
        "rating": rating,
        "status_color": status_color,
        "score_breakdown": {
            "savings_rate_score": {"score": savings_score, "max": 20, "label": "Savings Rate (Target >= 20%)"},
            "emergency_fund_score": {"score": emergency_score, "max": 20, "label": "Emergency Cushion (Target 6m)"},
            "debt_management_score": {"score": dti_score, "max": 20, "label": "Debt-to-Income (Target < 20%)"},
            "goal_progress_score": {"score": goal_score, "max": 20, "label": "Goal Achievability Rate"},
            "expense_stability_score": {"score": fixed_score, "max": 20, "label": "Fixed Expense Burden (Target <= 50%)"}
        }
    }
