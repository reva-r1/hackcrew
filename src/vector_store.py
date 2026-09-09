import chromadb
from typing import List, Dict, Any, Optional
from src.config import CHROMA_DIR

class VectorStore:
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_dir = str(persist_directory or CHROMA_DIR)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        # Using cosine distance
        self.collection = self.client.get_or_create_collection(
            name="enterprise_rag_chunks",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ):
        """Adds or updates chunks in the Chroma vector store."""
        if not chunk_ids:
            return
        self.collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def search(self, query_embedding: List[float], top_k: int = 25) -> List[Dict[str, Any]]:
        """
        Searches Chroma for top_k nearest chunks.
        Returns a list of dicts:
        [{'chunk_id': str, 'score': float, 'text': str, 'metadata': dict}, ...]
        Cosine distance in chroma is d in [0, 2], cosine similarity is 1 - d.
        """
        count = self.collection.count()
        if count == 0:
            return []
        
        n_results = min(top_k, count)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        output = []
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for i, chunk_id in enumerate(ids):
            # Chroma with hnsw:space "cosine" returns cosine distance = 1 - cosine_similarity
            dist = distances[i] if i < len(distances) else 1.0
            # Higher similarity score is better
            sim_score = max(0.0, 1.0 - dist)
            doc_text = str(documents[i]) if (i < len(documents) and documents[i] is not None) else ""
            meta = metadatas[i] if (i < len(metadatas) and metadatas[i] is not None) else {}

            output.append({
                "chunk_id": chunk_id,
                "score": sim_score,
                "text": doc_text,
                "metadata": meta
            })

        return output

    def count(self) -> int:
        return self.collection.count()

    def delete_chunks_by_doc_name(self, doc_name: str):
        """Removes existing chunks for doc_name from ChromaDB to prevent duplicates."""
        try:
            self.collection.delete(where={"doc_name": doc_name})
        except Exception as e:
            print(f"Notice during Chroma delete: {e}")

    def clear(self):
        self.client.delete_collection("enterprise_rag_chunks")
        self.collection = self.client.get_or_create_collection(
            name="enterprise_rag_chunks",
            metadata={"hnsw:space": "cosine"}
        )

