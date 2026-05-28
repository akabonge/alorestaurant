"""
Retrieves the most relevant document chunks from ChromaDB for a given query.
"""
from app.rag.embedder import get_collection
from app.config import get_settings


def retrieve(query: str) -> tuple[str, list[str]]:
    """
    Returns (formatted_context, source_labels) for the top-k chunks closest to the query.
    """
    settings = get_settings()
    collection = get_collection()

    if collection.count() == 0:
        return "", ["[no documents indexed — run scripts/ingest_data.py first]"]

    results = collection.query(
        query_texts=[query],
        n_results=min(settings.max_retrieved_chunks, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    context_parts = []
    sources = []

    for doc, meta in zip(docs, metas):
        context_parts.append(doc)
        label = meta.get("source", "restaurant data")
        if label not in sources:
            sources.append(label)

    context = "\n\n---\n\n".join(context_parts)
    return context, sources
