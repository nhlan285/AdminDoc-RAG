from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta


DATE_FIELDS = {
    "date",
    "start_date",
    "end_date",
    "event_date",
    "effective_date",
    "valid_until",
}


TEXT_DATE_FIELDS = {
    "deadline",
    "event_time",
    "timeline",
}


TRIM_BY_FIELD = {
    "recipient": ["về việc", "ve viec", "vào lúc", "vao luc", "thời gian", "thoi gian"],
    "invitee": ["về việc", "ve viec", "vào lúc", "vao luc", "dự", "du", "tham dự", "tham du"],
    "approval_target": ["về việc", "ve viec", "vào lúc", "vao luc"],
    "destination": ["để", "de", "về việc", "ve viec"],
    "event_time": ["tại", "tai", "địa điểm", "dia diem", "thành phần", "thanh phan"],
    "event_location": ["thành phần", "thanh phan", "chủ trì", "chu tri", "nội dung", "noi dung"],
    "participants": ["chủ trì", "chu tri", "thư ký", "thu ky", "nội dung", "noi dung"],
    "topic": ["kính gửi", "kinh gui", "vào lúc", "vao luc", "thành phần", "thanh phan", "thời hạn", "thoi han"],
    "purpose": ["thời hạn", "thoi han", "vào lúc", "vao luc"],
}


def normalize_slots(
    doc_type: str,
    slots: dict[str, str],
    *,
    reference_date: date | None = None,
) -> dict[str, str]:
    normalized = {
        key: _clean_value(value)
        for key, value in slots.items()
        if value is not None and str(value).strip()
    }
    reference = reference_date or date.today()

    for field in DATE_FIELDS.intersection(normalized):
        normalized[field] = normalize_date_value(normalized[field], reference_date=reference)

    for field in TEXT_DATE_FIELDS.intersection(normalized):
        normalized[field] = normalize_dates_in_text(
            _trim_field_value(field, normalized[field]),
            reference_date=reference,
        )

    for field in set(TRIM_BY_FIELD).intersection(normalized):
        normalized[field] = _trim_field_value(field, normalized[field])

    if normalized.get("deadline"):
        normalized["deadline"] = normalize_dates_in_text(
            normalized["deadline"],
            reference_date=reference,
        )

    if doc_type == "Giấy nghỉ phép":
        if not normalized.get("start_date") and normalized.get("date"):
            normalized["start_date"] = normalized["date"]
        if normalized.get("leave_days"):
            normalized["leave_days"] = normalize_duration_days(normalized["leave_days"])
        if normalized.get("reason"):
            normalized["reason"] = strip_date_clause(normalized["reason"])
        if (
            normalized.get("start_date")
            and normalized.get("leave_days")
            and not normalized.get("end_date")
        ):
            end_date = derive_end_date(
                normalized["start_date"],
                normalized["leave_days"],
            )
            if end_date:
                normalized["end_date"] = end_date

    return normalized


def normalize_dates_in_text(
    value: str,
    *,
    reference_date: date | None = None,
) -> str:
    reference = reference_date or date.today()

    def replace_slash(match: re.Match[str]) -> str:
        parsed = _safe_date(
            match.group("day"),
            match.group("month"),
            match.group("year") or str(reference.year),
        )
        return parsed.strftime("%d/%m/%Y") if parsed else match.group(0)

    text = re.sub(
        r"\b(?P<day>\d{1,2})[/-](?P<month>\d{1,2})(?:[/-](?P<year>\d{2,4}))?\b",
        replace_slash,
        _clean_value(value),
    )
    return text


def normalize_date_value(
    value: str,
    *,
    reference_date: date | None = None,
) -> str:
    cleaned = _strip_temporal_prefix(_clean_value(value))
    reference = reference_date or date.today()
    parsed = _parse_date(cleaned, reference_date=reference)
    if parsed:
        return parsed.strftime("%d/%m/%Y")
    return cleaned


def normalize_duration_days(value: str) -> str:
    match = re.search(r"\d+", str(value))
    return match.group(0) if match else _clean_value(value)


def derive_end_date(start_date: str, leave_days: str) -> str:
    parsed_start = _parse_date(start_date)
    duration_match = re.search(r"\d+", str(leave_days))
    if not parsed_start or not duration_match:
        return ""
    duration = max(1, int(duration_match.group(0)))
    return (parsed_start + timedelta(days=duration - 1)).strftime("%d/%m/%Y")


def strip_date_clause(value: str) -> str:
    cleaned = _clean_value(value)
    patterns = [
        r"\s+(?:từ|tu|kể từ|ke tu|bắt đầu|bat dau)\s+(?:ngày|ngay)?\s*\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?.*$",
        r"\s+(?:đến|den|tới|toi)\s+(?:ngày|ngay)?\s*\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?.*$",
        r"\s+ngày\s+\d{1,2}\s+tháng\s+\d{1,2}(?:\s+năm\s+\d{2,4})?.*$",
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    return _clean_value(cleaned)


def _parse_date(value: str, *, reference_date: date | None = None) -> date | None:
    reference = reference_date or date.today()
    cleaned = _strip_temporal_prefix(_clean_value(value))

    slash_match = re.search(
        r"\b(?P<day>\d{1,2})[/-](?P<month>\d{1,2})(?:[/-](?P<year>\d{2,4}))?\b",
        cleaned,
    )
    if slash_match:
        return _safe_date(
            slash_match.group("day"),
            slash_match.group("month"),
            slash_match.group("year") or str(reference.year),
        )

    verbose_match = re.search(
        r"(?:ngày|ngay)\s*(?P<day>\d{1,2})\s*(?:tháng|thang)\s*(?P<month>\d{1,2})(?:\s*(?:năm|nam)\s*(?P<year>\d{2,4}))?",
        _normalize_for_matching(cleaned),
    )
    if verbose_match:
        return _safe_date(
            verbose_match.group("day"),
            verbose_match.group("month"),
            verbose_match.group("year") or str(reference.year),
        )

    return None


def _safe_date(day: str, month: str, year: str) -> date | None:
    try:
        year_int = int(year)
        if year_int < 100:
            year_int += 2000
        return date(year_int, int(month), int(day))
    except (TypeError, ValueError):
        return None


def _strip_temporal_prefix(value: str) -> str:
    cleaned = _clean_value(value)
    cleaned = re.sub(
        r"^(?:từ|tu|kể từ|ke tu|đến|den|tới|toi|bắt đầu|bat dau)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return _clean_value(cleaned)


def _trim_field_value(field: str, value: str) -> str:
    cleaned = _clean_value(value)
    normalized = _normalize_for_matching(cleaned)
    cut_at = len(cleaned)
    for phrase in TRIM_BY_FIELD.get(field, []):
        phrase_normalized = _normalize_for_matching(phrase)
        match = re.search(rf"\b{re.escape(phrase_normalized)}\b", normalized)
        if match and match.start() > 0:
            cut_at = min(cut_at, match.start())
    return _clean_value(cleaned[:cut_at])


def _clean_value(value: object) -> str:
    return " ".join(str(value).strip(" :.-\t\n\r").split())


def _normalize_for_matching(text: str) -> str:
    text = text.lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return unicodedata.normalize("NFC", text)
