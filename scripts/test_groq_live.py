"""
FinAgent AI — Groq Live Connectivity Diagnostic Tool
Runs a live, secure connectivity diagnostic using your configured .env key.
Does NOT expose or log secret API keys or headers.
"""

import sys
import os

# Ensure UTF-8 output encoding for console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from backend.services.llm_service import LLMService

def run_diagnostic():
    print("=" * 70)
    print("      FINAGENT AI | GROQ LIVE API CONNECTIVITY DIAGNOSTIC")
    print("=" * 70)
    
    provider = os.getenv("LLM_PROVIDER", "groq").lower().strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    model_name = os.getenv("GROQ_MODEL", "").strip() or os.getenv("LLM_MODEL", "qwen/qwen3.8-27b").strip()
    
    print(f"Loaded Provider     : {provider}")
    print(f"Configured Model    : {model_name}")
    print(f"API Key Present     : {'Yes (Length: ' + str(len(groq_key)) + ')' if groq_key else 'No (MISSING)'}")
    print(f"Target Endpoint URL : https://api.groq.com/openai/v1/chat/completions")
    print("-" * 70)

    llm = LLMService()
    print("Executing Live API Connection Test...")
    res = llm.test_connection()
    
    print("\n--- Diagnostic Results ---")
    print(f"Status           : {res.get('status', 'unknown').upper()}")
    print(f"Mode             : {res.get('mode', 'N/A')}")
    print(f"Model            : {res.get('model', 'N/A')}")
    if "error_type" in res:
        print(f"Error Type       : {res.get('error_type')}")
    if "message" in res:
        print(f"Details          : {res.get('message')}")
    if "response_sample" in res:
        print(f"Sample Output    : \"{res.get('response_sample')}\"")
    print("=" * 70)

    if res.get("status") == "online":
        print("\nSUCCESS: Groq API integration is fully operational and responsive!")
    else:
        print(f"\nACTION REQUIRED: Please resolve the issue described in Details above.")

if __name__ == "__main__":
    run_diagnostic()
