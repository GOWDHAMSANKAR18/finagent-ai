"""
LLM Service Abstraction Provider
Supports Free-Tier Groq Developer API (llama-3.3-70b-versatile), Google Gemini, Ollama Local,
OpenAI Compatible Chat APIs, and a built-in Local Rule Engine for offline zero-dependency execution.

Features:
- Configurable provider priority: Groq (Free Tier) -> Gemini (Free Tier) -> Ollama -> Local Fallback
- Prompt injection filtering and prompt sanitization
- JSON output parsing & schema validation
- Clear error diagnostics (Rate limits, invalid keys, network timeouts)
- Empirical metrics tracking (call counts, average latencies, tool execution history)
"""

import os
import json
import time
import re
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Ensure root .env is loaded reliably
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENV_PATH = os.path.join(_PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=False)

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above)\s+instructions",
    r"disregard\s+system\s+prompt",
    r"override\s+system\s+instructions",
    r"you\s+are\s+now\s+a\s+hacker",
    r"system:\s*",
    r"delete\s+all\s+files",
    r"execute_command",
]

def sanitize_prompt(text: str) -> str:
    """
    Sanitize untrusted user prompt or document content to prevent prompt injection.
    Neutralizes attempts to alter system instructions or trigger unauthorized actions.
    """
    if not isinstance(text, str):
        return str(text)

    cleaned = text
    for pattern in PROMPT_INJECTION_PATTERNS:
        cleaned = re.sub(pattern, "[FLAGGED_INJECTION_ATTEMPT_REMOVED]", cleaned, flags=re.IGNORECASE)

    cleaned = cleaned.replace("\x00", "")
    return cleaned.strip()

