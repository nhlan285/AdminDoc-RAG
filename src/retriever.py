from __future__ import annotations

import math
import os
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.documents import Document
from src.embeddings import (
    EmbeddingConfig,
    build_embedding_provider,
    describe_embedding_config,
    load_embedding_config,
)
from src.vector_store import SQLiteVectorStore, VectorIndexStats


def _normalize_for_search(text: str) -> str:
    text = text.lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return unicodedata.normalize("NFC", text)


RAW_STOP_WORDS = {
    "ai",
    "bằng",
    "bị",
    "bộ",
    "các",
    "cái",
    "cần",
    "cho",
    "công",
    "cơ",
    "của",
    "cùng",
    "đã",
    "để",
    "đến",
    "được",
    "động",
    "gia",
    "hãy",
    "khi",
    "không",
    "ký",
    "là",
    "làm",
    "liên",
    "một",
    "muốn",
    "này",
    "những",
    "quan",
    "quốc",
    "số",
    "soạn",
    "tạo",
    "theo",
    "thông",
    "thì",
    "tôi",
    "tự",
    "trong",
    "và",
    "văn",
    "về",
    "việc",
}


STOP_WORDS = {_normalize_for_search(word) for word in RAW_STOP_WORDS}


@dataclass(frozen=True)
class SearchResult:
    document: Document
    score: float
    matched_terms: list[str]
    retrieval_method: str = "bm25"
    bm25_score: float = 0.0
    vector_score: float = 0.0


@dataclass(frozen=True)
class RetrievalConfig:
    mode: str
    bm25_weight: float
    vector_weight: float
    vector_min_score: float
    vector_top_k_multiplier: int
    allow_vector_only_matches: bool
    vector_db_path: Path
    embedding_config: EmbeddingConfig


class Retriever(Protocol):
    def search(
        self,
        query: str,
        *,
        doc_type: str | None = None,
        top_k: int = 3,
        min_score: float = 0.15,
    ) -> list[SearchResult]:
        ...


