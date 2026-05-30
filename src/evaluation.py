from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.documents import Document
from src.extractor import analyze_request
from src.generator import build_draft
from src.quality import evaluate_draft
from src.retriever import retrieve


@dataclass(frozen=True)
class RetrievalTestCase:
    id: str
    query: str
    doc_type: str | None
    expected_parent_id: str
    description: str

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "RetrievalTestCase":
        return cls(
            id=str(item["id"]),
            query=str(item["query"]),
            doc_type=item.get("doc_type"),
            expected_parent_id=str(item["expected_parent_id"]),
            description=str(item.get("description", "")),
        )


@dataclass(frozen=True)
class GenerationTestCase:
    id: str
    query: str
    doc_type: str
    expected_fragments: list[str]
    forbidden_fragments: list[str]
    description: str

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "GenerationTestCase":
        return cls(
            id=str(item["id"]),
            query=str(item["query"]),
            doc_type=str(item["doc_type"]),
            expected_fragments=[str(value) for value in item["expected_fragments"]],
            forbidden_fragments=[
                str(value) for value in item.get("forbidden_fragments", [])
            ],
            description=str(item.get("description", "")),
        )


@dataclass(frozen=True)
class ExtractionTestCase:
    id: str
    query: str
    default_doc_type: str
    expected_doc_type: str
    expected_slots: dict[str, str]
    description: str

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "ExtractionTestCase":
        return cls(
            id=str(item["id"]),
            query=str(item["query"]),
            default_doc_type=str(item.get("default_doc_type") or "Công văn"),
            expected_doc_type=str(item["expected_doc_type"]),
            expected_slots={
                str(key): str(value)
                for key, value in item.get("expected_slots", {}).items()
            },
            description=str(item.get("description", "")),
        )


def load_retrieval_test_cases(path: Path) -> list[RetrievalTestCase]:
    with path.open("r", encoding="utf-8") as file:
        raw_cases = json.load(file)

    return [RetrievalTestCase.from_dict(item) for item in raw_cases]


def load_generation_test_cases(path: Path) -> list[GenerationTestCase]:
    with path.open("r", encoding="utf-8") as file:
        raw_cases = json.load(file)

    return [GenerationTestCase.from_dict(item) for item in raw_cases]


def load_extraction_test_cases(path: Path) -> list[ExtractionTestCase]:
    with path.open("r", encoding="utf-8") as file:
        raw_cases = json.load(file)

    return [ExtractionTestCase.from_dict(item) for item in raw_cases]


def run_extraction_tests(
    test_cases: list[ExtractionTestCase],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for test_case in test_cases:
        analysis = analyze_request(
            test_case.query,
            default_doc_type=test_case.default_doc_type,
        )
        missing_slots = [
            f"{key}={expected}"
            for key, expected in test_case.expected_slots.items()
            if str(analysis.slots.get(key, "")) != expected
        ]
        passed = (
            analysis.detected_doc_type == test_case.expected_doc_type
            and not missing_slots
        )
        rows.append(
            {
                "id": test_case.id,
                "passed": passed,
                "query": test_case.query,
                "expected_doc_type": test_case.expected_doc_type,
                "detected_doc_type": analysis.detected_doc_type,
                "missing_slots": ", ".join(missing_slots),
                "confidence": round(analysis.confidence, 2),
                "description": test_case.description,
            }
        )

    return rows


def run_retrieval_tests(
    test_cases: list[RetrievalTestCase],
    documents: list[Document],
    *,
    top_k: int = 3,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for test_case in test_cases:
        results = retrieve(
            test_case.query,
            documents,
            doc_type=test_case.doc_type,
            top_k=top_k,
        )
        returned_parent_ids = [
            result.document.parent_id or result.document.id for result in results
        ]
        top_result = results[0] if results else None
        passed = test_case.expected_parent_id in returned_parent_ids

        rows.append(
            {
                "id": test_case.id,
                "passed": passed,
                "query": test_case.query,
                "doc_type": test_case.doc_type or "Không lọc",
                "expected": test_case.expected_parent_id,
                "top_result": (
                    top_result.document.parent_id or top_result.document.id
                    if top_result
                    else "Không có kết quả"
                ),
                "top_score": round(top_result.score, 3) if top_result else 0.0,
                "matched_terms": (
                    ", ".join(top_result.matched_terms) if top_result else ""
                ),
                "description": test_case.description,
            }
        )

    return rows


def run_generation_tests(
    test_cases: list[GenerationTestCase],
    documents: list[Document],
    *,
    top_k: int = 3,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for test_case in test_cases:
        results = retrieve(
            test_case.query,
            documents,
            doc_type=test_case.doc_type,
            top_k=top_k,
        )
        draft = build_draft(test_case.query, test_case.doc_type, results)

        missing_fragments = [
            fragment
            for fragment in test_case.expected_fragments
            if fragment not in draft
        ]
        forbidden_hits = [
            fragment
            for fragment in test_case.forbidden_fragments
            if fragment in draft
        ]
        passed = not missing_fragments and not forbidden_hits

        rows.append(
            {
                "id": test_case.id,
                "passed": passed,
                "doc_type": test_case.doc_type,
                "sources": len(results),
                "missing": ", ".join(missing_fragments),
                "forbidden_hits": ", ".join(forbidden_hits),
                "description": test_case.description,
            }
        )

    return rows


def run_quality_tests(
    test_cases: list[GenerationTestCase],
    documents: list[Document],
    *,
    top_k: int = 3,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for test_case in test_cases:
        results = retrieve(
            test_case.query,
            documents,
            doc_type=test_case.doc_type,
            top_k=top_k,
        )
        draft = build_draft(test_case.query, test_case.doc_type, results)
        report = evaluate_draft(
            draft=draft,
            doc_type=test_case.doc_type,
            search_results=results,
        )
        failed_checks = [
            check.name for check in report.checks if not check.passed
        ]
        expected_no_source = any(
            "CHƯA ĐỦ NGUỒN KIỂM CHỨNG" in fragment
            for fragment in test_case.expected_fragments
        )
        passed = (
            report.risk_level == "Cao"
            if expected_no_source
            else report.risk_level in {"Thấp", "Trung bình"}
        )

        rows.append(
            {
                "id": test_case.id,
                "passed": passed,
                "doc_type": test_case.doc_type,
                "risk_level": report.risk_level,
                "score": report.score,
                "failed_checks": ", ".join(failed_checks),
                "description": test_case.description,
            }
        )

    return rows
