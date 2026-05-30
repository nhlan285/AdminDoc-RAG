from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from src.extractor import RequestAnalysis
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

def build_draft(
    request: str,
    doc_type: str,
    search_results: list[SearchResult],
    *,
    analysis: RequestAnalysis | None = None,
) -> str:
    doc_type = _normalize_supported_doc_type(doc_type)
    today = date.today()
    citations = _build_citations(search_results)
    topic = _build_topic(request, doc_type, analysis)

    if not citations:
        return _build_no_source_draft(request=request, doc_type=doc_type, topic=topic, today=today, analysis=analysis)

    if doc_type == "Thông báo":
        return _form_thong_bao(topic, today, citations)
    if doc_type == "Tờ trình":
        return _form_to_trinh(topic, today, citations)
    if doc_type == "Quyết định hành chính đơn giản":
        return _form_quyet_dinh_hanh_chinh(topic, today, citations)

    if doc_type in ["Công văn", "Bản ghi nhớ", "Bản thỏa thuận", "Thư công"]:
        return _form_cong_van(topic, today, citations)
    elif doc_type == "Công điện":
        return _form_cong_dien(topic, today, citations)
    elif doc_type == "Giấy mời":
        return _form_giay_moi(topic, today, citations)
    elif doc_type == "Giấy giới thiệu":
        return _form_giay_gioi_thieu(topic, today, citations)
    elif doc_type == "Giấy nghỉ phép":
        return _form_giay_nghi_phep(topic, today, citations, analysis)
    elif doc_type == "Biên bản":
        return _form_bien_ban(topic, today, citations)

    elif doc_type == "Nghị quyết (cá biệt)":
        return _form_nghi_quyet(topic, today, citations)
    elif doc_type == "Quyết định (trực tiếp)":
        return _form_quyet_dinh_truc_tiep(topic, today, citations)
    elif doc_type == "Quyết định (gián tiếp)":
        return _form_quyet_dinh_gian_tiep(topic, today, citations)

    elif doc_type in [
        "Chỉ thị", "Quy chế", "Quy định", "Thông cáo", "Thông báo", "Hướng dẫn",
        "Chương trình", "Kế hoạch", "Phương án", "Đề án", "Dự án", "Báo cáo",
        "Tờ trình", "Hợp đồng", "Giấy ủy quyền", "Phiếu gửi", "Phiếu chuyển", "Phiếu báo"
    ]:
        return _form_van_ban_co_ten_loai(doc_type, topic, today, citations)

    elif doc_type == "Văn bản kèm theo quyết định":
        return _form_van_ban_kem_theo(doc_type, topic, today, citations)

    return _form_cong_van(topic, today, citations)

# --- CÁC HÀM XÂY DỰNG HEADER/FOOTER DÙNG CHUNG ---

def _header_standard(today: date, agency_parent="[TÊN CƠ QUAN CHỦ QUẢN]", agency_name="[TÊN CƠ QUAN BAN HÀNH]"):
    return f"""{agency_parent}
{agency_name}
-------
Số: ... /...

CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
---------------
[Địa danh], ngày {today.day:02d} tháng {today.month:02d} năm {today.year}"""

def _footer_signature(position="[CHỨC DANH NGƯỜI KÝ]"):
    return f"""Nơi nhận:
- Như trên;
- Lưu: VT, [Đơn vị soạn thảo].

{position}
(Ký, đóng dấu)

[Họ và tên người ký]"""

# --- 12 FORM CHI TIẾT ---

def _form_cong_van(topic, today, citations):
    return f"""{_header_standard(today)}
V/v: {topic}

Kính gửi: 
- [Tên đơn vị/cá nhân nhận 1];
- [Tên đơn vị/cá nhân nhận 2].

Nội dung đề nghị:
1. Căn cứ các thông tin đã truy xuất từ kho tri thức {_source_marks(citations)}, [Tên cơ quan ban hành] đề nghị [đơn vị nhận] phối hợp thực hiện nội dung: {topic}.
2. Đề nghị đơn vị liên quan rà soát số liệu, tài liệu minh chứng và gửi phản hồi theo thời hạn do người dùng xác định.
3. Đầu mối tiếp nhận, tổng hợp và báo cáo kết quả: [Tên phòng/ban hoặc chuyên viên phụ trách].

{_footer_signature()}

{_references_section(citations)}

{_quality_note()}
"""

