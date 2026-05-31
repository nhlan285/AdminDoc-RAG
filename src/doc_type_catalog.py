from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.slot_normalizer import normalize_slots


CATALOG_DIR = Path(__file__).resolve().parents[1] / "data" / "doc_types"


@dataclass(frozen=True)
class DocTypeSpec:
    id: str
    name: str
    aliases: list[str] = field(default_factory=list)
    intents: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    required_slots: list[str] = field(default_factory=list)
    optional_slots: list[str] = field(default_factory=list)
    retrieval_doc_types: list[str] = field(default_factory=list)
    required_sections: list[str] = field(default_factory=list)
    template_lines: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocTypeSpec":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            aliases=[str(value) for value in data.get("aliases", [])],
            intents=[str(value) for value in data.get("intents", [])],
            examples=[str(value) for value in data.get("examples", [])],
            required_slots=[str(value) for value in data.get("required_slots", [])],
            optional_slots=[str(value) for value in data.get("optional_slots", [])],
            retrieval_doc_types=[
                str(value) for value in data.get("retrieval_doc_types", [])
            ],
            required_sections=[
                str(value) for value in data.get("required_sections", [])
            ],
            template_lines=[str(value) for value in data.get("template_lines", [])],
        )


@dataclass(frozen=True)
class RouteResult:
    doc_type: str
    intent: str
    confidence: float
    spec: DocTypeSpec | None = None


