from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from src.documents import Document


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
) -> list[SearchResult]:
    retriever = BM25Retriever(documents)
    return retriever.search(
        query,
        doc_type=doc_type,
        top_k=top_k,
        min_score=min_score,
    )


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
