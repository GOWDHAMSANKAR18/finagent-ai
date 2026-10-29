"""
Validation Service
Performs cross-agent validation, mathematical sanity checks, conflict resolution,
and checks budget allocation constraints. Returns feedback/delegation directives for orchestrator.
"""

from typing import Dict, Any, List, Optional

def validate_and_reconcile_plan(
    user_profile: Dict[str, Any],
    budget_analysis: Dict[str, Any],
    goal_analysis: Dict[str, Any],
    debt_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validates agent outputs against strict financial constraints.
    Reconciles conflicting allocations between debt repayment, goal savings, and emergency fund.
    Detects inter-agent conflicts and provides explicit delegation directives.
    """
    income = float(user_profile.get('monthly_income', 0.0))
    fixed_exp = float(user_profile.get('fixed_expenses', 0.0))
    var_exp = float(user_profile.get('variable_expenses', 0.0))
    surplus = float(budget_analysis.get('monthly_surplus', income - (fixed_exp + var_exp)))

    validation_flags = []
    has_conflict = False
    delegate_to: Optional[str] = None
    delegation_reason: Optional[str] = None

    # Check 1: Budget Deficit Conflict (Fixed + Variable > Income)
    if fixed_exp + var_exp > income:
        has_conflict = True
        delegate_to = "budget_agent"
        deficit = round((fixed_exp + var_exp) - income, 2)
        delegation_reason = f"Total monthly expenses ({fixed_exp + var_exp}) exceed income ({income}). Net deficit: ₹{deficit}."
        validation_flags.append({
            "type": "Budget Deficit",
            "severity": "Critical",
            "message": delegation_reason
        })

    # Check 2: Emergency Fund Adequacy vs Debt Repayment Priority vs Goal Allocations
    emergency_fund_info = debt_analysis.get('emergency_fund_status', {})
    months_covered = emergency_fund_info.get('months_covered', 6.0)
    
    proposed_emergency_fund_monthly = 0.0
    proposed_debt_repayment_monthly = 0.0
    proposed_goal_savings_monthly = 0.0
    proposed_flexible_spending = 0.0

    # Priority Reconciliation Logic
    if surplus > 0:
        remaining = surplus

        # Priority 1: Emergency Fund top-up if below 3 months essential expenses
        if months_covered < 3.0:
            eff_target_shortfall = emergency_fund_info.get('shortfall', fixed_exp * 3.0)
            emf_alloc = min(remaining * 0.40, round(eff_target_shortfall / 6.0, 2))
            proposed_emergency_fund_monthly = round(emf_alloc, 2)
            remaining -= proposed_emergency_fund_monthly
            validation_flags.append({
                "type": "Emergency Fund Rebalancing",
                "severity": "Warning",
                "message": f"Emergency fund is below 3 months ({months_covered} months covered). Allocated ₹{proposed_emergency_fund_monthly}/month."
            })

        # Priority 2: High Interest Debt Extra Repayment if DTI > 25% or High Interest Present
        dti = debt_analysis.get('dti_ratio', 0.0)
        has_high_interest_debt = debt_analysis.get('has_high_interest_debt', False)

        if has_high_interest_debt or dti > 25.0:
            debt_extra_alloc = min(remaining * 0.50, round(surplus * 0.35, 2))
            proposed_debt_repayment_monthly = round(debt_extra_alloc, 2)
            remaining -= proposed_debt_repayment_monthly
            validation_flags.append({
                "type": "Debt Repayment Acceleration",
                "severity": "Warning",
                "message": f"High interest debt detected (DTI: {dti}%). Prioritized extra debt payoff allocation of ₹{proposed_debt_repayment_monthly}/month."
            })

        # Priority 3: Financial Goals
        goal_required = float(goal_analysis.get('total_required_monthly', 0.0))
        goal_allocated = float(goal_analysis.get('total_allocated_monthly', 0.0))

        # Conflict Check 3: Goal Allocation Exceeds Remaining Surplus after High-Priority Reserves
        if goal_required > remaining and goal_required > 0 and not has_conflict:
            has_conflict = True
            delegate_to = "goal_agent"
            gap = round(goal_required - remaining, 2)
            delegation_reason = f"Goal required allocation (₹{goal_required}/mo) exceeds available post-safety surplus (₹{round(remaining, 2)}/mo). Gap: ₹{gap}/mo."
            validation_flags.append({
                "type": "Goal Allocation Exceeds Surplus",
                "severity": "Warning",
                "message": delegation_reason
            })

        actual_goal_alloc = min(remaining, goal_allocated if goal_allocated > 0 else goal_required)
        proposed_goal_savings_monthly = round(max(0.0, actual_goal_alloc), 2)
        remaining -= proposed_goal_savings_monthly

        # Priority 4: Flexible Cash Reserve
        proposed_flexible_spending = round(max(0.0, remaining), 2)

    total_allocated = round(
        fixed_exp + var_exp + proposed_emergency_fund_monthly +
        proposed_debt_repayment_monthly + proposed_goal_savings_monthly + proposed_flexible_spending, 2
    )

    is_mathematically_balanced = abs(total_allocated - income) <= 1.0

    return {
        "is_valid": not has_conflict,
        "has_conflict": has_conflict,
        "delegate_to": delegate_to,
        "delegation_reason": delegation_reason,
        "is_mathematically_balanced": is_mathematically_balanced,
        "total_allocated": total_allocated,
        "income": income,
        "reconciled_allocations": {
            "fixed_expenses": fixed_exp,
            "variable_expenses": var_exp,
            "emergency_fund": proposed_emergency_fund_monthly,
            "debt_repayment": proposed_debt_repayment_monthly,
            "goal_savings": proposed_goal_savings_monthly,
            "flexible_spending": proposed_flexible_spending
        },
        "validation_flags": validation_flags
    }

