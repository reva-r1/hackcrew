import os
import sys
from pathlib import Path

# Configure BLAS / OpenMP threading to avoid Windows memory allocation issues with OpenBLAS
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
SQLITE_DB_PATH = DATA_DIR / "rag_storage.db"

# Ensure data directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Models
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# LLM Config (Groq)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
FAST_LLM_MODEL = "llama-3.1-8b-instant"
REASONING_LLM_MODEL = "llama-3.3-70b-versatile"

# RAG Hyperparameters
CHUNK_SIZE_TOKENS = 400  # Target 300-500 tokens
CHUNK_OVERLAP_TOKENS = 50
RRF_K = 60
TOP_K_HYBRID = 25
TOP_K_RERANK = 5

# Confidence threshold for refusal (calibrated empirically in Step 4)
CONFIDENCE_THRESHOLD = 0.40
