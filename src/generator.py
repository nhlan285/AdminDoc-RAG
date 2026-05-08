from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.retriever import SearchResult


MAX_CONTEXT_SOURCES = 3


@dataclass(frozen=True)
class Citation:
    marker: str
    document_id: str
    title: str
    source: str
    excerpt: str
    score: float
    matched_terms: list[str]


def build_draft(request: str, doc_type: str, search_results: list[SearchResult]) -> str:
    today = date.today()
    citations = _build_citations(search_results)
    topic = _build_topic(request, doc_type)

    if not citations:
        return _build_no_source_draft(
            request=request,
            doc_type=doc_type,
            topic=topic,
            today=today,
        )

    if doc_type == "Công văn":
        return _build_official_letter(request, topic, today, citations)
    if doc_type == "Thông báo":
        return _build_notice(request, topic, today, citations)
    if doc_type == "Tờ trình":
        return _build_proposal(request, topic, today, citations)
    if doc_type == "Quyết định hành chính đơn giản":
        return _build_decision(request, topic, today, citations)

    return _build_official_letter(request, topic, today, citations)


def _build_official_letter(
    request: str,
    topic: str,
    today: date,
    citations: list[Citation],
) -> str:
    source_marks = _source_marks(citations)
    return f"""{_header(today)}

Số: .../CV-...
V/v {topic}

Kính gửi: [Tên cơ quan/đơn vị/cá nhân nhận công văn]

1. Thông tin truy xuất dùng để soạn thảo
{_format_source_overview(citations)}

2. Nội dung công văn
Từ yêu cầu của người dùng: "{request}", bản nháp công văn cần bám các nguồn {source_marks} và có thể trình bày như sau:
- Nêu rõ đơn vị gửi, đơn vị nhận và mục đích ban hành công văn {source_marks}.
- Trình bày nội dung đề nghị/phối hợp theo đúng phạm vi thông tin đã truy xuất {source_marks}.
- Ghi rõ thời hạn phản hồi, đầu mối liên hệ và tài liệu/biểu mẫu kèm theo nếu người soạn thảo xác nhận có áp dụng {source_marks}.

3. Đề nghị thực hiện
Đề nghị [đơn vị nhận] phối hợp thực hiện nội dung nêu trên và phản hồi về [đầu mối tiếp nhận] trước ngày [ngày/tháng/năm].

Nơi nhận:
- Như trên;
- Lưu: ...

NGƯỜI KÝ
[Chức vụ, họ tên]

{_quality_note()}

Nguồn tham khảo
{_format_reference_list(citations)}
"""


def _build_notice(
    request: str,
    topic: str,
    today: date,
    citations: list[Citation],
) -> str:
    source_marks = _source_marks(citations)
    return f"""{_header(today)}

Số: .../TB-...

THÔNG BÁO
Về {topic}

1. Thông tin truy xuất dùng để soạn thảo
{_format_source_overview(citations)}

2. Nội dung thông báo
Theo yêu cầu: "{request}", thông báo này chỉ sử dụng các nguồn {source_marks} để gợi ý các nội dung cần có:
- Mục đích/nội dung thông báo: [điền nội dung đã được người soạn thảo xác nhận] {source_marks}.
- Thời gian, địa điểm hoặc hình thức thực hiện: [điền thông tin cụ thể].
- Thành phần tham dự/đối tượng nhận thông báo: [điền đối tượng].
- Yêu cầu chuẩn bị hoặc phản hồi: [điền yêu cầu cụ thể] {source_marks}.

3. Tổ chức thực hiện
Đề nghị các đơn vị, cá nhân liên quan theo dõi thông báo và thực hiện đúng nội dung sau khi được người có thẩm quyền rà soát.

Nơi nhận:
- Các đơn vị/cá nhân liên quan;
- Lưu: ...

NGƯỜI KÝ
[Chức vụ, họ tên]

{_quality_note()}

Nguồn tham khảo
{_format_reference_list(citations)}
"""


def _build_proposal(
    request: str,
    topic: str,
    today: date,
    citations: list[Citation],
) -> str:
    source_marks = _source_marks(citations)
    return f"""{_header(today)}

Số: .../TTr-...

TỜ TRÌNH
Về {topic}

Kính gửi: [Cấp có thẩm quyền xem xét/phê duyệt]

1. Thông tin truy xuất dùng để soạn thảo
{_format_source_overview(citations)}

2. Sự cần thiết
Từ yêu cầu: "{request}", người soạn thảo cần trình bày sự cần thiết dựa trên các thông tin đã truy xuất {source_marks}. Không bổ sung mục tiêu, kinh phí hoặc tiến độ chưa có nguồn xác nhận.

3. Nội dung đề xuất
- Mục tiêu/đầu ra dự kiến: [điền mục tiêu đã xác nhận] {source_marks}.
- Phạm vi thực hiện: [điền phạm vi].
- Nhiệm vụ chính: [điền các hạng mục công việc].
- Nguồn lực/kinh phí dự kiến: [chỉ điền khi đã có số liệu được kiểm chứng].
- Tiến độ thực hiện: [điền mốc thời gian].

4. Kiến nghị
Kính đề nghị [cấp có thẩm quyền] xem xét, phê duyệt chủ trương/kế hoạch sau khi các thông tin trong bản nháp được kiểm tra và hoàn thiện.

Nơi nhận:
- Như trên;
- Lưu: ...

NGƯỜI TRÌNH
[Chức vụ, họ tên]

{_quality_note()}

Nguồn tham khảo
{_format_reference_list(citations)}
"""