def _form_thong_bao(topic, today, citations):
    return f"""{_header_standard(today)}

THÔNG BÁO
Về việc: {topic}

Nội dung thông báo:
1. [Tên cơ quan ban hành] thông báo nội dung {topic} trên cơ sở các nguồn đã truy xuất {_source_marks(citations)}.
2. Thành phần, thời gian, địa điểm, hình thức thực hiện và tài liệu chuẩn bị cần được người dùng rà soát, bổ sung trước khi ban hành.
3. Các đơn vị/cá nhân liên quan có trách nhiệm theo dõi và phản hồi thông tin theo đầu mối được phân công.

Tổ chức thực hiện:
- [Đơn vị chủ trì] chịu trách nhiệm chuẩn bị nội dung, tài liệu và điều kiện thực hiện.
- [Đơn vị phối hợp] tổng hợp danh sách, kết quả phản hồi và báo cáo lãnh đạo phụ trách.

{_footer_signature()}

{_references_section(citations)}

{_quality_note()}
"""

def _form_to_trinh(topic, today, citations):
    return f"""{_header_standard(today)}

TỜ TRÌNH
Về việc: {topic}

Kính gửi: [Tên cơ quan/người có thẩm quyền phê duyệt]

I. Sự cần thiết
Trên cơ sở yêu cầu thực tiễn và các thông tin tham khảo từ kho tri thức {_source_marks(citations)}, việc {topic} là cần thiết nhằm nâng cao hiệu quả xử lý công việc hành chính.

II. Nội dung đề xuất
1. Mục tiêu: [Mô tả mục tiêu cần đạt].
2. Phạm vi thực hiện: [Đơn vị, thời gian, đối tượng áp dụng].
3. Nhiệm vụ chính: [Các nhiệm vụ, nguồn lực và tiến độ dự kiến].

III. Kiến nghị
Kính đề nghị [cơ quan/người có thẩm quyền] xem xét, phê duyệt chủ trương/nội dung nêu trên để các đơn vị liên quan triển khai thực hiện.

{_footer_signature(position="NGƯỜI TRÌNH")}

{_references_section(citations)}

{_quality_note()}
"""

def _form_quyet_dinh_hanh_chinh(topic, today, citations):
    return f"""{_header_standard(today)}

QUYẾT ĐỊNH
Về việc: {topic}

THẨM QUYỀN BAN HÀNH
Căn cứ chức năng, nhiệm vụ, quyền hạn của [Tên cơ quan ban hành] và các thông tin đã truy xuất {_source_marks(citations)};
Theo đề nghị của [Đơn vị tham mưu].

QUYẾT ĐỊNH:
Điều 1. [Nội dung quyết định chính liên quan đến {topic}; danh sách, phạm vi hoặc nhiệm vụ cụ thể cần người dùng rà soát].
Điều 2. [Trách nhiệm của các đơn vị/cá nhân liên quan trong tổ chức thực hiện].
Điều 3. Quyết định này có hiệu lực kể từ ngày ký. [Các đơn vị/cá nhân liên quan] chịu trách nhiệm thi hành Quyết định này.

{_footer_signature()}

{_references_section(citations)}

{_quality_note()}
"""

def _form_cong_dien(topic, today, citations):
    return f"""{_header_standard(today)}

CÔNG ĐIỆN
Về việc: {topic}

[CHỨC DANH NGƯỜI BAN HÀNH] điện:
- [Đơn vị nhận điện 1];
- [Đơn vị nhận điện 2].

[Nội dung Công điện: Trình bày ngắn gọn, khẩn trương các mệnh lệnh/yêu cầu dựa trên dữ liệu {_source_marks(citations)}.]

{_footer_signature()}

{_references_section(citations)}

{_quality_note()}
"""

def _form_giay_moi(topic, today, citations):
    return f"""{_header_standard(today)}

GIẤY MỜI
{topic.upper()}

[Tên cơ quan ban hành] trân trọng kính mời: [Tên đơn vị/cá nhân]
Tới dự: {topic}
Chủ trì: [Họ tên chuyên viên/lãnh đạo chủ trì]
Thời gian: [Giờ... ngày... tháng... năm...]
Địa điểm: [Phòng họp..., địa chỉ...]
Nội dung: [AI tóm tắt nội dung cuộc họp từ nguồn {_source_marks(citations)}.]

{_footer_signature()}

{_references_section(citations)}

{_quality_note()}
"""

