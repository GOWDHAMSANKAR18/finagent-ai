"""
FinAgent AI Platform Launcher
Starts the FastAPI application correctly from project root on 127.0.0.1:8000.
"""

import sys
import os
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def main():
    print("=" * 70)
    print("       FINAGENT AI | MULTI-AGENT FINANCIAL INTELLIGENCE PLATFORM")
    print("=" * 70)
    print(f"Project Root Directory : {PROJECT_ROOT}")
    print("Server URL             : http://127.0.0.1:8000")
    print("Swagger API Docs       : http://127.0.0.1:8000/docs")
    print("=" * 70)
    print("\nStarting Uvicorn Server...\n")

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=["backend", "frontend"])

if __name__ == "__main__":
    main()
