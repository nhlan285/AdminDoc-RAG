from __future__ import annotations

import re
from dataclasses import dataclass

from src.retriever import SearchResult


@dataclass(frozen=True)
class QualityCheck:
    name: str
    passed: bool
    severity: str
    message: str


@dataclass(frozen=True)
class QualityReport:
    risk_level: str
    score: int
    checks: list[QualityCheck]


def evaluate_draft(
    *,
    draft: str,
    doc_type: str,
    search_results: list[SearchResult],
) -> QualityReport:
    checks: list[QualityCheck] = []
    checks.extend(_format_checks(draft, doc_type))
    checks.extend(_citation_checks(draft, search_results))
    checks.extend(_hallucination_checks(draft, search_results))
    checks.append(_human_review_check(draft))

    score = _calculate_score(checks)
    risk_level = _risk_level(score, checks)
    return QualityReport(risk_level=risk_level, score=score, checks=checks)


def report_to_rows(report: QualityReport) -> list[dict[str, object]]:
    return [
        {
            "status": "Đạt" if check.passed else "Cần kiểm tra",
            "severity": check.severity,
            "check": check.name,
            "message": check.message,
        }
        for check in report.checks
    ]


def _format_checks(draft: str, doc_type: str) -> list[QualityCheck]:
    text = draft.lower()
    checks = [
        QualityCheck(
            name="Quốc hiệu",
            passed="cộng hòa xã hội chủ nghĩa việt nam" in text,
            severity="high",
            message="Văn bản cần có quốc hiệu.",
        ),
        QualityCheck(
            name="Tiêu ngữ",
            passed="độc lập - tự do - hạnh phúc" in text,
            severity="high",
            message="Văn bản cần có tiêu ngữ.",
        ),
        QualityCheck(
            name="Ngày tháng",
            passed=bool(re.search(r"ngày\s+\d{2}\s+tháng\s+\d{2}\s+năm\s+\d{4}", text)),
            severity="medium",
            message="Văn bản cần có dòng ngày tháng theo mẫu.",
        ),
    ]

    required_fragments = _required_fragments(doc_type)
    for fragment in required_fragments:
        checks.append(
            QualityCheck(
                name=f"Thể thức {doc_type}",
                passed=fragment.lower() in text,
                severity="high",
                message=f"Cần có thành phần: {fragment}",
            )
        )

    return checks


def _citation_checks(
    draft: str,
    search_results: list[SearchResult],
) -> list[QualityCheck]:
    text = draft.lower()
    source_count = min(len(search_results), 3)

    if source_count == 0:
        return [
            QualityCheck(
                name="Nguồn truy xuất",
                passed=False,
                severity="high",
                message="Không có nguồn truy xuất phù hợp, rủi ro ảo giác cao.",
            ),
            QualityCheck(
                name="Cảnh báo thiếu nguồn",
                passed="chưa đủ nguồn kiểm chứng" in text,
                severity="high",
                message="Khi không có nguồn, bản nháp phải cảnh báo rõ.",
            ),
        ]

    checks = [
        QualityCheck(
            name="Nguồn truy xuất",
            passed=True,
            severity="high",
            message=f"Có {len(search_results)} nguồn truy xuất.",
        ),
        QualityCheck(
            name="Mục nguồn tham khảo",
            passed="nguồn tham khảo" in text,
            severity="high",
            message="Bản nháp cần có mục nguồn tham khảo.",
        ),
    ]

    for index in range(1, source_count + 1):
        marker = f"[s{index}]"
        checks.append(
            QualityCheck(
                name=f"Citation {marker.upper()}",
                passed=marker in text,
                severity="medium",
                message=f"Nội dung dùng nguồn {marker.upper()} cần có marker citation.",
            )
        )

    return checks


def _hallucination_checks(
    draft: str,
    search_results: list[SearchResult],
) -> list[QualityCheck]:
    source_text = " ".join(
        " ".join(
            [
                result.document.title,
                result.document.source,
                result.document.content,
            ]
        ).lower()
        for result in search_results
    )
    draft_lower = draft.lower()

    legal_reference_terms = [
        "luật ",
        "nghị định",
        "thông tư",
        "quyết định số",
        "điều khoản",
    ]
    unsupported_terms = [
        term
        for term in legal_reference_terms
        if term in draft_lower and term not in source_text
    ]

    return [
        QualityCheck(
            name="Căn cứ pháp lý không có trong nguồn",
            passed=not unsupported_terms,
            severity="high",
            message=(
                "Không phát hiện căn cứ pháp lý ngoài nguồn."
                if not unsupported_terms
                else "Có dấu hiệu dùng căn cứ ngoài nguồn: "
                + ", ".join(unsupported_terms)
            ),
        ),
        QualityCheck(
            name="Placeholder cần con người điền",
            passed="[" in draft and "]" in draft,
            severity="low",
            message="Các thông tin chưa chắc chắn nên được để placeholder cho người dùng rà soát.",
        ),
    ]


def _human_review_check(draft: str) -> QualityCheck:
    text = draft.lower()
    has_review_note = "rà soát" in text or "kiểm chứng" in text
    return QualityCheck(
        name="Human-in-the-loop",
        passed=has_review_note,
        severity="medium",
        message="Bản nháp cần nhắc người dùng rà soát trước khi sử dụng.",
    )


def _required_fragments(doc_type: str) -> list[str]:
    if doc_type == "Công văn":
        return ["Số:", "Kính gửi:", "Nơi nhận:"]
    if doc_type == "Thông báo":
        return ["THÔNG BÁO", "Nơi nhận:"]
    if doc_type == "Tờ trình":
        return ["TỜ TRÌNH", "Kính gửi:", "Kiến nghị"]
    if doc_type == "Quyết định hành chính đơn giản":
        return ["QUYẾT ĐỊNH", "Điều 1.", "Điều 2.", "Điều 3."]

    return ["Số:"]


def _calculate_score(checks: list[QualityCheck]) -> int:
    score = 100
    penalties = {"high": 25, "medium": 12, "low": 5}
    for check in checks:
        if not check.passed:
            score -= penalties.get(check.severity, 10)

    return max(0, min(100, score))


def _risk_level(score: int, checks: list[QualityCheck]) -> str:
    has_failed_high = any(
        check.severity == "high" and not check.passed for check in checks
    )
    if score < 60 or has_failed_high:
        return "Cao"
    if score < 85:
        return "Trung bình"

    return "Thấp"
