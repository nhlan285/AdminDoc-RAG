from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RequestAnalysis:
    original_request: str
    detected_doc_type: str
    intent: str
    confidence: float
    slots: dict[str, str] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    retrieval_query: str = ""
    notes: list[str] = field(default_factory=list)


DOC_TYPE_RULES: list[tuple[str, str, list[str]]] = [
    ("Giấy nghỉ phép", "xin_nghi_phep", ["xin nghi", "nghi phep", "nghi lam", "don xin nghi"]),
    ("Giấy mời", "moi_hop", ["giay moi", "moi tham du", "moi hop", "hoi nghi", "tap huan"]),
    ("Giấy giới thiệu", "gioi_thieu", ["giay gioi thieu", "gioi thieu", "cu den", "den lam viec"]),
    ("Công điện", "cong_dien", ["cong dien", "khan", "hoa toc"]),
    ("Biên bản", "lap_bien_ban", ["bien ban", "lap bien ban", "cuoc hop"]),
    ("Thông báo", "thong_bao", ["thong bao"]),
    ("Tờ trình", "to_trinh", ["to trinh", "phe duyet", "trinh phe duyet", "kien nghi phe duyet"]),
    ("Quyết định hành chính đơn giản", "quyet_dinh", ["quyet dinh", "thanh lap", "bo nhiem", "ban hanh"]),
    ("Công văn", "cong_van", ["cong van", "de nghi", "yeu cau", "phoi hop"]),
]

REQUIRED_SLOTS: dict[str, list[str]] = {
    "Giấy nghỉ phép": ["subject_name", "leave_days", "start_date", "reason"],
    "Giấy mời": ["invitee", "event_name", "event_time", "event_location"],
    "Giấy giới thiệu": ["subject_name", "destination", "purpose"],
    "Công văn": ["topic", "recipient"],
    "Thông báo": ["topic"],
    "Tờ trình": ["topic", "approval_target"],
    "Quyết định hành chính đơn giản": ["topic"],
}


def analyze_request(request: str, *, default_doc_type: str = "Công văn") -> RequestAnalysis:
    text = " ".join(request.strip().split())
    normalized = _normalize_for_rules(text)
    detected_doc_type, intent, confidence = _detect_doc_type(normalized, default_doc_type)
    slots = _extract_common_slots(text, normalized)

    if detected_doc_type == "Giấy nghỉ phép":
        slots.update(_extract_leave_slots(text, normalized))
    elif detected_doc_type == "Giấy mời":
        slots.update(_extract_invitation_slots(text, normalized))
    elif detected_doc_type == "Giấy giới thiệu":
        slots.update(_extract_introduction_slots(text, normalized))

    slots.setdefault("topic", _extract_topic(text, detected_doc_type))
    missing_fields = [
        name
        for name in REQUIRED_SLOTS.get(detected_doc_type, [])
        if not slots.get(name)
    ]
    retrieval_query = _build_retrieval_query(
        original_request=text,
        detected_doc_type=detected_doc_type,
        intent=intent,
        slots=slots,
    )
    notes = _build_notes(detected_doc_type, missing_fields)
    return RequestAnalysis(
        original_request=text,
        detected_doc_type=detected_doc_type,
        intent=intent,
        confidence=confidence,
        slots=slots,
        missing_fields=missing_fields,
        retrieval_query=retrieval_query,
        notes=notes,
    )


def analysis_to_rows(analysis: RequestAnalysis) -> list[dict[str, str]]:
    rows = [
        {"Trường": "Loại văn bản nhận diện", "Giá trị": analysis.detected_doc_type},
        {"Trường": "Ý định", "Giá trị": analysis.intent},
        {"Trường": "Độ tin cậy", "Giá trị": f"{analysis.confidence:.2f}"},
    ]
    for key, value in analysis.slots.items():
        if value:
            rows.append({"Trường": key, "Giá trị": str(value)})
    if analysis.missing_fields:
        rows.append({"Trường": "Thiếu thông tin", "Giá trị": ", ".join(analysis.missing_fields)})
    return rows


def _detect_doc_type(normalized: str, default_doc_type: str) -> tuple[str, str, float]:
    explicit_prefixes = [
        ("giay nghi phep", "Giấy nghỉ phép", "xin_nghi_phep"),
        ("giay moi", "Giấy mời", "moi_hop"),
        ("giay gioi thieu", "Giấy giới thiệu", "gioi_thieu"),
        ("cong dien", "Công điện", "cong_dien"),
        ("bien ban", "Biên bản", "lap_bien_ban"),
        ("thong bao", "Thông báo", "thong_bao"),
        ("to trinh", "Tờ trình", "to_trinh"),
        ("quyet dinh", "Quyết định hành chính đơn giản", "quyet_dinh"),
        ("cong van", "Công văn", "cong_van"),
    ]
    for prefix, doc_type, intent in explicit_prefixes:
        if normalized.startswith(prefix):
            return doc_type, intent, 0.95

    best_doc_type = default_doc_type
    best_intent = "soan_thao"
    best_hits = 0
    for doc_type, intent, keywords in DOC_TYPE_RULES:
        hits = sum(1 for keyword in keywords if keyword in normalized)
        if hits > best_hits:
            best_doc_type = doc_type
            best_intent = intent
            best_hits = hits

    if best_hits:
        confidence = min(0.95, 0.55 + best_hits * 0.18)
        return best_doc_type, best_intent, confidence

    return default_doc_type, "soan_thao", 0.35


