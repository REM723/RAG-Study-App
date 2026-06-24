import logging
import shutil

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from . import config

log = logging.getLogger("rag")

_embeddings = None


def embeddings():
    global _embeddings
    if _embeddings is None:
        # bge wrapper sets normalize + the bge query instruction by default.
        # First use downloads the model (~130MB) from HuggingFace.
        _embeddings = HuggingFaceBgeEmbeddings(model_name=config.EMBED_MODEL)
    return _embeddings


def _load_chunks(user_id):
    """Load every PDF in the user's Artifacts folder, chunk with source/page/index metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP
    )
    chunks, per_file = [], {}
    for pdf in sorted(config.user_artifacts(user_id).glob("*.pdf")):
        pages = PyPDFLoader(str(pdf)).load()         # one Document per page
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


def load_index(user_id):
    idx = config.user_index(user_id)
    if not (idx / "index.faiss").exists():
        return None
    return FAISS.load_local(str(idx), embeddings(), allow_dangerous_deserialization=True)


def retrieve(query, user_id, k=4):
    store = load_index(user_id)
    return store.similarity_search(query, k=k) if store else []