def _form_giay_gioi_thieu(topic, today, citations):
    return f"""{_header_standard(today)}

GIẤY GIỚI THIỆU

[Tên cơ quan ban hành] trân trọng giới thiệu:
Ông (bà): [Họ và tên]
Chức vụ: [Chức vụ hiện tại]
Được cử đến: [Tên cơ quan đến làm việc]
Về việc: {topic} {_source_marks(citations)}

Đề nghị Quý cơ quan tạo điều kiện để ông (bà) có tên ở trên hoàn thành nhiệm vụ.
Giấy này có giá trị đến hết ngày: [Ngày/Tháng/Năm].

{_footer_signature()}

{_references_section(citations)}

{_quality_note()}
"""

def _form_giay_nghi_phep(topic, today, citations, analysis=None):
    subject_name = _slot(analysis, "subject_name", "[Họ và tên]")
    leave_days = _slot(analysis, "leave_days", "[Số ngày]")
    start_date = _slot(analysis, "start_date", "...")
    end_date = _slot(analysis, "end_date", "...")
    reason = _slot(analysis, "reason", topic)
    return f"""{_header_standard(today)}

GIẤY NGHỈ PHÉP

Xét đơn đề nghị nghỉ phép của Ông (bà): {subject_name}
Cấp cho Ông (bà): {subject_name}
Chức vụ: [Chức vụ]
Được nghỉ phép trong thời gian: {leave_days} ngày (Từ {start_date} đến {end_date})
Tại: [Nơi nghỉ phép]
Lý do: {reason} {_source_marks(citations)}

Số ngày nghỉ trên được tính vào thời gian nghỉ [hàng năm/việc riêng].

{_footer_signature()}

{_references_section(citations)}

{_quality_note()}
"""

def _form_bien_ban(topic, today, citations):
    return f"""{_header_standard(today)}

BIÊN BẢN
{topic.upper()}

Thời gian bắt đầu: [Giờ... ngày... tháng... năm...]
Địa điểm: [Nơi diễn ra]
Thành phần tham dự: [Liệt kê danh sách]
Chủ trì: [Họ và tên]
Thư ký: [Họ và tên]

Nội dung (theo diễn biến cuộc họp):
[AI tổng hợp diễn biến và kết luận dựa trên dữ liệu RAG {_source_marks(citations)}.]

Cuộc họp kết thúc vào .... giờ .... cùng ngày.

THƯ KÝ                      CHỦ TỌA
(Ký tên)                    (Ký, đóng dấu)

{_references_section(citations)}

{_quality_note()}
"""

def _form_nghi_quyet(topic, today, citations):
    return f"""{_header_standard(today)}

NGHỊ QUYẾT
{topic.upper()}

THẨM QUYỀN BAN HÀNH
Căn cứ [Các văn bản pháp lý làm căn cứ ban hành] {_source_marks(citations)};
[Diễn giải bối cảnh thông qua Nghị quyết].

QUYẾT NGHỊ:
[Nội dung Nghị quyết chi tiết: AI soạn các Điều 1, Điều 2...]

{_footer_signature()}

{_references_section(citations)}

{_quality_note()}
"""

def _form_quyet_dinh_truc_tiep(topic, today, citations):
    return f"""{_header_standard(today)}
QUYẾT ĐỊNH
Về việc: {topic}

THẨM QUYỀN BAN HÀNH
Căn cứ [Luật/Quy định liên quan] {_source_marks(citations)};
Theo đề nghị của [Chức danh đơn vị tham mưu].

QUYẾT ĐỊNH:
Điều 1. [AI soạn nội dung quyết định trực tiếp: ví dụ bổ nhiệm, khen thưởng...]
Điều 2. [Trách nhiệm thi hành]
Điều 3. [Hiệu lực thi hành]

{_footer_signature()}

{_references_section(citations)}

{_quality_note()}
"""

def _form_quyet_dinh_gian_tiep(topic, today, citations):
    return f"""{_header_standard(today)}
QUYẾT ĐỊNH
Ban hành (Phê duyệt): {topic}

THẨM QUYỀN BAN HÀNH
Căn cứ [Căn cứ pháp lý] {_source_marks(citations)};
Theo đề nghị của [Đơn vị tham mưu].

QUYẾT ĐỊNH:
Điều 1. Ban hành (Phê duyệt) kèm theo Quyết định này [Tên văn bản ban hành].
Điều 2. Quyết định này có hiệu lực kể từ ngày ký.
Điều 3. [Trách nhiệm thi hành].

{_footer_signature()}

{_references_section(citations)}

{_quality_note()}
"""

