import logging
import shutil
from io import BytesIO

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LCDocument
from cryptography.fernet import InvalidToken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from . import config, security

log = logging.getLogger("rag")

_embeddings = None


def embeddings():
    global _embeddings
    if _embeddings is None:
        # bge wrapper sets normalize + the bge query instruction by default.
        # First use downloads the model (~130MB) from HuggingFace.
        _embeddings = HuggingFaceBgeEmbeddings(model_name=config.EMBED_MODEL)
    return _embeddings


def _load_chunks(user_id, only=None):
    """Load PDFs in the user's Artifacts folder, chunk with source/page/index metadata.

    only: optional set of filenames to restrict to (for per-document ingest).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP
    )
    chunks, per_file = [], {}
    for pdf in sorted(config.user_artifacts(user_id).glob("*.pdf")):
        if only is not None and pdf.name not in only:
            continue
        try:
            raw = pdf.read_bytes()
            try:
                data = security.decrypt_bytes(raw)
            except InvalidToken:
                data = raw  # legacy plaintext upload — migrate it to encrypted on disk
                pdf.write_bytes(security.encrypt_bytes(raw))
            # decrypt + parse in memory — no temp file (avoids Windows file locks)
            reader = PdfReader(BytesIO(data))
            pages = []
            for n, page in enumerate(reader.pages):   # n is 0-based, matches old loader
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(LCDocument(page_content=text, metadata={"page": n}))
        except Exception as e:
            log.warning("skip %s: %s", pdf.name, e)   # one bad file shouldn't fail the batch
            continue
        split = splitter.split_documents(pages)       # fix #2: no [:20] cap
        for i, d in enumerate(split):
            d.metadata["source_file"] = pdf.name
            d.metadata["chunk_index"] = i
            d.metadata["page"] = d.metadata.get("page", 0) + 1  # 1-based
        chunks.extend(split)
        per_file[pdf.name] = len(split)
    return chunks, per_file


def rebuild_index(user_id):
    """Rebuild this user's FAISS index from their PDFs, persist to disk (fix #2 + #3).

    Returns ({filename: chunk_count}, [chunk Documents]).
    """
    # ponytail: full rebuild on every ingest; switch to incremental .add if reindex hurts
    # ponytail: embeddings batch internally; add manual batching/retry if rate limits bite
    idx = config.user_index(user_id)
    chunks, per_file = _load_chunks(user_id)
    if not chunks:
        shutil.rmtree(idx, ignore_errors=True)  # no PDFs left -> drop stale index
        return per_file, chunks
    store = FAISS.from_documents(chunks, embeddings())
    idx.mkdir(parents=True, exist_ok=True)
    store.save_local(str(idx))
    log.info("FAISS rebuilt for user %s: %d chunks from %d files", user_id, len(chunks), len(per_file))
    return per_file, chunks


def add_to_index(user_id, only):
    """Embed only the named PDFs and append to the user's FAISS index (incremental).

    Returns ({filename: chunk_count}, [chunk Documents]) for the added files.
    """
    # ponytail: appends, never dedups — only call for docs not already indexed (pending/failed).
    chunks, per_file = _load_chunks(user_id, only=only)
    if not chunks:
        return per_file, chunks
    idx = config.user_index(user_id)
    store = load_index(user_id)
    if store is None:
        store = FAISS.from_documents(chunks, embeddings())
    else:
        store.add_documents(chunks)
    idx.mkdir(parents=True, exist_ok=True)
    store.save_local(str(idx))
    log.info("FAISS +%d chunks for user %s from %s", len(chunks), user_id, list(per_file))
    return per_file, chunks


def load_index(user_id):
    idx = config.user_index(user_id)
    if not (idx / "index.faiss").exists():
        return None
    return FAISS.load_local(str(idx), embeddings(), allow_dangerous_deserialization=True)


def retrieve(query, user_id, k=4):
    store = load_index(user_id)
    return store.similarity_search(query, k=k) if store else []
