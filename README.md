# StudyRAG — Question-Answering & Test Generation from your own PDFs

StudyRAG turns your study material into practice tests. Upload PDFs, the app indexes
them with a Retrieval-Augmented-Generation (RAG) pipeline, then generates **source-grounded**
multiple-choice and descriptive questions, lets you take timed tests, and grades them —
multiple-choice deterministically and descriptive answers point-by-point with an LLM.

Every user has their own private library, vector index, questions, and test history.

> Originally forked from a Streamlit RAG demo; rebuilt as a FastAPI backend + React frontend
> with accounts, per-user isolation, local embeddings, and encryption at rest.

---

## Features

- **Accounts** — sign up / log in with email + password (hashed, never stored in plaintext).
- **Per-user isolation** — each user's PDFs, FAISS index, questions, and tests are separate.
- **Document upload** — 1–5 PDFs per upload, type/size/readability validated, re-uploads auto-renamed.
- **Encryption at rest** — uploaded PDFs are encrypted on disk (AES via Fernet); decrypted only in memory during ingestion.
- **Whole-document ingestion** — no page cap; chunked with source file + page metadata; FAISS index persists to disk and is rebuilt only on change.
- **Local embeddings** — `BAAI/bge-small-en-v1.5` via sentence-transformers (no embedding API, no rate limits, no cost).
- **Question generation** — grounded MCQs (4 options, single answer, source ref) and descriptive questions with a point-wise rubric.
- **Tests** — assemble a test from your questions, take it with autosave, submit, and get a scored evaluation.
- **Scoring** — MCQ is deterministic (1/0); descriptive is 1 mark per rubric point covered (LLM-judged).
- **Results** — total + section scores, per-question review, per-point descriptive feedback, source references; export to PDF.
- **Admin panel** — password-gated CRUD over all data tables, plus a full reset. Locks itself when you leave the page.

---

## Tech stack

**Backend (Python)**
- FastAPI + Uvicorn
- LangChain (`langchain`, `langchain-community`, `langchain-core`, `langchain-text-splitters`, `langchain-groq`)
- LLM: Groq-hosted `openai/gpt-oss-120b`
- Embeddings: `BAAI/bge-small-en-v1.5` (sentence-transformers, local)
- Vector store: FAISS (`faiss-cpu`)
- PDF parsing: `pypdf`
- DB: SQLite via SQLAlchemy
- Security: stdlib PBKDF2 (passwords) + `cryptography` Fernet (file encryption)

**Frontend (JavaScript)**
- React + Vite
- React Router, plain `fetch`, React Context for the logged-in user
- Minimal hand-written CSS design system (no UI library)

---

## Project structure

```
.
├── backend/
│   ├── main.py            # FastAPI app, CORS, startup key validation, router wiring
│   ├── config.py          # env + model constants, paths, per-user paths, file-encryption key
│   ├── db.py              # SQLAlchemy models (8 tables) + lightweight migrations
│   ├── security.py        # password hashing (PBKDF2) + file encryption (Fernet)
│   ├── rag.py             # decrypt → chunk → embed → FAISS (per user); retrieve
│   ├── generate.py        # Groq LLM: MCQ / descriptive generation + descriptive grading
│   ├── scoring.py         # grading math (MCQ deterministic, descriptive per-point)
│   ├── routers/
│   │   ├── users.py       # signup, login, per-user test history
│   │   ├── documents.py   # upload, ingest (background), list, delete
│   │   ├── questions.py   # MCQ / descriptive generation
│   │   ├── tests.py       # create / fetch / attempt / submit / result
│   │   └── admin.py       # password-gated generic CRUD + reset
│   └── test_*.py          # runnable self-checks (no framework needed)
├── frontend/
│   ├── public/img/        # logo + UI image assets
│   └── src/
│       ├── App.jsx        # routing, nav, login gate, admin layout
│       ├── api.js         # API client
│       ├── user.jsx       # current-user React context (localStorage)
│       └── pages/         # Login, Dashboard, Documents, Generate, TestBuilder,
│                          # Attempt, Results, ResultsList, Database (admin)
├── Artifacts/             # per-user uploaded PDFs (encrypted) — gitignored
├── faiss_index/           # per-user vector indexes — gitignored
├── app.db                 # SQLite database — gitignored
├── secret.key             # file-encryption key — gitignored (back this up!)
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- A **Groq API key** (free): https://console.groq.com/keys

Embeddings run locally, so no Google/OpenAI key is needed.

---

## Setup

### 1. Backend

```bash
python -m venv venv
# Windows (Git Bash):
source venv/Scripts/activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