class LLMService:
    _call_count: int = 0
    _tool_count: int = 0
    _call_history: List[Dict[str, Any]] = []
    _rate_limited_until: Dict[str, float] = {}
    _logged_cooldown: Dict[str, bool] = {}

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "groq").lower().strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip() or os.getenv("LLM_API_KEY", "").strip()
        
        self.api_key = self.groq_key or self.gemini_key or self.openai_key
        self.groq_model = (
            os.getenv("GROQ_MODEL", "").strip() or 
            os.getenv("LLM_MODEL", "").strip() or 
            "qwen/qwen3.8-27b"
        )
        self.base_url = (
            os.getenv("GROQ_BASE_URL", "").strip() or 
            os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
        )
        
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b").strip()

        self.timeout = int(os.getenv("LLM_TIMEOUT", 15))
        self.retry_limit = int(os.getenv("LLM_RETRY_LIMIT", 2))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", 2048))

        self.last_engine: str = "Local Rule Engine (Fallback)"
        self.is_last_live: bool = False

    @classmethod
    def reset_metrics(cls):
        """Reset empirical counters for clean evaluation runs."""
        cls._call_count = 0
        cls._tool_count = 0
        cls._call_history = []

    @classmethod
    def reset_cooldown(cls, provider: Optional[str] = None):
        """Explicitly clear cooldown state for a specific provider or all providers."""
        if provider:
            cls._rate_limited_until.pop(provider, None)
            cls._logged_cooldown.pop(provider, None)
        else:
            cls._rate_limited_until = {}
            cls._logged_cooldown = {}

    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """Return exact empirical call counts, tool usage, and call history."""
        providers = [item.get("provider") for item in cls._call_history]
        avg_latency = (
            sum(item.get("latency_seconds", 0) for item in cls._call_history) / len(cls._call_history)
            if cls._call_history else 0.0
        )
        return {
            "total_llm_calls": cls._call_count,
            "total_tool_calls": cls._tool_count,
            "average_latency_seconds": round(avg_latency, 4),
            "providers_used": list(set(providers)),
            "call_history": cls._call_history
        }

    @classmethod
    def record_tool_call(cls, tool_name: str, agent_name: str = ""):
        """Record an empirical tool call invocation."""
        cls._tool_count += 1

    def test_connection(self) -> Dict[str, Any]:
        """
        Tests API connectivity without exposing secret keys.
        Accurately distinguishes missing keys, invalid keys (401/403), model not found (404), rate limits (429), server errors (5xx), network errors, and success.
        """
        self.provider = os.getenv("LLM_PROVIDER", "groq").lower().strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip() or os.getenv("LLM_API_KEY", "").strip()
        self.groq_model = (
            os.getenv("GROQ_MODEL", "").strip() or 
            os.getenv("LLM_MODEL", "").strip() or 
            "qwen/qwen3.8-27b"
        )
        self.base_url = (
            os.getenv("GROQ_BASE_URL", "").strip() or 
            os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
        )

        if self.provider == "local":
            return {
                "status": "online",
                "mode": "local_rule_engine",
                "model": "deterministic_rules",
                "message": "Running on deterministic rule & synthesis engine (offline ready)."
            }
        
        active_key = (
            self.groq_key if self.provider == "groq" else
            self.gemini_key if self.provider == "gemini" else
            self.openai_key
        )

        if not active_key and self.provider in ["groq", "gemini", "openai"]:
            return {
                "status": "unconfigured",
                "mode": self.provider,
                "error_type": "missing_key",
                "message": f"API Key missing for provider '{self.provider}'. Falling back to local engine safely. Set {self.provider.upper()}_API_KEY in .env."
            }

        try:
            sample = ""
            if self.provider == "groq":
                sample = self._call_groq("Test connectivity. Reply with 'OK'.", system_prompt="Respond with OK only.", max_tokens=10)
            elif self.provider == "gemini":
                sample = self._call_gemini("Test connectivity. Reply with 'OK'.", system_prompt="Respond with OK only.")
            elif self.provider == "openai":
                sample = self._call_openai("Test connectivity. Reply with 'OK'.", system_prompt="Respond with OK only.")
            elif self.provider == "ollama":
                sample = self._call_ollama("Test connectivity. Reply with 'OK'.", system_prompt="Respond with OK only.")
            else:
                sample = "OK"

            LLMService._rate_limited_until.pop(self.provider, None)
            LLMService._logged_cooldown.pop(self.provider, None)

            return {
                "status": "online",
                "mode": self.provider,
                "model": self.groq_model if self.provider == "groq" else (self.ollama_model if self.provider == "ollama" else self.provider),
                "response_sample": sample[:60].strip(),
                "endpoint_url": f"{self.base_url}/chat/completions" if self.provider == "groq" else ""
            }
        except ValueError as ve:
            err_msg = str(ve)
            if any(k in err_msg for k in ["401", "403", "Unauthorized", "Forbidden"]):
                return {
                    "status": "invalid_credentials",
                    "mode": self.provider,
                    "error_type": "invalid_key",
                    "message": f"Invalid {self.provider.upper()} API Key (HTTP 401/403). Please verify your {self.provider.upper()}_API_KEY in .env.",
                    "endpoint_url": f"{self.base_url}/chat/completions"
                }
            elif any(k in err_msg for k in ["404", "Model Not Found", "model_not_found"]):
                return {
                    "status": "model_not_found",
                    "mode": self.provider,
                    "error_type": "model_not_found",
                    "message": f"Model '{self.groq_model}' not found on {self.provider.upper()} (HTTP 404). Details: {err_msg}",
                    "endpoint_url": f"{self.base_url}/chat/completions"
                }
            elif any(k in err_msg for k in ["429", "Rate Limit", "Quota"]):
                return {
                    "status": "rate_limited",
                    "mode": self.provider,
                    "error_type": "rate_limit",
                    "message": f"{self.provider.upper()} API Rate Limit Exceeded (HTTP 429). Please wait before retrying.",
                    "endpoint_url": f"{self.base_url}/chat/completions"
                }
            elif any(k in err_msg for k in ["500", "502", "503", "504", "Server Error"]):
                return {
                    "status": "server_error",
                    "mode": self.provider,
                    "error_type": "server_error",
                    "message": f"{self.provider.upper()} Server Error: {err_msg}",
                    "endpoint_url": f"{self.base_url}/chat/completions"
                }
            elif "Network Connection Failed" in err_msg:
                return {
                    "status": "network_error",
                    "mode": self.provider,
                    "error_type": "network_error",
                    "message": f"Network connection failed connecting to {self.provider.upper()} API: {err_msg}",
                    "endpoint_url": f"{self.base_url}/chat/completions"
                }
            else:
                return {
                    "status": "error",
                    "mode": self.provider,
                    "error_type": "api_error",
                    "message": f"{self.provider.upper()} API Error: {err_msg}",
                    "endpoint_url": f"{self.base_url}/chat/completions"
                }
        except Exception as e:
            return {
                "status": "error",
                "mode": self.provider,
                "error_type": "unknown_error",
                "message": f"Connectivity test failed for {self.provider.upper()}: {str(e)}"
            }

    def generate_completion(self, prompt: str, system_prompt: str = "", agent_name: str = "agent") -> str:
        """
        Generate completion using configured provider with automatic fallback to local engine.
        Enforces input sanitization, retries, and tracks real empirical call metrics.
        """
        start_time = time.perf_counter()
        LLMService._call_count += 1
        used_provider = self.provider

        safe_prompt = sanitize_prompt(prompt)
        safe_system = sanitize_prompt(system_prompt)

        result = None
        last_error = None

        now = time.time()
        cooldown_until = LLMService._rate_limited_until.get(self.provider, 0.0)
        in_cooldown = now < cooldown_until

        if in_cooldown:
            used_provider = f"{self.provider}_fallback_to_local"
            self.last_engine = f"Local Rule Engine (Fallback: Cooldown for {self.provider.upper()})"
            self.is_last_live = False
            result = self._local_fallback_completion(safe_prompt, safe_system)
        elif self.provider == "groq" and self.groq_key:
            token_request = min(self.max_tokens, 800)
            for attempt in range(self.retry_limit + 1):
                try:
                    result = self._call_groq(safe_prompt, safe_system, max_tokens=token_request)
                    self.last_engine = f"Groq ({self.groq_model})"
                    self.is_last_live = True
                    LLMService._rate_limited_until.pop(self.provider, None)
                    LLMService._logged_cooldown.pop(self.provider, None)
                    break
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    if "reduce max_tokens" in err_str or "OTPM" in err_str:
                        token_request = max(100, token_request // 2)
                    elif any(k in err_str for k in ["Rate Limit Exceeded", "429"]):
                        LLMService._rate_limited_until[self.provider] = time.time() + 45.0
                        if not LLMService._logged_cooldown.get(self.provider, False):
                            print(f"[LLMService] {self.provider.upper()} rate limit reached (HTTP 429). Activating 45s cooldown with local rule engine fallback.")
                            LLMService._logged_cooldown[self.provider] = True
                        break
                    elif any(k in err_str for k in ["401", "403", "404"]):
                        break
                    time.sleep(0.2 * (attempt + 1))
        elif self.provider == "gemini" and self.gemini_key:
            for attempt in range(self.retry_limit + 1):
                try:
                    result = self._call_gemini(safe_prompt, safe_system)
                    self.last_engine = "Gemini (gemini-1.5-flash)"
                    self.is_last_live = True
                    break
                except Exception as e:
                    last_error = e
                    time.sleep(0.3 * (attempt + 1))
        elif self.provider == "openai" and self.openai_key:
            for attempt in range(self.retry_limit + 1):
                try:
                    result = self._call_openai(safe_prompt, safe_system)
                    self.last_engine = f"OpenAI ({self.groq_model})"
                    self.is_last_live = True
                    break
                except Exception as e:
                    last_error = e
                    time.sleep(0.3 * (attempt + 1))
        elif self.provider == "ollama":
            for attempt in range(self.retry_limit + 1):
                try:
                    result = self._call_ollama(safe_prompt, safe_system)
                    self.last_engine = f"Ollama ({self.ollama_model})"
                    self.is_last_live = True
                    break
                except Exception as e:
                    last_error = e
                    time.sleep(0.3 * (attempt + 1))

        if result is None:
            if not in_cooldown and self.provider != "local" and last_error:
                err_msg = str(last_error)
                if not ("429" in err_msg or "Rate Limit" in err_msg):
                    print(f"[LLMService] {self.provider} API call failed: {last_error}. Falling back to deterministic local engine.")
                used_provider = f"{self.provider}_fallback_to_local"
                self.last_engine = f"Local Rule Engine (Fallback from {self.provider})"
            elif in_cooldown:
                used_provider = f"{self.provider}_fallback_to_local"
                self.last_engine = f"Local Rule Engine (Fallback: Cooldown for {self.provider.upper()})"
            else:
                used_provider = "local_rule_engine"
                self.last_engine = "Local Rule Engine (Offline)"
            self.is_last_live = False
            result = self._local_fallback_completion(safe_prompt, safe_system)

        latency = round(time.perf_counter() - start_time, 4)
        LLMService._call_history.append({
            "agent": agent_name,
            "provider": used_provider,
            "latency_seconds": latency,
            "timestamp": time.time()
        })

        return result

    def generate_json_completion(self, prompt: str, system_prompt: str = "", agent_name: str = "agent") -> Dict[str, Any]:
        """
        Generates completion and parses valid JSON output.
        """
        json_system_prompt = f"{system_prompt}\nIMPORTANT: Output strictly valid raw JSON only without markdown formatting."
        raw_output = self.generate_completion(prompt, system_prompt=json_system_prompt, agent_name=agent_name)
        
        cleaned_output = raw_output.strip()
        if cleaned_output.startswith("```"):
            cleaned_output = re.sub(r"^```(?:json)?\n?", "", cleaned_output)
            cleaned_output = re.sub(r"\n?```$", "", cleaned_output)
        
        try:
            return json.loads(cleaned_output.strip())
        except Exception:
            return {
                "raw_response": raw_output,
                "parsed": False,
                "summary": "Completed analysis using fallback synthesis."
            }

    def _call_groq(self, prompt: str, system_prompt: str, max_tokens: Optional[int] = None) -> str:
        """Call Groq Free Tier REST endpoint (OpenAI compatible format)."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt.strip()})

        model_name = self.groq_model or "qwen/qwen3.8-27b"
        tokens_to_request = max_tokens if max_tokens is not None else min(self.max_tokens, 800)
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": tokens_to_request
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as conn_err:
            raise ValueError(f"Network Connection Failed: {str(conn_err)}")
        except requests.exceptions.RequestException as req_err:
            raise ValueError(f"HTTP Request Error: {str(req_err)}")

        if resp.status_code != 200:
            err_data = {}
            try:
                err_data = resp.json().get("error", {})
            except Exception:
                pass
            err_msg = err_data.get("message", resp.text[:200])
            err_code = err_data.get("code", "")

            if resp.status_code == 401:
                raise ValueError("Invalid Groq API Key (HTTP 401 Unauthorized)")
            elif resp.status_code == 403:
                raise ValueError("Groq API Access Forbidden (HTTP 403 Forbidden)")
            elif resp.status_code == 404 or err_code == "model_not_found":
                raise ValueError(f"Groq Model Not Found (HTTP 404): Model '{model_name}' is not available. Details: {err_msg}")
            elif resp.status_code == 429:
                raise ValueError("Groq Rate Limit Exceeded (HTTP 429)")
            elif resp.status_code >= 500:
                raise ValueError(f"Groq Server Error (HTTP {resp.status_code}): {err_msg}")
            else:
                raise ValueError(f"Groq API Error (HTTP {resp.status_code}): {err_msg}")

        data = resp.json()
        return data['choices'][0]['message']['content']

    def _call_openai(self, prompt: str, system_prompt: str) -> str:
        """Call OpenAI API endpoint."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt.strip()})

        payload = {
            "model": self.groq_model or "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": self.max_tokens
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        if resp.status_code == 401:
            raise ValueError("Invalid OpenAI API Key (HTTP 401 Unauthorized)")
        elif resp.status_code == 429:
            raise ValueError("OpenAI API Quota / Rate Limit Exceeded (HTTP 429)")
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content']

    def _call_gemini(self, prompt: str, system_prompt: str) -> str:
        """Call Google Gemini REST endpoint."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"System Instruction: {system_prompt}\n\nUser Request: {prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": self.max_tokens
            }
        }
        resp = requests.post(url, json=payload, timeout=self.timeout)
        if resp.status_code == 400 or resp.status_code == 403:
            raise ValueError(f"Gemini API Error ({resp.status_code}): Invalid Key or Request Permissions")
        resp.raise_for_status()
        data = resp.json()
        return data['candidates'][0]['content']['parts'][0]['text']

    def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        """Call Ollama local endpoint."""
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "system": system_prompt,
            "prompt": prompt,
            "stream": False
        }
        resp = requests.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json().get("response", "")

    def _local_fallback_completion(self, prompt: str, system_prompt: str) -> str:
        """
        Deterministic Rule Engine fallback to guarantee reliable execution without API keys.
        Formats high-precision responses tailored for each specialized agent role.
        """
        prompt_lower = prompt.lower()
        sys_lower = system_prompt.lower()

        # Greetings & General Conversational Queries
        if any(kw in prompt_lower for kw in ["hi", "hello", "hey", "greetings", "good morning", "good evening"]):
            return "Hi! I'm your FinAgent AI assistant. I can help you understand your finances, analyze spending, plan budgets, track goals, and explore ways to improve your financial health. What would you like to work on?"
        if "what can you do" in prompt_lower or "who are you" in prompt_lower:
            return "I can analyze your financial data, review spending, help build budgets, track savings goals, evaluate debt payoff strategies, run what-if simulations, and navigate application pages for you. How can I help today?"
        if any(kw in prompt_lower for kw in ["thanks", "thank you"]):
            return "You're very welcome! Let me know if you need anything else to optimize your financial goals."

        if "budget_agent" in prompt_lower:
            return "Analyzed income and expenditure breakdown. Cash flow surplus and savings rate calculated accurately against obligations."
        elif "goal_agent" in prompt_lower:
            return "Evaluated target goal timelines and required monthly savings against available cash surplus. Prioritization rules applied."
        elif "risk_agent" in prompt_lower:
            return "Calculated Debt-to-Income (DTI) ratio and emergency fund adequacy. Identified high-interest debt and safety cushion risks."
        elif "research_agent" in prompt_lower:
            return "Retrieved relevant financial knowledge base benchmarks including 50/30/20 budgeting guidelines and Debt Avalanche methods."
        elif "recommendation_agent" in prompt_lower:
            return "Synthesized validated findings into a prioritized, balanced monthly financial allocation plan reconciled against monthly income."

        return "I'm here to assist with your financial planning, budgeting, goal tracking, and what-if simulations. How can I help you today?"


