import asyncio
from pathlib import Path
from typing import List, Optional, Any
import chromadb
from chromadb.utils import embedding_functions

from services.gemini import ask_gemini

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
COLLECTION_NAME = "neoretail_knowledge"
PERSIST_DIR = "./chroma_db"

_client: Any = None
_collection: Any = None


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def _load_documents_from_folder(folder_path: Path) -> List[dict]:
    docs = []
    for file_path in folder_path.glob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        chunks = _chunk_text(content)
        for i, chunk in enumerate(chunks):
            docs.append({
                "content": chunk,
                "metadata": {"source": file_path.stem, "chunk_id": i},
            })
    return docs


def _init_chromadb() -> None:
    global _client, _collection
    _client = chromadb.PersistentClient(path=PERSIST_DIR)
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )


def _populate_collection(docs: List[dict]) -> None:
    global _collection
    if _collection is None:
        return
    if _collection.count() > 0:
        return
    ids = [f"{doc['metadata']['source']}_{doc['metadata']['chunk_id']}" for doc in docs]
    contents = [doc["content"] for doc in docs]
    metadatas = [doc["metadata"] for doc in docs]
    _collection.add(ids=ids, documents=contents, metadatas=metadatas)


async def initialize_rag():
    kb_path = Path(__file__).parent.parent / "knowledge_base"
    if not kb_path.exists():
        print(f"Warning: Knowledge base folder not found at {kb_path}")
        return
    docs = _load_documents_from_folder(kb_path)
    if not docs:
        print("No documents found in knowledge_base/")
        return
    await asyncio.to_thread(_init_chromadb)
    await asyncio.to_thread(_populate_collection, docs)
    print(f"RAG initialized: {len(docs)} chunks loaded into ChromaDB")


async def retrieve_context(query: str, n_results: int = 3) -> str:
    global _collection
    if _collection is None:
        return ""
    results = await asyncio.to_thread(
        _collection.query, query_texts=[query], n_results=n_results,
    )
    if results and "documents" in results and results["documents"] and results["documents"][0]:
        chunks = results["documents"][0]
        return "\n\n---\n\n".join(chunks)
    return ""


async def answer_with_rag(query: str) -> str:
    context = await retrieve_context(query)
    if not context:
        return "I don't have that information. Please contact support@neoretail.com."
    prompt = f"""You are a helpful customer service assistant for NeoRetail, a high-end digital clothing brand.
Use only the context below to answer the customer's question.
Be concise, friendly, and professional.
If the answer is not in the context, say: "I don't have that information. Please contact support@neoretail.com."
Do not make up information.

CONTEXT:
{context}

CUSTOMER QUESTION:
{query}

ANSWER:"""
    reply = await ask_gemini(prompt)
    return reply