@lru_cache(maxsize=1)
def load_doc_type_specs() -> tuple[DocTypeSpec, ...]:
    if not CATALOG_DIR.exists():
        return ()

    specs: list[DocTypeSpec] = []
    for path in sorted(CATALOG_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
        raw_specs = raw_data if isinstance(raw_data, list) else [raw_data]
        for raw_spec in raw_specs:
            specs.append(DocTypeSpec.from_dict(raw_spec))
    return tuple(specs)


def get_doc_type_spec(doc_type: str) -> DocTypeSpec | None:
    normalized = _normalize(doc_type)
    for spec in load_doc_type_specs():
        names = [spec.name, *spec.retrieval_doc_types, *spec.aliases]
        if normalized in {_normalize(name) for name in names}:
            return spec
    return None


def route_doc_type(request: str, *, default_doc_type: str = "Công văn") -> RouteResult:
    normalized_request = _normalize(request)
    best_spec: DocTypeSpec | None = None
    best_score = 0.0

    for spec in load_doc_type_specs():
        score = _score_spec(normalized_request, spec)
        if score > best_score:
            best_score = score
            best_spec = spec

    if not best_spec or best_score <= 0:
        return RouteResult(
            doc_type=default_doc_type,
            intent="soan_thao",
            confidence=0.35,
            spec=get_doc_type_spec(default_doc_type),
        )

    confidence = min(0.97, 0.45 + best_score * 0.1)
    intent = best_spec.intents[0] if best_spec.intents else best_spec.id
    return RouteResult(
        doc_type=best_spec.name,
        intent=intent,
        confidence=confidence,
        spec=best_spec,
    )


def missing_required_slots(doc_type: str, slots: dict[str, str]) -> list[str]:
    spec = get_doc_type_spec(doc_type)
    if not spec:
        return []
    return [slot for slot in spec.required_slots if not slots.get(slot)]


def required_sections(doc_type: str) -> list[str]:
    spec = get_doc_type_spec(doc_type)
    return list(spec.required_sections) if spec else []


def retrieval_doc_types(doc_type: str) -> list[str]:
    spec = get_doc_type_spec(doc_type)
    if not spec:
        return [doc_type]
    return spec.retrieval_doc_types or [spec.name]


def render_template_draft(
    *,
    doc_type: str,
    topic: str,
    today: date,
    citations: list[Any],
    slots: dict[str, str] | None = None,
    agency_parent: str = "[TÊN CƠ QUAN CHỦ QUẢN]",
    agency_name: str = "[TÊN CƠ QUAN BAN HÀNH]",
    place_name: str = "[Địa danh]",
) -> str | None:
    spec = get_doc_type_spec(doc_type)
    if not spec or not spec.template_lines:
        return None

    context = _build_template_context(
        spec=spec,
        topic=topic,
        today=today,
        citations=citations,
        slots=normalize_slots(spec.name, slots or {}),
        agency_parent=agency_parent,
        agency_name=agency_name,
        place_name=place_name,
    )
    template = "\n".join(spec.template_lines)
    return _replace_placeholders(template, context)


def _score_spec(normalized_request: str, spec: DocTypeSpec) -> float:
    score = 0.0
    name = _normalize(spec.name)
    if name in normalized_request:
        score += 4.0

    for alias in spec.aliases:
        normalized_alias = _normalize(alias)
        if normalized_alias and normalized_alias in normalized_request:
            score += 2.8

    for intent in spec.intents:
        normalized_intent = _normalize(intent.replace("_", " "))
        if normalized_intent and normalized_intent in normalized_request:
            score += 1.2

    request_terms = set(_tokens(normalized_request))
    for example in spec.examples:
        example_terms = set(_tokens(_normalize(example)))
        if not example_terms:
            continue
        overlap = request_terms.intersection(example_terms)
        if len(overlap) >= 2:
            score += min(2.0, len(overlap) / max(len(example_terms), 1) * 3.0)

    return score


def _build_template_context(
    *,
    spec: DocTypeSpec,
    topic: str,
    today: date,
    citations: list[Any],
    slots: dict[str, str],
    agency_parent: str,
    agency_name: str,
    place_name: str,
) -> dict[str, str]:
    context = {
        "agency_parent": agency_parent,
        "agency_name": agency_name,
        "place_name": place_name,
        "day": f"{today.day:02d}",
        "month": f"{today.month:02d}",
        "year": str(today.year),
        "topic": topic,
        "source_marks": _source_marks(citations),
        "references": _references(citations),
        "quality_note": (
            "Ghi chú kiểm soát: Đây là bản nháp hỗ trợ soạn thảo tự động. "
            "Người dùng bắt buộc rà soát thể thức, thẩm quyền, số liệu và tính "
            "pháp lý trước khi ban hành."
        ),
    }

    for slot in [*spec.required_slots, *spec.optional_slots]:
        context[slot] = slots.get(slot) or _placeholder_for_slot(slot)

    return context


def _replace_placeholders(template: str, context: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group("key").strip()
        return context.get(key, f"[{key}]")

    return re.sub(r"\{\{\s*(?P<key>[a-zA-Z0-9_]+)\s*\}\}", replace, template)


def _source_marks(citations: list[Any]) -> str:
    markers = [f"[{getattr(citation, 'marker', '')}]" for citation in citations]
    markers = [marker for marker in markers if marker != "[]"]
    return ", ".join(markers) if markers else "[chưa có nguồn truy xuất]"


def _references(citations: list[Any]) -> str:
    lines = ["Nguồn tham khảo:"]
    if not citations:
        lines.append("- [Chưa có nguồn phù hợp trong kho tri thức]")
        return "\n".join(lines)

    for citation in citations:
        lines.append(
            "- [{marker}] {title} ({source}) - {excerpt}".format(
                marker=getattr(citation, "marker", "?"),
                title=getattr(citation, "title", "[Không rõ tiêu đề]"),
                source=getattr(citation, "source", "[Không rõ nguồn]"),
                excerpt=getattr(citation, "excerpt", ""),
            )
        )
    return "\n".join(lines)


def _placeholder_for_slot(slot: str) -> str:
    labels = {
        "subject_name": "[Họ và tên người liên quan]",
        "leave_days": "[Số ngày]",
        "start_date": "[Ngày bắt đầu]",
        "end_date": "[Ngày kết thúc]",
        "reason": "[Lý do]",
        "position": "[Chức vụ/đơn vị công tác]",
        "department": "[Đơn vị công tác]",
        "handover_person": "[Người nhận bàn giao]",
        "recipient": "[Tên cơ quan/đơn vị/cá nhân nhận]",
        "contact_person": "[Đầu mối tiếp nhận]",
        "event_time": "[Thời gian]",
        "event_location": "[Địa điểm]",
        "participants": "[Thành phần tham dự]",
        "approval_target": "[Cơ quan/người có thẩm quyền phê duyệt]",
        "scope": "[Phạm vi thực hiện]",
        "budget": "[Kinh phí/nguồn lực]",
        "timeline": "[Tiến độ thực hiện]",
        "legal_basis": "[Căn cứ pháp lý]",
        "responsible_unit": "[Đơn vị tham mưu/chịu trách nhiệm]",
        "effective_date": "[Ngày ký]",
        "urgency": "[Mức độ khẩn]",
        "deadline": "[Thời hạn thực hiện/báo cáo]",
        "invitee": "[Cơ quan/đơn vị/cá nhân được mời]",
        "event_name": "[Tên cuộc họp/sự kiện]",
        "chairperson": "[Người chủ trì]",
        "secretary": "[Thư ký]",
        "destination": "[Cơ quan/đơn vị đến làm việc]",
        "purpose": "[Mục đích làm việc]",
        "valid_until": "[Ngày hết hiệu lực]",
        "conclusion": "[Kết luận cuộc họp/làm việc]",
        "topic": "[Nội dung chính]",
    }
    return labels.get(slot, f"[{slot}]")


def _tokens(normalized_text: str) -> list[str]:
    return [token for token in re.findall(r"\w+", normalized_text) if len(token) > 1]


def _normalize(text: str) -> str:
    text = text.lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return unicodedata.normalize("NFC", text)
