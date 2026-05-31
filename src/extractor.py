from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from src.doc_type_catalog import missing_required_slots, route_doc_type
from src.slot_normalizer import normalize_slots


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
    "Công điện": ["recipient", "topic"],
    "Biên bản": ["event_time", "event_location", "participants"],
}


def analyze_request(request: str, *, default_doc_type: str = "Công văn") -> RequestAnalysis:
    text = " ".join(request.strip().split())
    normalized = _normalize_for_rules(text)
    detected_doc_type, intent, confidence = _detect_doc_type(normalized, default_doc_type)
    routed = route_doc_type(text, default_doc_type=default_doc_type)
    if routed.confidence >= confidence:
        detected_doc_type = routed.doc_type
        intent = routed.intent
        confidence = routed.confidence
    slots = _extract_common_slots(text, normalized)

    if detected_doc_type == "Giấy nghỉ phép":
        slots.update(_extract_leave_slots(text, normalized))
    elif detected_doc_type == "Giấy mời":
        slots.update(_extract_invitation_slots(text, normalized))
    elif detected_doc_type == "Giấy giới thiệu":
        slots.update(_extract_introduction_slots(text, normalized))
    elif detected_doc_type == "Công điện":
        slots.update(_extract_dispatch_slots(text, normalized))
    elif detected_doc_type == "Biên bản":
        slots.update(_extract_minutes_slots(text, normalized))

    if detected_doc_type in {"Tờ trình", "Giấy mời"} and slots.get("recipient"):
        slots.setdefault("approval_target", slots["recipient"])
        slots.setdefault("invitee", slots["recipient"])

    slots.setdefault("topic", _extract_topic(text, detected_doc_type))
    slots = normalize_slots(detected_doc_type, slots)
    catalog_missing_fields = missing_required_slots(detected_doc_type, slots)
    fallback_missing_fields = [
        name
        for name in REQUIRED_SLOTS.get(detected_doc_type, [])
        if not slots.get(name)
    ]
    missing_fields = catalog_missing_fields or fallback_missing_fields
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
        ("quyet dinh truc tiep", "Quyết định", "quyet_dinh"),
        ("quyet dinh gian tiep", "Quyết định", "quyet_dinh"),
        ("quyet dinh ca biet", "Quyết định", "quyet_dinh"),
        ("quyet dinh ban hanh", "Quyết định", "quyet_dinh"),
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

    event_time = _extract_after_phrase(text, ["vào lúc", "luc", "thời gian", "thoi gian"])
    if event_time:
        slots["event_time"] = event_time

    event_location = _extract_after_phrase(text, ["tại", "tai", "địa điểm", "dia diem"])
    if event_location:
        slots["event_location"] = event_location

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
    event_topic_match = re.search(
        r"(?:dự|du|tham dự|tham du)\s+(?P<topic>.+?)(?:\s+(?:vào lúc|vao luc|thời gian|thoi gian|tại|tai)\s+|$)",
        text,
        flags=re.IGNORECASE,
    )
    if event_topic_match:
        slots["topic"] = _clean_slot(event_topic_match.group("topic"))
    if "tap huan" in normalized:
        slots["event_name"] = "Tập huấn"
    elif "hoi nghi" in normalized:
        slots["event_name"] = "Hội nghị"
    elif "hop" in normalized:
        slots["event_name"] = "Cuộc họp"
    time_value = _extract_after_phrase(text, ["vào lúc", "luc", "thời gian", "thoi gian"])
    if time_value:
        slots["event_time"] = time_value
    location = _extract_after_phrase(text, ["tại", "tai", "địa điểm", "dia diem"])
    if location:
        slots["event_location"] = location
    return slots


