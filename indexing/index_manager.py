from contextvars import ContextVar
from pathlib import Path
import chromadb
from indexing.chunker import chunk_file, Chunk
from indexing.enricher import enrich
from workspace_context import get_workspace

_DB_PATH = Path(__file__).parent / "chroma_db"

_client = chromadb.PersistentClient(path=str(_DB_PATH))

_collection_name_var: ContextVar[str] = ContextVar("collection_name", default="codebase")


def get_collection_name() -> str:
    """Return the search index name for the current context (session)."""
    return _collection_name_var.get()


def set_collection_name(name: str) -> None:
    """Set the search index name for the current context (session)."""
    _collection_name_var.set(name)


def drop_collection(name: str ) -> None:
    """Delete a search index by name, or the active one if no name is given.
    Safe to call even if the index was never created."""
    try:
        _client.delete_collection(name or get_collection_name())
    except chromadb.errors.NotFoundError:
        pass


def _get_collection():
    return _client.get_or_create_collection(get_collection_name())


def _chunk_id(chunk: Chunk) -> str:
    return f"{chunk.file}::{chunk.start_line}::{chunk.end_line}"


def index_file(path: str) -> int:
    chunks = enrich(chunk_file(path))
    if not chunks:
        return 0
    _get_collection().upsert(
        ids=[_chunk_id(c) for c in chunks],
        documents=[c.summary for c in chunks],
        metadatas=[{
            "file": c.file,
            "type": c.type,
            "start_line": c.start_line,
            "end_line": c.end_line,
            "text": c.text,
        } for c in chunks],
    )
    return len(chunks)


def index_workspace() -> int:
    total = 0
    for ext in ("*.html", "*.css", "*.js"):
        for file in get_workspace().glob(ext):
            n = index_file(file.name)
            print(f"  indexed {file.name}: {n} chunks")
            total += n
    return total


def is_empty() -> bool:
    return _get_collection().count() == 0


def search(query: str, n_results: int = 5) -> list[dict]:
    results = _get_collection().query(query_texts=[query], n_results=n_results)
    hits = []
    for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
        hits.append({
            "file": meta["file"],
            "lines": f"{meta['start_line']}-{meta['end_line']}",
            "type": meta["type"],
            "summary": doc,
            "text": meta["text"],
        })
    return hits
