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

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "Artifacts"
FAISS_DIR = BASE_DIR / "faiss_index"
DB_PATH = BASE_DIR / "app.db"


def validate_keys():
    """Raise loudly at startup if the Groq key is missing (fix #1).
    Embeddings are local now, so GOOGLE_API_KEY is no longer required."""
    if not GROQ_API_KEY:
        raise RuntimeError("Missing required env var API_KEY (Groq). Set it in .env")
