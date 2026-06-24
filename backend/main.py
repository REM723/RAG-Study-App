import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .db import init_db
from .routers import admin, documents, questions, tests, users

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rag")


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.validate_keys()  # fix #1: fail at startup, not mid-request
    config.ARTIFACTS_DIR.mkdir(exist_ok=True)
    init_db()
    log.info("Config OK: model=%s artifacts=%s", config.MODEL_ID, config.ARTIFACTS_DIR)
    yield


app = FastAPI(title="RAG Study App", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(questions.router)
app.include_router(tests.router)
app.include_router(admin.router)
app.include_router(users.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "keys_configured": bool(config.GROQ_API_KEY and config.GOOGLE_API_KEY),
        "model": config.MODEL_ID,
    }
