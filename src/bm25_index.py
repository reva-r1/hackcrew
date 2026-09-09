import re
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from src.config import DATA_DIR

BM25_PICKLE_PATH = DATA_DIR / "bm25_index.pkl"

def tokenize(text: str) -> List[str]:
    """Basic lowercased regex word tokenization for BM25."""
    return re.findall(r'\w+', text.lower())

class BM25Index:
    def __init__(self, index_path: Optional[Path] = None):
        self.index_path = index_path or BM25_PICKLE_PATH
        self.chunk_ids: List[str] = []
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None
        self._load()

    def _load(self):
        if self.index_path.exists():
            try:
                with open(self.index_path, "rb") as f:
                    data = pickle.load(f)
                    self.chunk_ids = data.get("chunk_ids", [])
                    self.documents = data.get("documents", [])
                    self.metadatas = data.get("metadatas", [])
                    self.corpus_tokens = data.get("corpus_tokens", [])
                    if self.corpus_tokens:
                        self.bm25 = BM25Okapi(self.corpus_tokens)
            except Exception as e:
                print(f"Warning: Failed to load BM25 index from {self.index_path}: {e}")
                self.bm25 = None

    def _save(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({
                "chunk_ids": self.chunk_ids,
                "documents": self.documents,
                "metadatas": self.metadatas,
                "corpus_tokens": self.corpus_tokens
            }, f)

    def add_chunks(
        self,
        chunk_ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """Adds or updates chunks in the BM25 index."""
        if not chunk_ids:
            return

        metas = metadatas or [{} for _ in chunk_ids]
        
        # Build index mapping to replace existing or append new
        id_to_idx = {cid: idx for idx, cid in enumerate(self.chunk_ids)}
        
        for cid, doc, meta in zip(chunk_ids, documents, metas):
            tokens = tokenize(doc)
            if cid in id_to_idx:
                idx = id_to_idx[cid]
                self.documents[idx] = doc
                self.metadatas[idx] = meta
                self.corpus_tokens[idx] = tokens
            else:
                self.chunk_ids.append(cid)
                self.documents.append(doc)
                self.metadatas.append(meta)
                self.corpus_tokens.append(tokens)

        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)
            self._save()

    def search(self, query: str, top_k: int = 25) -> List[Dict[str, Any]]:
        """
        Searches BM25 index for top_k results matching query.
        Returns [{'chunk_id': str, 'score': float, 'text': str, 'metadata': dict}, ...]
        """
        if not self.bm25 or not self.chunk_ids:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        
        # Pair with indices and sort descending by score
        indexed_scores = [(idx, score) for idx, score in enumerate(scores) if score > 0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in indexed_scores[:top_k]:
            results.append({
                "chunk_id": self.chunk_ids[idx],
                "score": float(score),
                "text": self.documents[idx],
                "metadata": self.metadatas[idx]
            })

        return results

    def count(self) -> int:
        return len(self.chunk_ids)

    def delete_chunks_by_doc_name(self, doc_name: str):
        """Removes existing chunks for doc_name from BM25 index."""
        keep_indices = [
            i for i, m in enumerate(self.metadatas)
            if m.get("doc_name") != doc_name
        ]
        if len(keep_indices) == len(self.chunk_ids):
            return  # Nothing to remove

        self.chunk_ids = [self.chunk_ids[i] for i in keep_indices]
        self.documents = [self.documents[i] for i in keep_indices]
        self.metadatas = [self.metadatas[i] for i in keep_indices]
        self.corpus_tokens = [self.corpus_tokens[i] for i in keep_indices]
        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)
        else:
            self.bm25 = None
        self._save()

    def clear(self):
        self.chunk_ids = []
        self.documents = []
        self.metadatas = []
        self.corpus_tokens = []
        self.bm25 = None
        if self.index_path.exists():
            self.index_path.unlink()

