from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    doc_type: str
    source: str
    content: str
    source_kind: str = "system"
    parent_id: str | None = None
    chunk_index: int | None = None
    total_chunks: int | None = None

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "Document":
        return cls(
            id=str(item.get("id", "")).strip(),
            title=str(item.get("title", "")).strip(),
            doc_type=str(item.get("doc_type", "")).strip(),
            source=str(item.get("source", "")).strip(),
            content=str(item.get("content", "")).strip(),
            source_kind=str(item.get("source_kind") or "system").strip() or "system",
            parent_id=_optional_str(item.get("parent_id")),
            chunk_index=_optional_int(item.get("chunk_index")),
            total_chunks=_optional_int(item.get("total_chunks")),
        )


def load_documents(path: Path) -> list[Document]:
    with path.open("r", encoding="utf-8") as file:
        raw_documents = json.load(file)

    if isinstance(raw_documents, dict):
        raw_documents = raw_documents.get("documents", [])

    return [Document.from_dict(item) for item in raw_documents]


def document_to_dict(document: Document) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": document.id,
        "title": document.title,
        "doc_type": document.doc_type,
        "source": document.source,
        "content": document.content,
        "source_kind": document.source_kind,
    }

    if document.parent_id is not None:
        item["parent_id"] = document.parent_id
    if document.chunk_index is not None:
        item["chunk_index"] = document.chunk_index
    if document.total_chunks is not None:
        item["total_chunks"] = document.total_chunks

    return item


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None