def _build_decision(
    request: str,
    topic: str,
    today: date,
    citations: list[Citation],
) -> str:
    source_marks = _source_marks(citations)
    return f"""{_header(today)}

Số: .../QĐ-...

QUYẾT ĐỊNH
Về {topic}

[CHỨC DANH NGƯỜI CÓ THẨM QUYỀN]

Căn cứ thông tin truy xuất từ kho tri thức: {source_marks};
Xét yêu cầu soạn thảo: "{request}";

QUYẾT ĐỊNH:

Điều 1. [Nội dung quyết định]
Ban hành/Thành lập/Phê duyệt [nội dung cụ thể] theo phạm vi đã được người soạn thảo kiểm chứng từ nguồn {source_marks}.

Điều 2. [Trách nhiệm thực hiện]
[Đơn vị/cá nhân liên quan] có trách nhiệm tổ chức thực hiện, phối hợp, báo cáo tiến độ và xử lý vướng mắc theo nhiệm vụ được giao {source_marks}.

Điều 3. [Hiệu lực và thi hành]
Quyết định này có hiệu lực kể từ ngày ký. [Các đơn vị/cá nhân liên quan] chịu trách nhiệm thi hành Quyết định này.

Nơi nhận:
- Như Điều 3;
- Lưu: ...

NGƯỜI KÝ
[Chức vụ, họ tên]

{_quality_note()}

Nguồn tham khảo
{_format_reference_list(citations)}
"""


def _build_no_source_draft(
    *,
    request: str,
    doc_type: str,
    topic: str,
    today: date,
) -> str:
    return f"""{_header(today)}

{doc_type.upper()}
Về {topic}

Trạng thái: CHƯA ĐỦ NGUỒN KIỂM CHỨNG ĐỂ SINH BẢN NHÁP HOÀN CHỈNH

Yêu cầu người dùng:
"{request}"

Khung xử lý đề xuất:
- Bổ sung văn bản mẫu hoặc tài liệu liên quan vào kho tri thức.
- Chạy lại bước truy xuất để có nguồn tham khảo.
- Chỉ hoàn thiện nội dung sau khi có nguồn phù hợp và được con người rà soát.

Nguồn tham khảo
- Chưa có nguồn phù hợp trong kho tri thức.

{_quality_note()}
"""


def _build_topic(request: str, doc_type: str) -> str:
    normalized_request = " ".join(request.strip().split())
    if not normalized_request:
        return doc_type.lower()

    lowered = normalized_request.lower()
    prefixes = [
        "soạn công văn",
        "soạn thông báo",
        "soạn tờ trình",
        "soạn quyết định",
        "tạo công văn",
        "tạo thông báo",
        "tạo tờ trình",
        "tạo quyết định",
        "soạn",
        "tạo",
    ]
    for prefix in prefixes:
        if lowered.startswith(prefix):
            normalized_request = normalized_request[len(prefix) :].strip(" :.-")
            break

    return normalized_request[:120] or doc_type.lower()


def _header(today: date) -> str:
    return f"""CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc

..., ngày {today.day:02d} tháng {today.month:02d} năm {today.year}"""


def _build_citations(search_results: list[SearchResult]) -> list[Citation]:
    citations: list[Citation] = []
    for index, result in enumerate(search_results[:MAX_CONTEXT_SOURCES], start=1):
        document = result.document
        citations.append(
            Citation(
                marker=f"S{index}",
                document_id=document.parent_id or document.id,
                title=document.title,
                source=document.source,
                excerpt=_excerpt(document.content),
                score=result.score,
                matched_terms=result.matched_terms,
            )
        )

    return citations


def _format_source_overview(citations: list[Citation]) -> str:
    return "\n".join(
        f"- [{citation.marker}] {citation.title}: {citation.excerpt}"
        for citation in citations
    )


def _format_reference_list(citations: list[Citation]) -> str:
    return "\n".join(
        (
            f"- [{citation.marker}] {citation.document_id} - {citation.source}; "
            f"điểm BM25: {citation.score:.3f}; từ khóa khớp: "
            f"{_matched_terms_text(citation.matched_terms)}"
        )
        for citation in citations
    )


def _source_marks(citations: list[Citation]) -> str:
    return ", ".join(f"[{citation.marker}]" for citation in citations)


def _matched_terms_text(matched_terms: list[str]) -> str:
    return ", ".join(matched_terms) if matched_terms else "khớp theo ngữ cảnh"


def _excerpt(content: str, max_length: int = 260) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= max_length:
        return normalized

    return normalized[: max_length - 3].rstrip() + "..."


def _quality_note() -> str:
    return (
        "Ghi chú kiểm soát: Đây là bản nháp hỗ trợ soạn thảo. Người dùng phải rà soát "
        "thể thức, thẩm quyền, số liệu, ngày tháng và tính phù hợp của nguồn trước khi sử dụng."
    )
