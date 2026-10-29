"""
Subscription Optimizer Tool
Scans transaction history for recurring merchants and subscription drains,
calculating monthly/annual recurring costs and potential optimizations.
"""

from typing import List, Dict, Any

SUBSCRIPTION_KEYWORDS = [
    "netflix", "spotify", "gym", "amazon prime", "hulu", "disney", "adobe",
    "cloud", "storage", "icloud", "apple", "chatgpt", "midjourney", "youtube",
    "membership", "subscription", "domain", "hosting", "playstation", "xbox", "utility"
]

def analyze_subscriptions(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Scans transaction list and outputs subscription breakdown."""
    if not transactions:
        return {
            "subscription_count": 0,
            "total_monthly_cost": 0.0,
            "total_annual_cost": 0.0,
            "potential_annual_savings": 0.0,
            "detected_subscriptions": []
        }

    detected = []
    total_monthly = 0.0

    for tx in transactions:
        desc = str(tx.get("description", "")).lower()
        cat = str(tx.get("category", "")).lower()
        amt = float(tx.get("amount", 0.0))

        is_sub = any(kw in desc or kw in cat for kw in SUBSCRIPTION_KEYWORDS)
        if is_sub and amt > 0:
            total_monthly += amt
            detected.append({
                "merchant": tx.get("description", "Subscription"),
                "category": tx.get("category", "Subscriptions"),
                "monthly_amount": round(amt, 2),
                "annual_amount": round(amt * 12.0, 2),
                "optimization_note": f"Review frequency of use for {tx.get('description')} to evaluate utility vs cost."
            })

    annual_cost = round(total_monthly * 12.0, 2)
    # Potential optimization estimate (assuming 25-30% negotiable/unused subscriptions)
    potential_savings = round(annual_cost * 0.30, 2)

    return {
        "subscription_count": len(detected),
        "total_monthly_cost": round(total_monthly, 2),
        "total_annual_cost": annual_cost,
        "potential_annual_savings": potential_savings,
        "detected_subscriptions": detected
    }

detect_recurring_subscriptions = analyze_subscriptions

