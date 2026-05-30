from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.documents import Document


@dataclass(frozen=True)
class StoreStats:
    chunks: int
    documents: int
    uploads: int


class KnowledgeStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id TEXT PRIMARY KEY,
                    parent_id TEXT,
                    title TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    chunk_index INTEGER,
                    total_chunks INTEGER,
                    content_hash TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_doc_type ON knowledge_chunks(doc_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_source_kind ON knowledge_chunks(source_kind)"
            )

    def replace_chunks(self, chunks: list[Document]) -> None:
        self.initialize()
        with self._connect() as connection:
            connection.execute("DELETE FROM knowledge_chunks")
            connection.executemany(
                """
                INSERT INTO knowledge_chunks (
                    id, parent_id, title, doc_type, source, content, source_kind,
                    chunk_index, total_chunks, content_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [_chunk_row(chunk) for chunk in chunks],
            )

    def list_chunks(self, *, source_kind: str | None = None) -> list[Document]:
        self.initialize()
        query = """
            SELECT id, title, doc_type, source, content, source_kind,
                   parent_id, chunk_index, total_chunks
            FROM knowledge_chunks
        """
        params: tuple[str, ...] = ()
        if source_kind:
            query += " WHERE source_kind = ?"
            params = (source_kind,)
        query += " ORDER BY source_kind, doc_type, source, chunk_index"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            Document(
                id=row["id"],
                title=row["title"],
                doc_type=row["doc_type"],
                source=row["source"],
                content=row["content"],
                source_kind=row["source_kind"],
                parent_id=row["parent_id"],
                chunk_index=row["chunk_index"],
                total_chunks=row["total_chunks"],
            )
            for row in rows
        ]

    def stats(self) -> StoreStats:
        self.initialize()
        with self._connect() as connection:
            chunks = connection.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0]
            documents = connection.execute(
                "SELECT COUNT(DISTINCT COALESCE(parent_id, id)) FROM knowledge_chunks"
            ).fetchone()[0]
            uploads = connection.execute(
                "SELECT COUNT(*) FROM knowledge_chunks WHERE source_kind = 'user_upload'"
            ).fetchone()[0]
        return StoreStats(chunks=chunks, documents=documents, uploads=uploads)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection


def _chunk_row(chunk: Document) -> tuple[object, ...]:
    return (
        chunk.id,
        chunk.parent_id,
        chunk.title,
        chunk.doc_type,
        chunk.source,
        chunk.content,
        chunk.source_kind,
        chunk.chunk_index,
        chunk.total_chunks,
        hashlib.sha1(chunk.content.encode("utf-8")).hexdigest(),
    )