> First run downloads the `bge-small-en-v1.5` model (~130 MB) on the first ingest.

### 2. Environment

Create a `.env` file in the project root:

```dotenv
API_KEY=your_groq_api_key_here      # required (Groq)
ADMIN_PASSWORD=change-me            # optional, defaults to "admin123"
```

`API_KEY` is the only required secret. The file-encryption key is generated automatically
into `secret.key` on first use.

### 3. Frontend

```bash
cd frontend
npm install
```

---

## Running

Two terminals:

```bash
# Terminal 1 — backend (http://localhost:8000, docs at /docs)
uvicorn backend.main:app --port 8000

# Terminal 2 — frontend (http://localhost:5173)
cd frontend && npm run dev
```

Open **http://localhost:5173**.

> On Windows, `--reload` can leave orphaned processes holding the port; running without
> `--reload` is more reliable (restart manually after backend edits).

---

## Usage

1. **Sign up / log in** (email + password).
2. **Documents** — drop 1–5 PDFs, click **Upload**, then **Ingest into Vector Store**; wait for status `completed`.
3. **Generate** — request N MCQs and/or N descriptive questions; preview them with source references; export to PDF.
4. **Build Test** — choose how many MCQ / descriptive questions; a test is assembled from your questions.
5. **Take it** — radio buttons for MCQs, text areas for descriptive answers, autosaved as you go; submit.
6. **Results** — see total + section scores, correct answers, per-point descriptive feedback, and sources. The **Results** tab lists all past evaluations.
7. **Admin panel** — visit `/admin`, enter the admin password to browse/edit every table or reset everything.

---

## API overview

`http://localhost:8000` — interactive docs at `/docs`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness + config check |
| POST | `/users` | Sign up (name, email, password) |
| POST | `/users/login` | Log in (email, password) |
| GET | `/users/{id}/tests` | A user's tests + scores (dashboard) |
| POST | `/documents/upload` | Upload 1–5 PDFs (multipart, `user_id`) |
| POST | `/documents/ingest?user_id=` | Build the user's FAISS index (background) |
| GET | `/documents?user_id=` | List the user's documents + status |
| DELETE | `/documents/{id}` | Delete a document |
| POST | `/questions/mcq` | Generate MCQs `{count, user_id}` |
| POST | `/questions/descriptive` | Generate descriptive questions `{count, user_id}` |
| POST | `/tests` | Assemble a test `{mcq_count, descriptive_count, user_id}` |
| GET | `/tests/{id}` | Test questions (answers hidden) |
| POST | `/tests/{id}/attempt` | Autosave in-progress answers |
| POST | `/tests/{id}/submit` | Grade + persist |
| GET | `/tests/{id}/result` | Full evaluation |
| GET/POST/DELETE | `/admin/...` | Admin CRUD + `/admin/reset` (requires `X-Admin-Password` header) |

---

## Data model (SQLite)

`User`, `Document`, `Chunk`, `Question`, `Rubric`, `Test`, `Attempt`, `Evaluation`.

- `Document`, `Question`, `Test`, `Attempt` are scoped by `user_id`.
- Tests carry a per-user sequence number (`seq`) so each user's tests read 1, 2, 3…
- `Chunk`, `Rubric`, and `Evaluation` are auto-populated by the pipeline (ingest / generate / submit) and are also editable from the admin panel.

---

## Security notes

- **Passwords**: PBKDF2-HMAC-SHA256, per-user salt, 200k iterations. Never stored in plaintext.
- **Uploaded PDFs**: encrypted at rest with Fernet (authenticated AES). The key lives in `secret.key` (gitignored) — **back it up**; losing it makes stored PDFs unrecoverable.
- **Admin**: endpoints require the `X-Admin-Password` header; the panel re-locks every time you leave the page.
- **Known limitation**: there are no session tokens yet — data APIs trust the `user_id` sent by the client. This protects data *at rest* and gates login, but is not full multi-tenant API authorization. Add JWT/session tokens before exposing this beyond a trusted environment.

---

## Tests

Runnable self-checks (no test framework, no network):

```bash
python -m backend.test_security     # password hashing + file encryption
python -m backend.test_documents    # upload validation + per-user scoping
python -m backend.test_generate     # question parsing / validation / dedup
python -m backend.test_scoring      # grading math
python -m backend.test_admin        # admin auth + generic CRUD
```

---

## Deferred / possible next steps

- Session tokens (JWT) for real API authorization
- OCR for scanned/image-only PDFs (currently text PDFs only)
- Hosted vector store and teacher/admin cross-user views
- Incremental FAISS updates instead of full rebuild per ingest

---

