from __future__ import annotations

import re
from dataclasses import dataclass

from src.doc_type_catalog import required_sections
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
    checks.extend(_form_consistency_checks(draft, doc_type))
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


def _form_consistency_checks(draft: str, doc_type: str) -> list[QualityCheck]:
    text = draft.lower()
    duplicated_time_prefix = re.search(
        r"\b(từ|đến|kể từ)\s+(từ|đến|kể từ|ngày)\s+ngày\b",
        text,
    ) or re.search(r"\b(từ|đến|kể từ)\s+\1\b", text)
    slash_dates = re.findall(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", draft)
    non_standard_dates = [
        value
        for value in slash_dates
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", value)
    ]
    checks = [
        QualityCheck(
            name="Cụm thời gian không lặp",
            passed=not duplicated_time_prefix,
            severity="medium",
            message=(
                "Không phát hiện cụm thời gian bị lặp."
                if not duplicated_time_prefix
                else "Có cụm thời gian bị lặp như 'từ từ ngày' hoặc 'đến đến ngày'."
            ),
        ),
        QualityCheck(
            name="Định dạng ngày nhập liệu",
            passed=not non_standard_dates,
            severity="medium",
            message=(
                "Các ngày dạng số đã theo dd/mm/yyyy."
                if not non_standard_dates
                else "Ngày chưa thống nhất định dạng dd/mm/yyyy: "
                + ", ".join(sorted(set(non_standard_dates)))
            ),
        ),
        QualityCheck(
            name="Placeholder template",
            passed="{{" not in draft and "}}" not in draft,
            severity="high",
            message="Không còn placeholder template dạng {{...}}.",
        ),
    ]

    if doc_type == "Giấy nghỉ phép":
        leave_line = _find_line(draft, "Được nghỉ phép trong thời gian")
        has_duration_and_start = bool(
            re.search(r"\d+\s+ngày", leave_line)
            and re.search(r"từ\s+\d{2}/\d{2}/\d{4}", leave_line.lower())
        )
        checks.append(
            QualityCheck(
                name="Ngày kết thúc nghỉ phép",
                passed=not has_duration_and_start or "[Ngày kết thúc]" not in leave_line,
                severity="medium",
                message=(
                    "Ngày kết thúc nghỉ phép đã được điền hoặc chưa đủ dữ kiện để suy ra."
                    if not has_duration_and_start or "[Ngày kết thúc]" not in leave_line
                    else "Có ngày bắt đầu và số ngày nghỉ nhưng ngày kết thúc vẫn là placeholder."
                ),
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


def _find_line(text: str, fragment: str) -> str:
    fragment_lower = fragment.lower()
    for line in text.splitlines():
        if fragment_lower in line.lower():
            return line
    return ""

def _required_fragments(doc_type: str) -> list[str]:
    catalog_sections = required_sections(doc_type)
    if catalog_sections:
        return catalog_sections

    # Quốc hiệu & Tiêu ngữ là bắt buộc với hầu hết văn bản hành chính (NĐ 30)
    base_requirements = [
        "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", 
        "Độc lập - Tự do - Hạnh phúc",
        "Nơi nhận:"
    ]
    
    if doc_type == "Công văn":
        return base_requirements + ["Kính gửi:"]
    if doc_type == "Thông báo":
        return base_requirements + ["THÔNG BÁO"]
    if doc_type == "Tờ trình":
        return base_requirements + ["TỜ TRÌNH", "Kính gửi:", "Kiến nghị"]
    if doc_type in {"Quyết định", "Quyết định hành chính đơn giản"}:
        return base_requirements + ["QUYẾT ĐỊNH", "Điều 1.", "Điều 2.", "Điều 3."]
        
    return base_requirements

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
