import os
import io
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.config import Config
from backend.models.user_profile import UserProfile
from backend.agents.orchestrator import MultiAgentOrchestrator
from backend.tools.transaction_analyzer import analyze_transaction_list
from backend.tools.knowledge_retriever import KnowledgeRetriever
from backend.tools.simulation_engine import run_what_if_simulation, compare_debt_payoff_strategies
from backend.tools.report_generator import generate_text_report
from backend.tools.external_financial_data import get_currency_exchange_rates, get_market_benchmarks
from backend.services.llm_service import LLMService, sanitize_prompt
from evaluation.multi_agent_evaluation import run_benchmark_evaluation

app = FastAPI(
    title=Config.PROJECT_NAME,
    version=Config.VERSION,
    description="Professional Multi-Agent AI Platform for Personal Finance & Financial Intelligence"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = MultiAgentOrchestrator()
knowledge_retriever = KnowledgeRetriever()
llm_service = LLMService()

MAX_CSV_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit

_last_health_conn = {"time": 0.0, "result": None}

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint returning system status, agent status, knowledge base readiness, and LLM provider.
    """
    kb_ready = len(knowledge_retriever.knowledge_base) > 0
    now = time.time()
    if now - _last_health_conn["time"] < 60.0 and _last_health_conn["result"] is not None:
        conn_status = _last_health_conn["result"]
    else:
        conn_status = llm_service.test_connection()
        _last_health_conn["time"] = now
        _last_health_conn["result"] = conn_status

    return {
        "status": "ok",
        "service": "FinAgent AI",
        "backend": True,
        "knowledge_base": kb_ready,
        "llm_provider": Config.LLM_PROVIDER,
        "llm_connection": conn_status,
        "version": Config.VERSION,
        "agents": {
            "budget_agent": "ready",
            "goal_agent": "ready",
            "debt_risk_agent": "ready",
            "research_agent": "ready",
            "recommendation_agent": "ready"
        }
    }

@app.get("/api/settings/connectivity-test")
async def test_llm_connectivity():
    """
    Endpoint for frontend settings page to perform live LLM API connectivity tests.
    """
    res = llm_service.test_connection()
    return res

@app.get("/api/external-data/rates")
async def fetch_exchange_rates(base: str = "INR"):
    """
    Endpoint for live FX rates and market benchmark indicators.
    """
    rates = get_currency_exchange_rates(base_currency=base)
    benchmarks = get_market_benchmarks()
    return {
        "status": "success",
        "exchange_rates": rates,
        "market_benchmarks": benchmarks
    }

@app.post("/api/analyze")
async def analyze_financial_profile(profile: UserProfile, task_intent: str = "full_plan"):
    """
    Main endpoint: Executes multi-agent pipeline and returns synthesized plan with agent logs.
    """
    try:
        start_time = time.time()
        shared_context = orchestrator.run_pipeline(
            profile.model_dump(),
            parallel_mode=False,
            enable_feedback=True,
            task_intent=task_intent
        )
        execution_time = round(time.time() - start_time, 3)

        return {
            "status": "success",
            "execution_time_seconds": execution_time,
            "final_plan": shared_context.final_plan,
            "agent_messages": [msg.model_dump() for msg in shared_context.messages],
            "agent_states": {name: state.model_dump() for name, state in shared_context.agent_states.items()},
            "budget_analysis": shared_context.budget_analysis,
            "goal_analysis": shared_context.goal_analysis,
            "debt_risk_analysis": shared_context.debt_risk_analysis,
            "research_results": shared_context.research_results,
            "validation_results": shared_context.validation_results,
            "health_score": shared_context.health_score,
            "subscriptions": shared_context.subscriptions,
            "debt_strategies": shared_context.debt_strategies,
            "alerts": shared_context.alerts,
            "delegation_history": shared_context.delegation_history,
            "tool_calls": shared_context.tool_calls
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-Agent pipeline execution error: {str(e)}")

@app.post("/api/baseline")
async def single_agent_baseline(profile: UserProfile):
    """
    Runs single-agent monolithic baseline for comparative evaluation.
    """
    try:
        start_time = time.time()
        result = orchestrator.run_single_agent_baseline(profile.model_dump())
        result["execution_time_seconds"] = round(time.time() - start_time, 3)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Baseline execution error: {str(e)}")

@app.post("/api/simulate")
async def simulate_what_if_scenario(payload: dict = Body(...)):
    """
    Runs a What-If scenario simulation modifying income, expenses, or savings delta.
    """
    try:
        profile = payload.get("profile", {})
        modifications = payload.get("modifications", {})
        sim_result = run_what_if_simulation(profile, modifications)
        return {"status": "success", "simulation": sim_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@app.post("/api/debt-strategies")
async def debt_strategy_comparison(payload: dict = Body(...)):
    """
    Compares Debt Avalanche vs Debt Snowball vs Minimum Payments.
    """
    try:
        debts = payload.get("debts", [])
        extra_alloc = float(payload.get("extra_monthly_allocation", 0.0))
        result = compare_debt_payoff_strategies(debts, extra_alloc)
        return {"status": "success", "comparison": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debt strategy comparison failed: {str(e)}")

@app.post("/api/generate-report")
async def generate_report(payload: dict = Body(...)):
    """
    Generates downloadable plain text/markdown report.
    """
    try:
        final_plan = payload.get("final_plan", {})
        report_text = generate_text_report(final_plan)
        return PlainTextResponse(report_text, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

from backend.services.chat_assistant import ChatAssistant

chat_assistant = ChatAssistant()

@app.post("/api/chat")
async def ai_assistant_chat(payload: dict = Body(...)):
    """
    Interactive AI Financial Chat querying the conversational assistant engine.
    Supports natural conversation, intent routing, tool calling, and UI action execution.
    """
    try:
        raw_query = payload.get("query", "")
        profile_data = payload.get("profile", {})
        session_id = payload.get("session_id", "default_session")

        response = chat_assistant.process_message(
            query=raw_query,
            profile_data=profile_data,
            session_id=session_id
        )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat assistant error: {str(e)}")

@app.post("/api/chat/clear")
async def clear_chat_history(payload: dict = Body(...)):
    """
    Clear session chat history.
    """
    session_id = payload.get("session_id", "default_session")
    ChatAssistant.clear_session_history(session_id)
    return {"status": "success", "message": f"Chat history for session '{session_id}' cleared."}

@app.post("/api/evaluate")
async def evaluate_systems():
    """
    Runs automated comparative benchmark evaluation comparing Single-Agent vs Multi-Agent.
    """
    try:
        results = run_benchmark_evaluation()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.post("/api/upload-csv")
async def upload_transaction_csv(file: UploadFile = File(...)):
    """
    Upload and analyze transaction CSV file with size validation and safe Pandas parsing.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    try:
        content = await file.read()
        if len(content) > MAX_CSV_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="CSV file exceeds maximum allowed size limit of 5MB.")

        import pandas as pd
        df = pd.read_csv(io.BytesIO(content))
        analysis = analyze_transaction_list(df.to_dict(orient='records'))
        return {
            "filename": file.filename,
            "analysis": analysis,
            "raw_transactions": df.to_dict(orient='records')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV processing failed: {str(e)}")

@app.get("/api/knowledge")
async def query_knowledge_base(q: str = ""):
    """
    Query educational financial knowledge base.
    """
    results = knowledge_retriever.query(q, top_k=5)
    return {"query": q, "results": results}

# Serve Frontend static assets
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(
            os.path.join(frontend_dir, "index.html"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )
