"""Local retrieval with semantic embeddings when available and TF-IDF fallback."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Iterable

import numpy as np

from .chunking import DocumentChunk


@dataclass(frozen=True)
class RetrievalResult:
    chunk: DocumentChunk
    score: float


class LocalRetriever:
    """Small local vector store for one processed document set at a time."""

    def __init__(
        self,
        prefer_semantic: bool = True,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.prefer_semantic = prefer_semantic
        self.embedding_model_name = embedding_model_name
        self.backend = "not-built"
        self.warnings: list[str] = []
        self.chunks: list[DocumentChunk] = []
        self._model = None
        self._faiss_index = None
        self._matrix = None
        self._vectorizer = None

    def reset(self) -> None:
        self.backend = "not-built"
        self.warnings = []
        self.chunks = []
        self._model = None
        self._faiss_index = None
        self._matrix = None
        self._vectorizer = None

    def build(self, chunks: Iterable[DocumentChunk]) -> None:
        self.reset()
        self.chunks = list(chunks)
        if not self.chunks:
            raise ValueError("No text chunks are available for retrieval.")

        texts = [chunk.text for chunk in self.chunks]

        if self.prefer_semantic and self._try_build_semantic(texts):
            return

        if self._try_build_tfidf(texts):
            return

        self._build_keyword_index(texts)

    def query(self, question: str, top_k: int = 5) -> list[RetrievalResult]:
        if not self.chunks:
            raise ValueError("Retriever has not been built yet.")
        if not question.strip():
            return []
        top_k = max(1, min(top_k, len(self.chunks)))

        if self.backend.startswith("sentence-transformers"):
            return self._query_semantic(question, top_k)
        if self.backend == "tf-idf":
            return self._query_tfidf(question, top_k)
        return self._query_keyword(question, top_k)

    def _try_build_semantic(self, texts: list[str]) -> bool:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as exc:
            self.warnings.append(
                "Sentence Transformers is not available. Using TF-IDF fallback. "
                f"Reason: {exc}"
            )
            return False

        try:
            self._model = SentenceTransformer(self.embedding_model_name)
            embeddings = self._model.encode(
                texts, normalize_embeddings=True, show_progress_bar=False
            )
            matrix = np.asarray(embeddings, dtype="float32")
            self._matrix = matrix
        except Exception as exc:
            self.warnings.append(
                "Could not load the embedding model. Using TF-IDF fallback. "
                f"Reason: {exc}"
            )
            return False

        try:
            import faiss  # type: ignore

            index = faiss.IndexFlatIP(matrix.shape[1])
            index.add(matrix)
            self._faiss_index = index
            self.backend = "sentence-transformers + faiss"
        except Exception as exc:
            self.warnings.append(
                "FAISS is not available. Semantic embeddings will use numpy search. "
                f"Reason: {exc}"
            )
            self.backend = "sentence-transformers + numpy"

        return True

    def _try_build_tfidf(self, texts: list[str]) -> bool:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except Exception as exc:
            self.warnings.append(
                "scikit-learn is not available. Using keyword fallback. "
                f"Reason: {exc}"
            )
            return False

        self._vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), max_features=20000
        )
        self._matrix = self._vectorizer.fit_transform(texts)
        self.backend = "tf-idf"
        self.warnings.append(
            "Using TF-IDF fallback. This is lexical retrieval, not semantic embeddings."
        )
        return True

    def _build_keyword_index(self, texts: list[str]) -> None:
        self._matrix = [_token_set(text) for text in texts]
        self.backend = "keyword"
        self.warnings.append(
            "Using simple keyword fallback. Install scikit-learn for stronger retrieval."
        )

    def _query_semantic(self, question: str, top_k: int) -> list[RetrievalResult]:
        query_embedding = self._model.encode(
            [question], normalize_embeddings=True, show_progress_bar=False
        )
        query_vector = np.asarray(query_embedding, dtype="float32")

        if self._faiss_index is not None:
            scores, indices = self._faiss_index.search(query_vector, top_k)
            pairs = zip(indices[0].tolist(), scores[0].tolist())
        else:
            scores = np.dot(self._matrix, query_vector[0])
            ordered = np.argsort(scores)[::-1][:top_k]
            pairs = [(int(index), float(scores[index])) for index in ordered]

        return [
            RetrievalResult(chunk=self.chunks[index], score=float(score))
            for index, score in pairs
            if index >= 0
        ]

    def _query_tfidf(self, question: str, top_k: int) -> list[RetrievalResult]:
        query_vector = self._vectorizer.transform([question])
        scores = (self._matrix @ query_vector.T).toarray().ravel()
        ordered = np.argsort(scores)[::-1][:top_k]
        return [
            RetrievalResult(chunk=self.chunks[int(index)], score=float(scores[index]))
            for index in ordered
        ]

    def _query_keyword(self, question: str, top_k: int) -> list[RetrievalResult]:
        query_tokens = _token_set(question)
        scored = []
        for index, chunk_tokens in enumerate(self._matrix):
            if not query_tokens or not chunk_tokens:
                score = 0.0
            else:
                overlap = len(query_tokens & chunk_tokens)
                score = overlap / math.sqrt(len(query_tokens) * len(chunk_tokens))
            scored.append((index, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return [
            RetrievalResult(chunk=self.chunks[index], score=float(score))
            for index, score in scored[:top_k]
        ]


def _token_set(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", text)
        if token.lower() not in {"the", "and", "for", "with", "that", "this"}
    }

