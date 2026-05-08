from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from src.documents import Document


DEFAULT_CHUNK_SIZE_WORDS = 120
DEFAULT_CHUNK_OVERLAP_WORDS = 20


def clean_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)

    cleaned_lines: list[str] = []
    previous_blank = False
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
            continue

        cleaned_lines.append(line)
        previous_blank = False

    return "\n".join(cleaned_lines).strip()


def parse_documents_from_text(
    *,
    filename: str,
    text: str,
    default_doc_type: str,
    source_kind: str = "system",
) -> list[Document]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".json":
        return _parse_json_documents(
            text=text,
            filename=filename,
            default_doc_type=default_doc_type,
            source_kind=source_kind,
        )

    cleaned = clean_text(text)
    if not cleaned:
        return []

    title = _guess_title(filename, cleaned)
    return [
        Document(
            id=_stable_id("DOC", filename, title, cleaned),
            title=title,
            doc_type=default_doc_type,
            source=filename,
            content=cleaned,
            source_kind=source_kind,
        )
    ]


def build_chunks(
    documents: list[Document],
    *,
    chunk_size_words: int = DEFAULT_CHUNK_SIZE_WORDS,
    overlap_words: int = DEFAULT_CHUNK_OVERLAP_WORDS,
) -> list[Document]:
    chunks: list[Document] = []
    for document in documents:
        chunks.extend(
            chunk_document(
                document,
                chunk_size_words=chunk_size_words,
                overlap_words=overlap_words,
            )
        )

    return chunks


def chunk_document(
    document: Document,
    *,
    chunk_size_words: int = DEFAULT_CHUNK_SIZE_WORDS,
    overlap_words: int = DEFAULT_CHUNK_OVERLAP_WORDS,
) -> list[Document]:
    cleaned_content = clean_text(document.content)
    words = cleaned_content.split()
    if not words:
        return []

    chunk_size_words = max(40, chunk_size_words)
    overlap_words = max(0, min(overlap_words, chunk_size_words // 2))

    raw_chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size_words, len(words))
        raw_chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap_words

    total_chunks = len(raw_chunks)
    return [
        Document(
            id=f"{document.id}-CH{index:03d}",
            title=document.title,
            doc_type=document.doc_type,
            source=document.source,
            content=chunk_text,
            source_kind=document.source_kind,
            parent_id=document.id,
            chunk_index=index,
            total_chunks=total_chunks,
        )
        for index, chunk_text in enumerate(raw_chunks, start=1)
    ]


def decode_file_bytes(raw_bytes: bytes) -> str:
    try:
        return raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw_bytes.decode("utf-8", errors="replace")


def _parse_json_documents(
    *,
    text: str,
    filename: str,
    default_doc_type: str,
    source_kind: str,
) -> list[Document]:
    raw_data = json.loads(text)
    raw_documents = raw_data.get("documents", []) if isinstance(raw_data, dict) else raw_data

    documents: list[Document] = []
    for index, raw_item in enumerate(raw_documents, start=1):
        if not isinstance(raw_item, dict):
            continue

        content = clean_text(str(raw_item.get("content") or raw_item.get("text") or ""))
        if not content:
            continue

        title = str(raw_item.get("title") or _guess_title(filename, content)).strip()
        source = str(raw_item.get("source") or filename).strip()
        doc_type = str(raw_item.get("doc_type") or default_doc_type).strip()
        document_id = str(raw_item.get("id") or "").strip()
        if not document_id:
            document_id = _stable_id("DOC", filename, title, str(index), content)

        documents.append(
            Document(
                id=document_id,
                title=title,
                doc_type=doc_type,
                source=source,
                content=content,
                source_kind=source_kind,
            )
        )

    return documents


def _guess_title(filename: str, content: str) -> str:
    for line in content.splitlines():
        line = line.strip(" #\t")
        if line:
            return line[:90]

    return Path(filename).stem.replace("_", " ").strip() or "Tài liệu chưa đặt tên"


def _stable_id(prefix: str, *parts: Any) -> str:
    raw_value = "|".join(str(part) for part in parts)
    digest = hashlib.sha1(raw_value.encode("utf-8")).hexdigest()[:10].upper()
    return f"{prefix}-{digest}"