class BM25Retriever:
    def __init__(
        self,
        documents: list[Document],
        *,
        k1: float = 1.5,
        b: float = 0.75,
        doc_type_boost: float = 1.2,
    ) -> None:
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.doc_type_boost = doc_type_boost
        self._term_counts = [_count_terms(document) for document in documents]
        self._doc_lengths = [sum(counts.values()) for counts in self._term_counts]
        self._avg_doc_length = (
            sum(self._doc_lengths) / len(self._doc_lengths)
            if self._doc_lengths
            else 0.0
        )
        self._idf = self._build_idf()

    def search(
        self,
        query: str,
        *,
        doc_type: str | None = None,
        top_k: int = 3,
        min_score: float = 0.15,
    ) -> list[SearchResult]:
        query_terms = tokenize(query)
        if not query_terms:
            return []

        scored: list[SearchResult] = []
        has_exact_doc_type = bool(doc_type) and any(
            document.doc_type == doc_type for document in self.documents
        )
        for document, term_counts, doc_length in zip(
            self.documents,
            self._term_counts,
            self._doc_lengths,
        ):
            if has_exact_doc_type and document.doc_type != doc_type:
                continue
            matched_terms = sorted(query_terms.intersection(term_counts))
            if not matched_terms:
                continue
            if len(query_terms) >= 3 and len(matched_terms) < 2:
                continue

            score = self._score_document(matched_terms, term_counts, doc_length)
            if doc_type and document.doc_type == doc_type:
                score *= self.doc_type_boost

            if score >= min_score:
                scored.append(
                    SearchResult(
                        document=document,
                        score=score,
                        matched_terms=matched_terms,
                        retrieval_method="bm25",
                        bm25_score=score,
                    )
                )

        scored.sort(
            key=lambda item: (
                item.score,
                item.document.doc_type == doc_type if doc_type else False,
                item.document.title,
            ),
            reverse=True,
        )
        return scored[:top_k]

    def _build_idf(self) -> dict[str, float]:
        total_documents = len(self.documents)
        document_frequency: Counter[str] = Counter()
        for term_counts in self._term_counts:
            document_frequency.update(term_counts.keys())

        return {
            term: math.log(1 + (total_documents - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def _score_document(
        self,
        matched_terms: list[str],
        term_counts: Counter[str],
        doc_length: int,
    ) -> float:
        if not self._avg_doc_length:
            return 0.0

        score = 0.0
        length_factor = 1 - self.b + self.b * doc_length / self._avg_doc_length
        for term in matched_terms:
            term_frequency = term_counts[term]
            denominator = term_frequency + self.k1 * length_factor
            score += self._idf.get(term, 0.0) * (
                term_frequency * (self.k1 + 1) / denominator
            )

        return score


class VectorRetriever:
    def __init__(
        self,
        documents: list[Document],
        *,
        store: SQLiteVectorStore,
        embedding_config: EmbeddingConfig,
    ) -> None:
        self.documents = documents
        self.store = store
        self.embedding_config = embedding_config

    def search(
        self,
        query: str,
        *,
        doc_type: str | None = None,
        top_k: int = 3,
        min_score: float = 0.05,
    ) -> list[SearchResult]:
        provider = build_embedding_provider(self.embedding_config)
        hits = self.store.search(
            query,
            self.documents,
            provider,
            doc_type=doc_type,
            top_k=top_k,
            min_score=min_score,
        )
        return [
            SearchResult(
                document=hit.document,
                score=hit.score,
                matched_terms=["semantic"],
                retrieval_method="vector",
                vector_score=hit.score,
            )
            for hit in hits
        ]


class HybridRetriever:
    def __init__(
        self,
        documents: list[Document],
        *,
        bm25_weight: float,
        vector_weight: float,
        vector_min_score: float,
        vector_top_k_multiplier: int,
        allow_vector_only_matches: bool,
        store: SQLiteVectorStore,
        embedding_config: EmbeddingConfig,
    ) -> None:
        self.documents = documents
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.vector_min_score = vector_min_score
        self.vector_top_k_multiplier = max(1, vector_top_k_multiplier)
        self.allow_vector_only_matches = allow_vector_only_matches
        self.store = store
        self.embedding_config = embedding_config

    def search(
        self,
        query: str,
        *,
        doc_type: str | None = None,
        top_k: int = 3,
        min_score: float = 0.15,
    ) -> list[SearchResult]:
        expanded_top_k = max(top_k * self.vector_top_k_multiplier, top_k)
        bm25_results = BM25Retriever(self.documents).search(
            query,
            doc_type=doc_type,
            top_k=expanded_top_k,
            min_score=min_score,
        )

        try:
            vector_results = VectorRetriever(
                self.documents,
                store=self.store,
                embedding_config=self.embedding_config,
            ).search(
                query,
                doc_type=doc_type,
                top_k=expanded_top_k,
                min_score=self.vector_min_score,
            )
        except Exception:
            return bm25_results[:top_k]

        merged = _merge_rankings(
            bm25_results=bm25_results,
            vector_results=vector_results,
            bm25_weight=self.bm25_weight,
            vector_weight=self.vector_weight,
            allow_vector_only_matches=self.allow_vector_only_matches,
            doc_type=doc_type,
        )
        return merged[:top_k]


def tokenize(text: str) -> set[str]:
    return set(tokenize_sequence(text))


def tokenize_sequence(text: str) -> list[str]:
    normalized_text = _normalize_for_search(text)
    tokens = re.findall(r"\w+", normalized_text, flags=re.UNICODE)
    return [
        token
        for token in tokens
        if len(token) > 1 and token not in STOP_WORDS and not token.isnumeric()
    ]


def retrieve(
    query: str,
    documents: list[Document],
    *,
    doc_type: str | None = None,
    top_k: int = 3,
    min_score: float = 0.15,
    mode: str | None = None,
    project_root: Path | None = None,
) -> list[SearchResult]:
    config = load_retrieval_config(project_root)
    selected_mode = (mode or config.mode).strip().lower()
    if selected_mode == "bm25":
        retriever = BM25Retriever(documents)
        return retriever.search(
            query,
            doc_type=doc_type,
            top_k=top_k,
            min_score=min_score,
        )

    store = SQLiteVectorStore(config.vector_db_path)
    if selected_mode == "vector":
        try:
            retriever = VectorRetriever(
                documents,
                store=store,
                embedding_config=config.embedding_config,
            )
            return retriever.search(
                query,
                doc_type=doc_type,
                top_k=top_k,
                min_score=config.vector_min_score,
            )
        except Exception:
            retriever = BM25Retriever(documents)
            return retriever.search(
                query,
                doc_type=doc_type,
                top_k=top_k,
                min_score=min_score,
            )

    retriever = HybridRetriever(
        documents,
        bm25_weight=config.bm25_weight,
        vector_weight=config.vector_weight,
        vector_min_score=config.vector_min_score,
        vector_top_k_multiplier=config.vector_top_k_multiplier,
        allow_vector_only_matches=config.allow_vector_only_matches,
        store=store,
        embedding_config=config.embedding_config,
    )
    return retriever.search(
        query,
        doc_type=doc_type,
        top_k=top_k,
        min_score=min_score,
    )


def rebuild_vector_index(
    documents: list[Document],
    *,
    project_root: Path | None = None,
) -> VectorIndexStats:
    config = load_retrieval_config(project_root)
    provider = build_embedding_provider(config.embedding_config)
    store = SQLiteVectorStore(config.vector_db_path)
    return store.rebuild(documents, provider)


def describe_retrieval_status(project_root: Path | None = None) -> str:
    config = load_retrieval_config(project_root)
    embedding = describe_embedding_config(config.embedding_config)
    return f"{config.mode.upper()} | vector SQLite | embedding {embedding}"


def load_retrieval_config(project_root: Path | None = None) -> RetrievalConfig:
    root = project_root or Path.cwd()
    dotenv_values = _read_dotenv(root / ".env")

    def get_value(name: str, default: str = "") -> str:
        return os.environ.get(name) or dotenv_values.get(name) or default

    embedding_config = load_embedding_config(root)
    vector_db_path = Path(
        get_value("VECTOR_DB_PATH", str(root / "data" / "knowledge.sqlite"))
    )
    if not vector_db_path.is_absolute():
        vector_db_path = root / vector_db_path

    bm25_weight = _as_float(get_value("HYBRID_BM25_WEIGHT", "0.7"), default=0.7)
    vector_weight = _as_float(get_value("HYBRID_VECTOR_WEIGHT", "0.3"), default=0.3)
    if bm25_weight <= 0 and vector_weight <= 0:
        bm25_weight, vector_weight = 0.7, 0.3

    return RetrievalConfig(
        mode=get_value("RETRIEVAL_MODE", "hybrid").strip().lower() or "hybrid",
        bm25_weight=bm25_weight,
        vector_weight=vector_weight,
        vector_min_score=_as_float(
            get_value("VECTOR_MIN_SCORE", "0.05"),
            default=0.05,
        ),
        vector_top_k_multiplier=_as_int(
            get_value("VECTOR_TOP_K_MULTIPLIER", "3"),
            default=3,
        ),
        allow_vector_only_matches=_as_bool(
            get_value("HYBRID_ALLOW_VECTOR_ONLY", "false"),
            default=False,
        ),
        vector_db_path=vector_db_path,
        embedding_config=embedding_config,
    )


def _merge_rankings(
    *,
    bm25_results: list[SearchResult],
    vector_results: list[SearchResult],
    bm25_weight: float,
    vector_weight: float,
    allow_vector_only_matches: bool,
    doc_type: str | None,
) -> list[SearchResult]:
    by_id: dict[str, dict[str, object]] = {}
    max_bm25 = max((result.score for result in bm25_results), default=0.0) or 1.0
    max_vector = max((result.score for result in vector_results), default=0.0) or 1.0

    for result in bm25_results:
        by_id[result.document.id] = {
            "document": result.document,
            "matched_terms": list(result.matched_terms),
            "bm25_score": result.score,
            "vector_score": 0.0,
        }

    for result in vector_results:
        if not allow_vector_only_matches and result.document.id not in by_id:
            continue
        item = by_id.setdefault(
            result.document.id,
            {
                "document": result.document,
                "matched_terms": [],
                "bm25_score": 0.0,
                "vector_score": 0.0,
            },
        )
        item["vector_score"] = result.score
        matched_terms = item["matched_terms"]
        if isinstance(matched_terms, list) and "semantic" not in matched_terms:
            matched_terms.append("semantic")

    merged: list[SearchResult] = []
    for item in by_id.values():
        document = item["document"]
        bm25_score = float(item["bm25_score"])
        vector_score = float(item["vector_score"])
        normalized_bm25 = bm25_score / max_bm25 if bm25_score else 0.0
        normalized_vector = vector_score / max_vector if vector_score else 0.0
        combined_score = (
            bm25_weight * normalized_bm25 + vector_weight * normalized_vector
        ) / max(bm25_weight + vector_weight, 0.0001)
        if bm25_score and vector_score:
            retrieval_method = "hybrid"
        elif vector_score:
            retrieval_method = "vector"
        else:
            retrieval_method = "bm25"
        merged.append(
            SearchResult(
                document=document,
                score=combined_score,
                matched_terms=sorted(set(item["matched_terms"])),
                retrieval_method=retrieval_method,
                bm25_score=bm25_score,
                vector_score=vector_score,
            )
        )

    merged.sort(
        key=lambda result: (
            result.score,
            result.document.doc_type == doc_type if doc_type else False,
            result.vector_score,
            result.bm25_score,
            result.document.title,
        ),
        reverse=True,
    )
    return merged


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _as_float(value: str, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: str, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: str, *, default: bool) -> bool:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _count_terms(document: Document) -> Counter[str]:
    search_text = " ".join(
        [
            document.title,
            document.title,
            document.doc_type,
            document.doc_type,
            document.source,
            document.content,
        ]
    )
    return Counter(tokenize_sequence(search_text))
