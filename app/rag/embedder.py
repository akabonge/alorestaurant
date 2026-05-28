"""
Sets up the ChromaDB collection using sentence-transformers for local embeddings.
No API key required for embeddings — runs fully offline.
"""
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.config import get_settings

_collection = None


def get_collection():
    global _collection
    if _collection is None:
        settings = get_settings()
        ef = SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
        client = chromadb.PersistentClient(path=settings.chroma_persist_path)
        _collection = client.get_or_create_collection(
            name=settings.chroma_collection_name,
            embedding_function=ef,
        )
    return _collection