def _extract_introduction_slots(text: str, normalized: str) -> dict[str, str]:
    slots: dict[str, str] = {}
    name_match = re.search(
        r"(?:giới thiệu|gioi thieu|cử|cu)\s+(?P<name>.+?)\s+(?:đến|den|tới|toi)\s+",
        text,
        flags=re.IGNORECASE,
    )
    if name_match:
        slots["subject_name"] = _clean_slot(name_match.group("name"))
    else:
        name = _extract_after_phrase(text, ["giới thiệu", "gioi thieu", "cử", "cu"])
        if name:
            slots["subject_name"] = name

    destination_match = re.search(
        r"(?:đến|den|tới|toi)\s+(?P<destination>.+?)(?:\s+(?:để|de|về việc|ve viec)\s+|$)",
        text,
        flags=re.IGNORECASE,
    )
    if destination_match:
        slots["destination"] = _clean_slot(destination_match.group("destination"))

    purpose = _extract_after_phrase(text, ["để", "de", "về việc", "ve viec"])
    if purpose:
        slots["purpose"] = purpose
    return slots


def _extract_dispatch_slots(text: str, normalized: str) -> dict[str, str]:
    slots: dict[str, str] = {}
    if "hoa toc" in normalized:
        slots["urgency"] = "HỎA TỐC"
    elif "khan" in normalized:
        slots["urgency"] = "KHẨN"

    recipient = _match_after_label(text, ["kính gửi", "gui", "gửi"])
    if recipient:
        slots["recipient"] = recipient

    deadline = _extract_after_phrase(
        text,
        ["thời hạn", "thoi han", "trước", "truoc", "hoàn thành trước", "hoan thanh truoc"],
    )
    if deadline:
        slots["deadline"] = deadline

    responsible = _extract_after_phrase(
        text,
        ["đơn vị chịu trách nhiệm", "don vi chiu trach nhiem", "giao", "phân công", "phan cong"],
    )
    if responsible:
        slots["responsible_unit"] = responsible

    topic = _extract_topic_from_label(text)
    if topic:
        slots["topic"] = topic

    return slots


def _extract_minutes_slots(text: str, normalized: str) -> dict[str, str]:
    slots: dict[str, str] = {}
    participants = _extract_after_phrase(
        text,
        ["thành phần", "thanh phan", "thành phần tham dự", "thanh phan tham du"],
    )
    if participants:
        slots["participants"] = participants
    chairperson = _extract_after_phrase(text, ["chủ trì", "chu tri"])
    if chairperson:
        slots["chairperson"] = chairperson
    secretary = _extract_after_phrase(text, ["thư ký", "thu ky"])
    if secretary:
        slots["secretary"] = secretary
    conclusion = _extract_after_phrase(text, ["kết luận", "ket luan"])
    if conclusion:
        slots["conclusion"] = conclusion
    topic = _extract_topic_from_label(text)
    if topic:
        slots["topic"] = topic
    elif "hop" in normalized:
        slots["topic"] = _extract_topic(text, "Biên bản")
    return slots


def _extract_topic(text: str, detected_doc_type: str) -> str:
    labeled_topic = _extract_topic_from_label(text)
    if labeled_topic:
        return labeled_topic[:160]

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
        "giấy giới thiệu",
        "công điện",
        "biên bản",
        "cuộc họp",
        "họp",
    ]
    lowered = normalized.lower()
    for prefix in prefixes:
        prefix_lower = prefix.lower()
        if lowered.startswith(prefix_lower):
            normalized = normalized[len(prefix):].strip(" :.-")
            lowered = normalized.lower()
    normalized = _trim_topic_tail(normalized)
    return normalized[:160] or detected_doc_type


def _extract_topic_from_label(text: str) -> str:
    return _extract_after_phrase(text, ["về việc", "ve viec", "v/v", "nội dung", "noi dung"])


def _trim_topic_tail(value: str) -> str:
    normalized_value = value
    for phrase in [
        "kính gửi",
        "kinh gui",
        "vào lúc",
        "vao luc",
        "tại",
        "tai",
        "thành phần",
        "thanh phan",
        "thời hạn",
        "thoi han",
    ]:
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", flags=re.IGNORECASE)
        match = pattern.search(normalized_value)
        if match and match.start() > 0:
            normalized_value = normalized_value[: match.start()]
    return _clean_slot(normalized_value.rstrip(" ,;"))


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
