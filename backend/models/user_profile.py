from pydantic import BaseModel, Field
from typing import List, Optional

class FinancialGoal(BaseModel):
    name: str = Field(..., description="Name of the financial goal e.g. Emergency Fund, Laptop, House")
    target_amount: float = Field(..., description="Target monetary amount required")
    deadline_months: int = Field(..., description="Target time horizon in months")
    current_allocated: float = Field(default=0.0, description="Current money saved toward this goal")
    priority: int = Field(default=1, description="Priority level 1 (High) to 5 (Low)")

class DebtItem(BaseModel):
    name: str = Field(..., description="Description of the debt/loan e.g. Credit Card, Education Loan")
    total_balance: float = Field(..., description="Remaining principal debt balance")
    monthly_emi: float = Field(..., description="Mandatory minimum monthly repayment / EMI")
    interest_rate_annual: float = Field(..., description="Annual interest rate percentage e.g. 18.0 for 18%")

class TransactionItem(BaseModel):
    date: str
    description: str
    category: str
    amount: float
    type: str = "expense"  # 'income' or 'expense'

class UserProfile(BaseModel):
    monthly_income: float = Field(..., description="Gross or net monthly income")
    fixed_expenses: float = Field(..., description="Fixed expenses (Rent, Utilities, Insurance, EMIs)")
    variable_expenses: float = Field(..., description="Variable expenses (Dining, Shopping, Entertainment)")
    existing_savings: float = Field(default=0.0, description="Current total liquid savings")
    emergency_fund: float = Field(default=0.0, description="Current liquid emergency fund balance")
    risk_tolerance: str = Field(default="moderate", description="conservative, moderate, aggressive")
    currency: str = Field(default="₹", description="Currency symbol e.g. ₹, $, €")
    goals: List[FinancialGoal] = Field(default_factory=list)
    debts: List[DebtItem] = Field(default_factory=list)
    transactions: Optional[List[TransactionItem]] = Field(default_factory=list)
