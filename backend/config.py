import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Single source of truth for models. 70b for question generation + rubric grading.
MODEL_ID = "llama-3.3-70b-versatile"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # local sentence-transformers, no API

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

MAX_FILES = 5
MAX_UPLOAD_MB = 25

# Admin panel password. Override in .env: ADMIN_PASSWORD=...
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "Artifacts"
FAISS_DIR = BASE_DIR / "faiss_index"
DB_PATH = BASE_DIR / "app.db"


def user_artifacts(user_id):
    """Per-user PDF folder, created on demand."""
    p = ARTIFACTS_DIR / str(user_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def user_index(user_id):
    """Per-user FAISS index directory."""
    return FAISS_DIR / str(user_id)


def validate_keys():
    """Raise loudly at startup if the Groq key is missing (fix #1).
    Embeddings are local now, so GOOGLE_API_KEY is no longer required."""
    if not GROQ_API_KEY:
        raise RuntimeError("Missing required env var API_KEY (Groq). Set it in .env")