def _form_van_ban_co_ten_loai(doc_type, topic, today, citations):
    return f"""{_header_standard(today)}

{doc_type.upper()}
{topic.upper()}

[Nội dung văn bản: AI tự động phân bổ mục lục dựa trên {doc_type}. 
Ví dụ Tờ trình cần có: 1. Sự cần thiết; 2. Nội dung đề xuất; 3. Kiến nghị.] 
Dữ liệu nguồn: {_source_marks(citations)}

{_footer_signature()}

{_references_section(citations)}

{_quality_note()}
"""

def _form_van_ban_kem_theo(doc_type, topic, today, citations):
    return f"""[TÊN CƠ QUAN BAN HÀNH]

{doc_type.upper()}
{topic.upper()}
(Kèm theo Quyết định số: ..../QĐ-... ngày ... tháng ... năm ... của ...)
-------
[AI soạn thảo nội dung quy chế/quy định/đề án chi tiết tại đây. 
Chia thành các Chương, Điều, Khoản dựa trên dữ liệu nguồn {_source_marks(citations)}.]

{_references_section(citations)}

{_quality_note()}
"""

# --- CÁC HÀM TRỢ GIÚP (HELPER FUNCTIONS) ---

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

def _source_marks(citations: list[Citation]) -> str:
    return ", ".join(f"[{citation.marker}]" for citation in citations)

def _references_section(citations: list[Citation]) -> str:
    lines = ["Nguồn tham khảo:"]
    for citation in citations:
        lines.append(
            f"- [{citation.marker}] {citation.title} ({citation.source}) - {citation.excerpt}"
        )
    return "\n".join(lines)

def _normalize_supported_doc_type(doc_type: str) -> str:
    if doc_type in {"Quyết định", "Quyết định hành chính đơn giản"}:
        return "Quyết định hành chính đơn giản"
    return doc_type

def _build_topic(request: str, doc_type: str, analysis: RequestAnalysis | None = None) -> str:
    if analysis and analysis.slots.get("topic"):
        return analysis.slots["topic"][:120]
    normalized = " ".join(request.strip().split())
    # Loại bỏ các tiền tố thừa
    for p in ["soạn ", "tạo ", "lập ", doc_type.lower()]:
        if normalized.lower().startswith(p):
            normalized = normalized[len(p):].strip(" :.-")
    return normalized[:120] or doc_type.lower()

def _excerpt(content: str, max_length: int = 260) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= max_length: return normalized
    return normalized[: max_length - 3].rstrip() + "..."

def _build_no_source_draft(*, request: str, doc_type: str, topic: str, today: date, analysis: RequestAnalysis | None = None) -> str:
    """Hàm xử lý khi kho tri thức không có tài liệu phù hợp"""
    return f"""{_header_standard(today)}

{doc_type.upper()}
Về: {topic}

Trạng thái: CHƯA ĐỦ NGUỒN KIỂM CHỨNG ĐỂ SINH BẢN NHÁP HOÀN CHỈNH

Yêu cầu người dùng:
"{request}"

{_analysis_section(analysis)}

Khung xử lý đề xuất:
1. Bổ sung văn bản mẫu hoặc tài liệu quy định liên quan vào kho tri thức (Tab Kho tri thức).
2. Kiểm tra lại từ khóa trong yêu cầu soạn thảo để hệ thống truy xuất chính xác hơn.
3. Bản nháp chi tiết chỉ được sinh ra khi hệ thống tìm thấy ít nhất một nguồn tham khảo tin cậy.

Nguồn tham khảo:
- (Chưa có nguồn phù hợp trong kho tri thức)

{_quality_note()}"""

def _analysis_section(analysis: RequestAnalysis | None) -> str:
    if not analysis:
        return ""
    lines = [
        "Thông tin đã phân tích:",
        f"- Loại văn bản nhận diện: {analysis.detected_doc_type}",
        f"- Ý định: {analysis.intent}",
    ]
    for key, value in analysis.slots.items():
        if value:
            lines.append(f"- {key}: {value}")
    if analysis.missing_fields:
        lines.append("- Cần bổ sung: " + ", ".join(analysis.missing_fields))
    return "\n".join(lines)

def _slot(analysis: RequestAnalysis | None, name: str, placeholder: str) -> str:
    if not analysis:
        return placeholder
    value = analysis.slots.get(name)
    return str(value) if value else placeholder

def _quality_note() -> str:
    """Ghi chú kiểm soát chất lượng"""
    return (
        "Ghi chú kiểm soát: Đây là bản nháp hỗ trợ soạn thảo tự động. "
        "Người dùng bắt buộc phải rà soát lại thể thức, thẩm quyền, số liệu "
        "và tính pháp lý của nội dung trước khi ban hành."
    )
