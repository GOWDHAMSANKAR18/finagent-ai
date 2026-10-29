import os
import pytest
from unittest.mock import patch, MagicMock
from backend.services.llm_service import LLMService
from backend.services.chat_assistant import ChatAssistant

def test_groq_missing_key(monkeypatch):
    """Test behavior when GROQ_API_KEY is missing or empty."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "")
    
    llm = LLMService()
    conn = llm.test_connection()
    
    assert conn["status"] == "unconfigured"
    assert conn["error_type"] == "missing_key"
    assert "missing" in conn["message"].lower()

    # Test fallback completion
    res = llm.generate_completion("Hello test", system_prompt="Test system")
    assert res is not None
    assert len(res) > 0
    assert llm.is_last_live is False
    assert "Local Rule Engine" in llm.last_engine

def test_groq_valid_configuration(monkeypatch):
    """Test valid Groq configuration and successful mock API call."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_valid_mock_key")
    monkeypatch.setenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    
    llm = LLMService()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "OK - Groq LLM Connected Successfully"
                }
            }
        ]
    }
    
    with patch("requests.post", return_value=mock_response) as mock_post:
        conn = llm.test_connection()
        
        assert conn["status"] == "online"
        assert conn["mode"] == "groq"
        assert conn["model"] == "qwen/qwen3.8-27b"
        assert "OK" in conn["response_sample"]
        
        # Verify request structure
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer gsk_test_valid_mock_key"
        assert kwargs["json"]["model"] == "qwen/qwen3.8-27b"
        assert args[0] == "https://api.groq.com/openai/v1/chat/completions"

def test_groq_invalid_credentials_401(monkeypatch):
    """Test Groq provider response when API key is rejected (HTTP 401)."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_invalid_key_999")
    
    llm = LLMService()
    
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": {"message": "Invalid API key provided", "type": "invalid_request_error"}}
    
    with patch("requests.post", return_value=mock_response):
        conn = llm.test_connection()
        assert conn["status"] == "invalid_credentials"
        assert conn["error_type"] == "invalid_key"
        
        # Verify generate_completion falls back safely
        res = llm.generate_completion("Test prompt")
        assert llm.is_last_live is False
        assert "Fallback" in llm.last_engine
        assert len(res) > 0

def test_groq_model_not_found_404(monkeypatch):
    """Test Groq provider response when model ID is invalid or deprecated (HTTP 404)."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key")
    monkeypatch.setenv("GROQ_MODEL", "nonexistent-model-xyz")
    
    llm = LLMService()
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {
        "error": {
            "message": "The model `nonexistent-model-xyz` does not exist",
            "type": "invalid_request_error",
            "code": "model_not_found"
        }
    }
    
    with patch("requests.post", return_value=mock_response):
        conn = llm.test_connection()
        assert conn["status"] == "model_not_found"
        assert conn["error_type"] == "model_not_found"
        assert "nonexistent-model-xyz" in conn["message"]

def test_groq_rate_limit_429(monkeypatch):
    """Test Groq provider handling when rate limits are exceeded (HTTP 429)."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key")
    
    llm = LLMService()
    
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.json.return_value = {"error": {"message": "Rate limit reached", "type": "tokens_exceeded"}}
    
    with patch("requests.post", return_value=mock_response):
        conn = llm.test_connection()
        assert conn["status"] == "rate_limited"
        assert conn["error_type"] == "rate_limit"

def test_groq_server_error_500(monkeypatch):
    """Test Groq provider handling when server error occurs (HTTP 500)."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key")
    
    llm = LLMService()
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": {"message": "Internal server error"}}
    
    with patch("requests.post", return_value=mock_response):
        conn = llm.test_connection()
        assert conn["status"] == "server_error"
        assert conn["error_type"] == "server_error"

def test_groq_network_error(monkeypatch):
    """Test Groq provider handling during network connection failure (Timeout / Connection Error)."""
    import requests
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key")
    
    llm = LLMService()
    
    with patch("requests.post", side_effect=requests.exceptions.ConnectionError("DNS resolution failed")):
        conn = llm.test_connection()
        assert conn["status"] == "network_error"
        assert conn["error_type"] == "network_error"

def test_chat_assistant_engine_metadata(monkeypatch):
    """Test ChatAssistant output metadata contains active engine and live status."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "")
    
    chat = ChatAssistant()
    res = chat.process_message("Hello FinAgent")
    
    assert "explainability" in res
    assert "active_engine" in res["explainability"]
    assert "is_live_llm" in res["explainability"]
    assert res["explainability"]["is_live_llm"] is False
