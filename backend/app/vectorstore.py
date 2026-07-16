"""
Free, fully local vector store: Chroma runs embedded (no server, no cost) and
uses sentence-transformers' all-MiniLM-L6-v2 for embeddings (downloaded once,
runs on CPU, no API calls).
"""
import posthog

# Workaround for posthog signature mismatch crash in chromadb telemetry
_original_capture = posthog.capture
def _safe_capture(*args, **kwargs):
    if getattr(posthog, "disabled", False):
        return None
    try:
        if len(args) >= 3:
            return _original_capture(event=args[1], distinct_id=args[0], properties=args[2], **kwargs)
        return _original_capture(*args, **kwargs)
    except Exception:
        return None
posthog.capture = _safe_capture

import chromadb
from chromadb.utils import embedding_functions
from app.config import settings

_client = chromadb.PersistentClient(
    path=settings.chroma_persist_dir,
    settings=chromadb.Settings(anonymized_telemetry=False)
)

_embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = _client.get_or_create_collection(
    name="regulations",
    embedding_function=_embedder,
)


def upsert_document(doc_id: str, text: str, metadata: dict) -> None:
    # Chroma has a metadata size/type limit — keep it flat and small
    collection.upsert(
        ids=[doc_id],
        documents=[text[:8000]],   # cap length for embedding cost/perf
        metadatas=[metadata],
    )


def query_similar(text: str, n_results: int = 5, where: dict | None = None):
    return collection.query(query_texts=[text], n_results=n_results, where=where)
