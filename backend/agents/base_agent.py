"""
Base Agent Abstract Implementation
Defines standard agent lifecycle, structured messaging protocols, tool execution,
and integration with shared context.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
import time
from backend.models.agent_messages import AgentMessage, AgentTaskState, SharedContext
from backend.services.llm_service import LLMService

class BaseAgent(ABC):
    def __init__(self, name: str, role: str, description: str):
        self.name = name
        self.role = role
        self.description = description
        self.llm_service = LLMService()

    @abstractmethod
    def execute(self, shared_context: SharedContext, input_message: Optional[AgentMessage] = None) -> AgentMessage:
        """
        Execute agent reasoning and tool calls, updating shared context.
        Must return a structured AgentMessage output.
        """
        pass

    def execute_tool(
        self,
        shared_context: SharedContext,
        tool_name: str,
        tool_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Executes a domain tool, logs execution to shared context, and tracks empirical tool metrics.
        """
        t0 = time.perf_counter()
        LLMService.record_tool_call(tool_name=tool_name, agent_name=self.name)
        result = tool_func(*args, **kwargs)
        elapsed = round(time.perf_counter() - t0, 4)

        shared_context.tool_calls.append({
            "agent": self.name,
            "tool_name": tool_name,
            "status": "success",
            "execution_time_seconds": elapsed,
            "timestamp": time.time()
        })
        return result

    def create_message(
        self,
        receiver: str,
        message_type: str,
        data: Dict[str, Any],
        summary: str,
        step_id: int = 1,
        confidence: float = 0.95,
        task_id: Optional[str] = None,
        status: str = "completed"
    ) -> AgentMessage:
        """Helper to create standardized inter-agent messages."""
        msg_kwargs = {
            "sender": self.name,
            "receiver": receiver,
            "message_type": message_type,
            "data": data,
            "confidence": confidence,
            "status": status,
            "step_id": step_id,
            "summary": summary,
            "timestamp": time.time()
        }
        if task_id:
            msg_kwargs["task_id"] = task_id
        return AgentMessage(**msg_kwargs)

    def log_state(self, shared_context: SharedContext, status: str, summary: str = "", error: str = None):
        """Update agent execution status in shared context tracking table."""
        state = AgentTaskState(
            agent_name=self.name,
            status=status,
            started_at=time.time() if status == "running" else None,
            completed_at=time.time() if status in ["completed", "failed"] else None,
            output_summary=summary,
            error=error
        )
        shared_context.agent_states[self.name] = state

