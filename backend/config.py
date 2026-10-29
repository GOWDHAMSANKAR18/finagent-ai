import os
from dotenv import load_dotenv

# Ensure the root .env file is explicitly loaded
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=ENV_PATH, override=True)

class Config:
    PROJECT_NAME: str = "FinAgent AI | Dark Knight Multi-Agent Financial Intelligence Platform"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))
    
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").lower().strip()
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "").strip() or os.getenv("LLM_MODEL", "qwen/qwen3.8-27b").strip()
    LLM_MODEL: str = GROQ_MODEL

