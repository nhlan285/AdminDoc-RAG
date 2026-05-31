from __future__ import annotations

import hashlib
import math
import sqlite3
import struct
from dataclasses import dataclass
from pathlib import Path

from src.documents import Document
from src.embeddings import EmbeddingProvider


@dataclass(frozen=True)
class VectorIndexStats:
    indexed: int
    refreshed: int
    removed: int
    provider_signature: str


@dataclass(frozen=True)
class VectorHit:
    document: Document
    score: float


class SQLiteVectorStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_vectors (
                    id TEXT NOT NULL,
                    embedding_signature TEXT NOT NULL,
                    embedding_dim INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id, embedding_signature)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_vectors_signature
                ON knowledge_vectors(embedding_signature)
                """
            )

    def rebuild(
        self,
        documents: list[Document],
        provider: EmbeddingProvider,
        *,
        batch_size: int = 32,
    ) -> VectorIndexStats:
        self.initialize()
        signature = provider.config.signature
        document_by_id = {document.id: document for document in documents}
        active_ids = set(document_by_id)
        refreshed = 0
        removed = 0

        with self._connect() as connection:
            existing_rows = connection.execute(
                """
                SELECT id, content_hash
                FROM knowledge_vectors
                WHERE embedding_signature = ?
                """,
                (signature,),
            ).fetchall()
            existing_hashes = {row["id"]: row["content_hash"] for row in existing_rows}

            stale_ids = [item_id for item_id in existing_hashes if item_id not in active_ids]
            if stale_ids:
                connection.executemany(
                    """
                    DELETE FROM knowledge_vectors
                    WHERE id = ? AND embedding_signature = ?
                    """,
                    [(item_id, signature) for item_id in stale_ids],
                )
                removed = len(stale_ids)

            pending = [
                document
                for document in documents
                if existing_hashes.get(document.id) != _content_hash(document)
            ]

            for start in range(0, len(pending), batch_size):
                batch = pending[start : start + batch_size]
                vectors = provider.embed_texts([_embedding_text(document) for document in batch])
                connection.executemany(
                    """
                    INSERT INTO knowledge_vectors (
                        id, embedding_signature, embedding_dim, content_hash, embedding, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(id, embedding_signature) DO UPDATE SET
                        embedding_dim = excluded.embedding_dim,
                        content_hash = excluded.content_hash,
                        embedding = excluded.embedding,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    [
                        (
                            document.id,
                            signature,
                            len(vector),
                            _content_hash(document),
                            _pack_vector(vector),
                        )
                        for document, vector in zip(batch, vectors)
                    ],
                )
                refreshed += len(batch)

            indexed = connection.execute(
                """
                SELECT COUNT(*)
                FROM knowledge_vectors
                WHERE embedding_signature = ?
                """,
                (signature,),
            ).fetchone()[0]

        return VectorIndexStats(
            indexed=int(indexed),
            refreshed=refreshed,
            removed=removed,
            provider_signature=signature,
        )

    def search(
        self,
        query: str,
        documents: list[Document],
        provider: EmbeddingProvider,
        *,
        doc_type: str | None = None,
        top_k: int = 6,
        min_score: float = 0.05,
    ) -> list[VectorHit]:
        if not documents:
            return []

        self.rebuild(documents, provider)
        signature = provider.config.signature
        candidates = _filter_by_doc_type(documents, doc_type)
        if not candidates:
            return []

        candidate_by_id = {document.id: document for document in candidates}
        query_vector = provider.embed_query(query)

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, embedding_dim, embedding
                FROM knowledge_vectors
                WHERE embedding_signature = ?
                """,
                (signature,),
            ).fetchall()

        hits: list[VectorHit] = []
        for row in rows:
            document = candidate_by_id.get(row["id"])
            if not document:
                continue
            vector = _unpack_vector(row["embedding"], int(row["embedding_dim"]))
            score = _cosine_similarity(query_vector, vector)
            if score >= min_score:
                hits.append(VectorHit(document=document, score=score))

        hits.sort(key=lambda hit: (hit.score, hit.document.title), reverse=True)
        return hits[:top_k]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection


def _filter_by_doc_type(
    documents: list[Document],
    doc_type: str | None,
) -> list[Document]:
    if not doc_type:
        return documents
    has_exact_doc_type = any(document.doc_type == doc_type for document in documents)
    if not has_exact_doc_type:
        return documents
    return [document for document in documents if document.doc_type == doc_type]


def _embedding_text(document: Document) -> str:
    return " ".join(
        [
            document.title,
            document.title,
            document.doc_type,
            document.doc_type,
            document.source,
            document.content,
        ]
    )


def _content_hash(document: Document) -> str:
    return hashlib.sha1(_embedding_text(document).encode("utf-8")).hexdigest()


def _pack_vector(vector: list[float]) -> bytes:
    return struct.pack(f"<{len(vector)}f", *vector)


def _unpack_vector(blob: bytes, dimensions: int) -> list[float]:
    return list(struct.unpack(f"<{dimensions}f", blob))


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    size = min(len(left), len(right))
    if not size:
        return 0.0
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size]))
    right_norm = math.sqrt(sum(value * value for value in right[:size]))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)
