import logging

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


def _load_chunks():
    """Load every PDF in Artifacts, chunk with source/page/index metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP
    )
    chunks, per_file = [], {}
    for pdf in sorted(config.ARTIFACTS_DIR.glob("*.pdf")):
        pages = PyPDFLoader(str(pdf)).load()         # one Document per page
        split = splitter.split_documents(pages)       # fix #2: no [:20] cap
        for i, d in enumerate(split):
            d.metadata["source_file"] = pdf.name
            d.metadata["chunk_index"] = i
            d.metadata["page"] = d.metadata.get("page", 0) + 1  # 1-based
        chunks.extend(split)
        per_file[pdf.name] = len(split)
    return chunks, per_file


def rebuild_index():
    """Rebuild whole FAISS index from all PDFs, persist to disk (fix #2 + #3).

    Returns {filename: chunk_count}.
    """
    # ponytail: full rebuild on every ingest; switch to incremental .add if reindex hurts
    # ponytail: GoogleGenerativeAIEmbeddings batches internally; add manual batching/retry if rate limits bite
    chunks, per_file = _load_chunks()
    if not chunks:
        return per_file
    store = FAISS.from_documents(chunks, embeddings())
    config.FAISS_DIR.mkdir(exist_ok=True)
    store.save_local(str(config.FAISS_DIR))
    log.info("FAISS rebuilt: %d chunks from %d files", len(chunks), len(per_file))
    return per_file


def load_index():
    if not (config.FAISS_DIR / "index.faiss").exists():
        return None
    return FAISS.load_local(
        str(config.FAISS_DIR), embeddings(), allow_dangerous_deserialization=True
    )


def retrieve(query, k=4):
    store = load_index()
    return store.similarity_search(query, k=k) if store else []
