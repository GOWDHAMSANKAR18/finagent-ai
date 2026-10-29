"""
Financial Calculator Tool
Provides exact, deterministic mathematical calculations for cash flow, savings rate,
debt-to-income (DTI) ratio, emergency fund adequacy, and loan payoffs.
"""

from typing import Dict, Any, List

def calculate_monthly_surplus(income: float, fixed_expenses: float, variable_expenses: float) -> float:
    """Calculate net monthly surplus after essential and discretionary expenses."""
    return round(income - (fixed_expenses + variable_expenses), 2)

def calculate_savings_rate(monthly_surplus: float, monthly_income: float) -> float:
    """Calculate savings rate percentage."""
    if monthly_income <= 0:
        return 0.0
    return round((monthly_surplus / monthly_income) * 100, 2)

def calculate_debt_to_income(total_monthly_emi: float, gross_monthly_income: float) -> float:
    """Calculate Debt-to-Income (DTI) ratio percentage."""
    if gross_monthly_income <= 0:
        return 0.0
    return round((total_monthly_emi / gross_monthly_income) * 100, 2)

def calculate_emergency_fund_status(
    current_emergency_fund: float,
    monthly_fixed_expenses: float,
    target_months: int = 6
) -> Dict[str, Any]:
    """Calculate emergency fund adequacy in terms of months of essential expenses."""
    if monthly_fixed_expenses <= 0:
        months_covered = 99.0
    else:
        months_covered = round(current_emergency_fund / monthly_fixed_expenses, 1)

    target_amount = round(monthly_fixed_expenses * target_months, 2)
    shortfall = max(0.0, round(target_amount - current_emergency_fund, 2))
    is_adequate = months_covered >= 3.0

    return {
        "current_balance": current_emergency_fund,
        "monthly_essential_expense": monthly_fixed_expenses,
        "months_covered": months_covered,
        "target_months": target_months,
        "target_amount": target_amount,
        "shortfall": shortfall,
        "is_adequate": is_adequate,
        "status": "Healthy" if months_covered >= 6 else ("Manageable" if months_covered >= 3 else "Critical Shortfall")
    }

def calculate_loan_payoff_estimate(
    total_balance: float,
    monthly_emi: float,
    annual_interest_rate: float
) -> Dict[str, Any]:
    """Estimate loan payoff duration and total interest payable given EMI."""
    if total_balance <= 0 or monthly_emi <= 0:
        return {"months_to_payoff": 0, "total_interest": 0.0, "status": "Paid Off"}

    monthly_rate = (annual_interest_rate / 100.0) / 12.0
    
    # Check if monthly EMI covers monthly interest
    monthly_interest = total_balance * monthly_rate
    if monthly_emi <= monthly_interest and monthly_rate > 0:
        return {
            "months_to_payoff": 999,
            "total_interest": 999999.0,
            "status": "Warning: EMI too low to cover interest (Negative Amortization)"
        }

    balance = total_balance
    months = 0
    total_interest_paid = 0.0

    while balance > 0 and months < 360:
        interest = balance * monthly_rate
        principal = monthly_emi - interest
        if principal > balance:
            principal = balance
            interest = balance * monthly_rate
        balance -= principal
        total_interest_paid += interest
        months += 1

    return {
        "months_to_payoff": months,
        "total_interest": round(total_interest_paid, 2),
        "total_payout": round(total_balance + total_interest_paid, 2),
        "status": "Calculated"
    }

def calculate_50_30_20_budget(income: float, fixed_expenses: float, variable_expenses: float) -> Dict[str, Any]:
    """Calculate 50/30/20 budget allocations and comparison against actual spending."""
    target_fixed = round(income * 0.50, 2)
    target_variable = round(income * 0.30, 2)
    target_savings = round(income * 0.20, 2)
    
    surplus = calculate_monthly_surplus(income, fixed_expenses, variable_expenses)
    savings_rate = calculate_savings_rate(surplus, income)
    
    return {
        "monthly_income": income,
        "fixed_expenses": fixed_expenses,
        "variable_expenses": variable_expenses,
        "monthly_surplus": surplus,
        "savings_rate": savings_rate,
        "target_50_fixed": target_fixed,
        "target_30_variable": target_variable,
        "target_20_savings": target_savings,
        "fixed_delta": round(fixed_expenses - target_fixed, 2),
        "variable_delta": round(variable_expenses - target_variable, 2),
        "savings_delta": round(surplus - target_savings, 2)
    }

def detect_spending_anomalies(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect unusual or high expenditure anomalies in transaction data."""
    anomalies = []
    for tx in transactions:
        amt = float(tx.get("amount", tx.get("Amount", 0)))
        tx_type = str(tx.get("type", tx.get("Type", ""))).lower()
        if amt > 10000 and tx_type != "income" and tx_type != "credit":
            anomalies.append({
                "transaction": tx,
                "reason": f"High expenditure anomaly (> ₹10,000): ₹{amt:,.2f}"
            })
    return anomalies

