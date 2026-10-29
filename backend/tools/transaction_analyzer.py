"""
Transaction Analyzer Tool
Uses Pandas to process transaction streams, categorize spending, detect recurring
subscription drains, and flag anomalous high spending.
"""

import pandas as pd
from typing import List, Dict, Any, Optional

def analyze_transaction_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze a DataFrame of transactions and return summary metrics."""
    if df.empty:
        return {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "category_breakdown": {},
            "recurring_subscriptions": [],
            "anomalies": []
        }

    # Ensure required columns exist safely
    if 'amount' not in df.columns:
        df['amount'] = 0.0
    if 'type' not in df.columns:
        df['type'] = 'expense'
    if 'category' not in df.columns:
        df['category'] = 'Uncategorized'
    if 'description' not in df.columns:
        df['description'] = 'Unknown'

    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
    df['type'] = df['type'].astype(str).str.lower()
    df['category'] = df['category'].astype(str)

    income_df = df[df['type'] == 'income']
    expense_df = df[df['type'] == 'expense']

    total_income = float(income_df['amount'].sum())
    total_expenses = float(expense_df['amount'].sum())

    # Category breakdown
    category_summary = {}
    if not expense_df.empty:
        cat_group = expense_df.groupby('category')['amount'].sum()
        for cat, val in cat_group.items():
            category_summary[str(cat)] = round(float(val), 2)

    # Detect recurring subscriptions (e.g. Subscriptions, Netflix, Spotify, Gym, Utilities)
    recurring = []
    sub_df = expense_df[
        expense_df['category'].str.contains('Subscription|Utilities', case=False, na=False) |
        expense_df['description'].str.contains('Netflix|Spotify|Gym|Amazon|Cloud|Bill', case=False, na=False)
    ]
    for _, row in sub_df.iterrows():
        recurring.append({
            "description": str(row['description']),
            "category": str(row['category']),
            "amount": float(row['amount'])
        })

    # High spending anomalies (expenses > 2x mean expense)
    anomalies = []
    if not expense_df.empty and len(expense_df) > 3:
        mean_exp = expense_df['amount'].mean()
        high_exp = expense_df[expense_df['amount'] > (mean_exp * 2.0)]
        for _, row in high_exp.iterrows():
            anomalies.append({
                "description": str(row['description']),
                "category": str(row['category']),
                "amount": float(row['amount']),
                "reason": f"Expense exceeds 2x average transaction size ({round(mean_exp, 2)})"
            })

    return {
        "transaction_count": len(df),
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "category_breakdown": category_summary,
        "recurring_subscriptions": recurring,
        "anomalies": anomalies
    }

def analyze_transaction_list(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Helper wrapper to accept raw list of dict transactions."""
    if not transactions:
        return analyze_transaction_dataframe(pd.DataFrame())
    df = pd.DataFrame(transactions)
    return analyze_transaction_dataframe(df)

def load_and_analyze_csv(file_path: str) -> Dict[str, Any]:
    """Load a CSV file and return transaction analytics."""
    try:
        df = pd.read_csv(file_path)
        return analyze_transaction_dataframe(df)
    except Exception as e:
        return {"error": f"Failed to load CSV: {str(e)}"}
