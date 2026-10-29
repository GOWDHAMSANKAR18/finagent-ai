"""
Simulation Engine Tool
Provides deterministic calculations for What-If scenario simulations and
Debt Payoff Strategy comparison (Avalanche vs Snowball vs Minimum payments).
"""

from typing import Dict, Any, List
import copy

def run_what_if_simulation(
    base_profile: Dict[str, Any],
    modifications: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Runs a what-if simulation modifying user inputs without mutating active state.
    """
    sim_profile = copy.deepcopy(base_profile)

    # Apply scenario delta modifications
    if "income_delta" in modifications:
        sim_profile["monthly_income"] = max(0.0, sim_profile.get("monthly_income", 0.0) + float(modifications["income_delta"]))
    if "fixed_expenses_delta" in modifications:
        sim_profile["fixed_expenses"] = max(0.0, sim_profile.get("fixed_expenses", 0.0) + float(modifications["fixed_expenses_delta"]))
    if "variable_expenses_delta" in modifications:
        sim_profile["variable_expenses"] = max(0.0, sim_profile.get("variable_expenses", 0.0) + float(modifications["variable_expenses_delta"]))
    if "extra_savings_monthly" in modifications:
        extra_savings = float(modifications["extra_savings_monthly"])
        # Reduce variable expenses or add to surplus
        sim_profile["variable_expenses"] = max(0.0, sim_profile.get("variable_expenses", 0.0) - extra_savings)

    income = float(sim_profile.get("monthly_income", 0.0))
    fixed = float(sim_profile.get("fixed_expenses", 0.0))
    var = float(sim_profile.get("variable_expenses", 0.0))
    surplus = income - (fixed + var)
    savings_rate = round((surplus / income * 100), 1) if income > 0 else 0.0

    # Impact on goals
    goals = sim_profile.get("goals", [])
    sim_goals = []
    total_required = 0.0

    for g in goals:
        target = float(g.get("target_amount", 0.0))
        deadline = max(1, int(g.get("deadline_months", 1)))
        saved = float(g.get("current_allocated", 0.0))
        needed = max(0.0, target - saved)
        req_monthly = round(needed / deadline, 2)
        total_required += req_monthly

        feasible = surplus >= req_monthly
        sim_goals.append({
            "name": g.get("name", "Goal"),
            "required_monthly": req_monthly,
            "feasible": feasible,
            "simulated_months_to_achieve": round(needed / surplus, 1) if surplus > 0 else 999
        })

    return {
        "scenario_name": modifications.get("scenario_name", "Custom What-If Scenario"),
        "simulated_income": income,
        "simulated_fixed": fixed,
        "simulated_variable": var,
        "simulated_surplus": round(surplus, 2),
        "simulated_savings_rate": savings_rate,
        "surplus_delta": round(surplus - (base_profile.get("monthly_income", 0) - (base_profile.get("fixed_expenses", 0) + base_profile.get("variable_expenses", 0))), 2),
        "goal_impacts": sim_goals
    }

def compare_debt_payoff_strategies(
    debts: List[Dict[str, Any]],
    extra_monthly_allocation: float = 0.0
) -> Dict[str, Any]:
    """
    Compares Debt Avalanche (highest APR first) vs Debt Snowball (lowest balance first)
    vs Minimum Payments only.
    """
    if not debts:
        return {
            "strategies": {},
            "recommendation": "No debts specified."
        }

    # Minimum payments baseline
    total_balance = sum(float(d.get("total_balance", 0.0)) for d in debts)
    total_emi = sum(float(d.get("monthly_emi", 0.0)) for d in debts)

    if total_balance <= 0 or total_emi <= 0:
        return {
            "strategies": {
                "avalanche": {"months": 0, "total_interest": 0.0},
                "snowball": {"months": 0, "total_interest": 0.0}
            },
            "recommendation": "All debts paid off."
        }

    # Avalanche Simulation (Sort by APR DESC)
    avalanche_debts = sorted(debts, key=lambda d: float(d.get("interest_rate_annual", 0)), reverse=True)
    avalanche_res = _simulate_payoff_sequence(avalanche_debts, extra_monthly_allocation)

    # Snowball Simulation (Sort by Balance ASC)
    snowball_debts = sorted(debts, key=lambda d: float(d.get("total_balance", 0)))
    snowball_res = _simulate_payoff_sequence(snowball_debts, extra_monthly_allocation)

    # Minimum only Simulation
    minimum_debts = copy.deepcopy(debts)
    minimum_res = _simulate_payoff_sequence(minimum_debts, 0.0)

    interest_saved = round(minimum_res["total_interest"] - avalanche_res["total_interest"], 2)
    months_saved = max(0, minimum_res["months"] - avalanche_res["months"])

    return {
        "total_debt_balance": round(total_balance, 2),
        "extra_monthly_allocation": extra_monthly_allocation,
        "strategies": {
            "avalanche": {
                "name": "Debt Avalanche (Highest APR First)",
                "payoff_months": avalanche_res["months"],
                "total_interest_paid": avalanche_res["total_interest"],
                "interest_saved_vs_minimum": interest_saved,
                "months_saved": months_saved
            },
            "snowball": {
                "name": "Debt Snowball (Lowest Balance First)",
                "payoff_months": snowball_res["months"],
                "total_interest_paid": snowball_res["total_interest"],
                "interest_saved_vs_minimum": round(minimum_res["total_interest"] - snowball_res["total_interest"], 2)
            },
            "minimum_only": {
                "name": "Minimum Payments Only",
                "payoff_months": minimum_res["months"],
                "total_interest_paid": minimum_res["total_interest"]
            }
        },
        "recommendation": f"Debt Avalanche saves {interest_saved} in interest and cuts payoff duration by {months_saved} months compared to minimum payments."
    }

def _simulate_payoff_sequence(debts_list: List[Dict[str, Any]], extra_cash: float) -> Dict[str, Any]:
    active_debts = [copy.deepcopy(d) for d in debts_list]
    months = 0
    total_interest = 0.0

    while any(float(d.get("total_balance", 0)) > 0 for d in active_debts) and months < 360:
        months += 1
        current_extra = extra_cash

        for d in active_debts:
            bal = float(d.get("total_balance", 0))
            if bal <= 0:
                continue

            rate = (float(d.get("interest_rate_annual", 0)) / 100.0) / 12.0
            emi = float(d.get("monthly_emi", 0))
            
            interest = round(bal * rate, 2)
            total_interest += interest

            principal = emi - interest
            if principal < 0:
                principal = 0

            # Add extra payment to first remaining active debt
            if current_extra > 0:
                principal += current_extra
                current_extra = 0.0

            if principal >= bal:
                current_extra += (principal - bal)
                d["total_balance"] = 0.0
            else:
                d["total_balance"] = round(bal - principal, 2)

    return {"months": months, "total_interest": round(total_interest, 2)}