def _extract_common_slots(text: str, normalized: str) -> dict[str, str]:
    slots: dict[str, str] = {}
    recipient = _match_after_label(text, ["kính gửi", "gui", "gửi"])
    if recipient:
        slots["recipient"] = recipient

    date_match = re.search(r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)", text)
    if date_match:
        slots["date"] = date_match.group(1)

    if "phe duyet" in normalized:
        slots["approval_target"] = _extract_after_phrase(text, ["phê duyệt", "phe duyet"])

    return slots


def _extract_leave_slots(text: str, normalized: str) -> dict[str, str]:
    slots: dict[str, str] = {}
    name_match = re.search(
        r"^(?P<name>[A-Za-zÀ-ỹ][A-Za-zÀ-ỹ\s]{1,60}?)\s+(?:xin|muốn|muon|đề nghị|de nghi)\s+nghỉ",
        text,
        flags=re.IGNORECASE,
    )
    if name_match:
        name = _clean_slot(name_match.group("name"))
        if _normalize_for_rules(name) not in {"toi", "em", "minh"}:
            slots["subject_name"] = name

    alt_name_match = re.search(
        r"(?:cho|cấp cho|cap cho)\s+(?P<name>[A-Za-zÀ-ỹ][A-Za-zÀ-ỹ\s]{1,60}?)\s+nghỉ",
        text,
        flags=re.IGNORECASE,
    )
    if alt_name_match and not slots.get("subject_name"):
        slots["subject_name"] = _clean_slot(alt_name_match.group("name"))

    days_match = re.search(r"(\d+)\s*(?:ngày|ngay|buổi|buoi)", normalized)
    if days_match:
        slots["leave_days"] = days_match.group(1)

    range_match = re.search(
        r"từ\s+ngày\s+(?P<start>[^,;.]+?)\s+(?:đến|den)\s+ngày\s+(?P<end>[^,;.]+)",
        text,
        flags=re.IGNORECASE,
    )
    if range_match:
        slots["start_date"] = _clean_slot(range_match.group("start"))
        slots["end_date"] = _clean_slot(range_match.group("end"))

    reason = _extract_after_phrase(text, ["vì", "do", "lý do", "ly do"])
    if reason:
        slots["reason"] = reason

    return slots


def _extract_invitation_slots(text: str, normalized: str) -> dict[str, str]:
    slots: dict[str, str] = {}
    invitee = _match_after_label(text, ["mời", "moi", "kính mời"])
    if invitee:
        slots["invitee"] = invitee
    if "tap huan" in normalized:
        slots["event_name"] = "Tập huấn"
    elif "hoi nghi" in normalized:
        slots["event_name"] = "Hội nghị"
    time_value = _extract_after_phrase(text, ["vào lúc", "luc", "thời gian", "thoi gian"])
    if time_value:
        slots["event_time"] = time_value
    location = _extract_after_phrase(text, ["tại", "tai", "địa điểm", "dia diem"])
    if location:
        slots["event_location"] = location
    return slots


def _extract_introduction_slots(text: str, normalized: str) -> dict[str, str]:
    slots: dict[str, str] = {}
    name = _extract_after_phrase(text, ["giới thiệu", "gioi thieu", "cử", "cu"])
    if name:
        slots["subject_name"] = name
    destination = _extract_after_phrase(text, ["đến", "den", "tới", "toi"])
    if destination:
        slots["destination"] = destination
    purpose = _extract_after_phrase(text, ["về việc", "ve viec", "để", "de"])
    if purpose:
        slots["purpose"] = purpose
    return slots


def _extract_topic(text: str, detected_doc_type: str) -> str:
    normalized = " ".join(text.strip().split())
    prefixes = [
        "soạn",
        "tạo",
        "lập",
        detected_doc_type,
        "công văn",
        "thông báo",
        "tờ trình",
        "quyết định",
        "giấy nghỉ phép",
        "giấy mời",
    ]
    lowered = normalized.lower()
    for prefix in prefixes:
        prefix_lower = prefix.lower()
        if lowered.startswith(prefix_lower):
            normalized = normalized[len(prefix):].strip(" :.-")
            lowered = normalized.lower()
    return normalized[:160] or detected_doc_type


def _match_after_label(text: str, labels: list[str]) -> str:
    for label in labels:
        value = _extract_after_phrase(text, [label])
        if value:
            return value
    return ""


def _extract_after_phrase(text: str, phrases: list[str]) -> str:
    for phrase in phrases:
        pattern = re.compile(rf"{re.escape(phrase)}\s*:?\s*(?P<value>[^.;,\n]+)", flags=re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return _clean_slot(match.group("value"))
    return ""


def _build_retrieval_query(
    *,
    original_request: str,
    detected_doc_type: str,
    intent: str,
    slots: dict[str, str],
) -> str:
    slot_text = " ".join(str(value) for value in slots.values() if value)
    intent_text = intent.replace("_", " ")
    return " ".join([detected_doc_type, intent_text, slot_text, original_request]).strip()


def _build_notes(doc_type: str, missing_fields: list[str]) -> list[str]:
    notes = [f"Hệ thống sẽ ưu tiên mẫu {doc_type} khi truy xuất."]
    if missing_fields:
        notes.append("Các trường thiếu sẽ được giữ bằng placeholder để người dùng bổ sung.")
    return notes


def _clean_slot(value: str) -> str:
    return " ".join(value.strip(" :.-\t\n\r").split())


def _normalize_for_rules(text: str) -> str:
    text = text.lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return unicodedata.normalize("NFC", text)
