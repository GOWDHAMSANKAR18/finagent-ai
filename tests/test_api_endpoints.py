import pytest
import io
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["backend"] is True
    assert "agents" in data
    assert len(data["agents"]) == 5

def test_api_analyze_valid():
    payload = {
        "monthly_income": 60000,
        "fixed_expenses": 20000,
        "variable_expenses": 10000,
        "existing_savings": 50000,
        "emergency_fund": 30000,
        "risk_tolerance": "moderate",
        "goals": [{"name": "Laptop", "target_amount": 60000, "deadline_months": 6}],
        "debts": [{"name": "Personal Loan", "total_balance": 50000, "monthly_emi": 3000, "interest_rate_annual": 10.5}]
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "final_plan" in data
    assert "agent_states" in data
    assert len(data["agent_states"]) == 5

def test_api_analyze_empty_goals_debts():
    payload = {
        "monthly_income": 50000,
        "fixed_expenses": 20000,
        "variable_expenses": 10000,
        "existing_savings": 10000,
        "emergency_fund": 5000,
        "goals": [],
        "debts": []
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"

def test_api_baseline():
    payload = {
        "monthly_income": 50000,
        "fixed_expenses": 20000,
        "variable_expenses": 10000
    }
    resp = client.post("/api/baseline", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_type"] == "Single-Agent Monolithic Baseline"
    assert data["monthly_surplus"] == 20000.0

def test_api_simulate():
    payload = {
        "profile": {
            "monthly_income": 60000,
            "fixed_expenses": 20000,
            "variable_expenses": 15000
        },
        "modifications": {
            "income_delta": 5000,
            "extra_savings_monthly": 2000
        }
    }
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "simulation" in data

def test_api_debt_strategies():
    payload = {
        "debts": [
            {"name": "Credit Card", "total_balance": 100000, "monthly_emi": 10000, "interest_rate_annual": 24.0},
            {"name": "Car Loan", "total_balance": 200000, "monthly_emi": 8000, "interest_rate_annual": 11.0}
        ],
        "extra_monthly_allocation": 3000
    }
    resp = client.post("/api/debt-strategies", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "avalanche" in data["comparison"]["strategies"]
    assert "snowball" in data["comparison"]["strategies"]

def test_api_chat():
    payload = {
        "query": "How is my financial health score calculated?",
        "profile": {"monthly_income": 60000, "fixed_expenses": 20000, "variable_expenses": 10000}
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "explainability" in data

def test_api_upload_csv_valid():
    csv_content = "date,description,category,amount,type\n2026-09-01,Salary,Income,60000,income\n2026-09-02,Rent,Housing,15000,expense\n"
    file_bytes = io.BytesIO(csv_content.encode("utf-8"))
    resp = client.post(
        "/api/upload-csv",
        files={"file": ("transactions.csv", file_bytes, "text/csv")}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "transactions.csv"
    assert len(data["raw_transactions"]) == 2

def test_api_upload_csv_invalid_file_extension():
    txt_content = "some text file"
    file_bytes = io.BytesIO(txt_content.encode("utf-8"))
    resp = client.post(
        "/api/upload-csv",
        files={"file": ("data.txt", file_bytes, "text/plain")}
    )
    assert resp.status_code == 400

def test_api_generate_report():
    payload = {
        "final_plan": {
            "summary": {"health_score": 85, "health_rating": "Healthy", "monthly_income": 60000},
            "proposed_monthly_plan": [],
            "action_plan": ["Cut variable spending by 10%"]
        }
    }
    resp = client.post("/api/generate-report", json=payload)
    assert resp.status_code == 200
    assert "FinAgent" in resp.text or "FINANCIAL" in resp.text or "REPORT" in resp.text

def test_api_knowledge():
    resp = client.get("/api/knowledge?q=budget")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data

def test_api_evaluate():
    resp = client.post("/api/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert "evaluation_summary" in data
    assert "detailed_test_cases" in data

def test_root_index_serving():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "FINAGENT AI" in resp.text
    assert "Cache-Control" in resp.headers
