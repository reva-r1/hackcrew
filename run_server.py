import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import src.config
from src.app import app
import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 60, flush=True)
    print("🚀 Enterprise RAG Backend Server Started!", flush=True)
    print("👉 API URL:      http://127.0.0.1:8000", flush=True)
    print("👉 Swagger Docs: http://127.0.0.1:8000/docs", flush=True)
    print("👉 Health Check: http://127.0.0.1:8000/health", flush=True)
    print("=" * 60 + "\n", flush=True)
    
    # Running app directly avoids Windows reload multiprocessing spawn stalls
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
