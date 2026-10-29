from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import time
import uuid

class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_id: str = Field(default_factory=lambda: f"task_{str(uuid.uuid4())[:6]}", description="Unique task session identifier")
    sender: str = Field(..., description="Agent name sending message e.g. budget_agent")
    receiver: str = Field(..., description="Agent name receiving message e.g. goal_agent, orchestrator")
    message_type: str = Field(..., description="e.g. financial_analysis, goal_feasibility, risk_assessment, final_recommendation")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured payload passed between agents")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0, description="Confidence score of analysis")
    status: str = Field(default="completed", description="Status of agent message execution e.g. completed, pending, delegated")
    timestamp: float = Field(default_factory=time.time)
    step_id: int = Field(default=1, description="Execution step sequence index")
    summary: str = Field(default="", description="Human-readable summary of findings sent in message")

    @property
    def payload(self) -> Dict[str, Any]:
        return self.data

class AgentTaskState(BaseModel):
    agent_name: str
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    output_summary: Optional[str] = None
    error: Optional[str] = None

class SharedContext(BaseModel):
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    transaction_analysis: Dict[str, Any] = Field(default_factory=dict)
    budget_analysis: Dict[str, Any] = Field(default_factory=dict)
    goal_analysis: Dict[str, Any] = Field(default_factory=dict)
    debt_risk_analysis: Dict[str, Any] = Field(default_factory=dict)
    research_results: Dict[str, Any] = Field(default_factory=dict)
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    final_plan: Dict[str, Any] = Field(default_factory=dict)
    health_score: Dict[str, Any] = Field(default_factory=dict)
    subscriptions: Dict[str, Any] = Field(default_factory=dict)
    debt_strategies: Dict[str, Any] = Field(default_factory=dict)
    simulations: Dict[str, Any] = Field(default_factory=dict)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    messages: List[AgentMessage] = Field(default_factory=list)
    agent_states: Dict[str, AgentTaskState] = Field(default_factory=dict)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    delegation_history: List[Dict[str, Any]] = Field(default_factory=list)
    conflict_history: List[Dict[str, Any]] = Field(default_factory=list)

