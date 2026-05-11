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
        return _build_no_source_draft(request=request, doc_type=doc_type, topic=topic, today=today)

    # ==============================================================
    # BỘ ĐỊNH TUYẾN (ROUTER): GOM 29 LOẠI VĂN BẢN VỀ 12 KHUÔN MẪU
    # ==============================================================
    
    # 1. Nhóm Công văn & Thư tín hành chính
    if doc_type in ["Công văn", "Bản ghi nhớ", "Bản thỏa thuận", "Thư công"]:
        return _form_cong_van(topic, today, citations)
        
    # 2. Các mẫu đặc thù có format riêng lẻ
    elif doc_type == "Công điện":
        return _form_cong_dien(topic, today, citations)
    elif doc_type == "Giấy mời":
        return _form_giay_moi(topic, today, citations)
    elif doc_type == "Giấy giới thiệu":
        return _form_giay_gioi_thieu(topic, today, citations)
    elif doc_type == "Giấy nghỉ phép":
        return _form_giay_nghi_phep(topic, today, citations)
    elif doc_type == "Biên bản":
        return _form_bien_ban(topic, today, citations)
        
    # 3. Nhóm Quyết định & Nghị quyết
    elif doc_type == "Nghị quyết (cá biệt)":
        return _form_nghi_quyet(topic, today, citations)
    elif doc_type == "Quyết định (trực tiếp)":
        return _form_quyet_dinh_truc_tiep(topic, today, citations)
    elif doc_type == "Quyết định (gián tiếp)":
        return _form_quyet_dinh_gian_tiep(topic, today, citations)
        
    # 4. Nhóm "Văn bản có tên loại" (Gánh 18 loại văn bản có chung bố cục)
    elif doc_type in [
        "Chỉ thị", "Quy chế", "Quy định", "Thông cáo", "Thông báo", "Hướng dẫn",
        "Chương trình", "Kế hoạch", "Phương án", "Đề án", "Dự án", "Báo cáo",
        "Tờ trình", "Hợp đồng", "Giấy ủy quyền", "Phiếu gửi", "Phiếu chuyển", "Phiếu báo"
    ]:
        return _form_van_ban_co_ten_loai(doc_type, topic, today, citations)
        
    # 5. Phụ lục đính kèm
    elif doc_type == "Văn bản kèm theo quyết định":
        return _form_van_ban_kem_theo(doc_type, topic, today, citations)

    # Fallback an toàn nếu có lỗi truyền dữ liệu
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

[Nội dung Công văn: AI soạn thảo căn cứ vào dữ liệu RAG tại đây. Sử dụng trích dẫn {_source_marks(citations)} khi nêu thông tin nguồn.]

{_footer_signature()}
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
"""

def _form_giay_nghi_phep(topic, today, citations):
    return f"""{_header_standard(today)}

GIẤY NGHỈ PHÉP

Xét đơn đề nghị nghỉ phép của Ông (bà): [Họ và tên]
Cấp cho Ông (bà): [Họ và tên]
Chức vụ: [Chức vụ]
Được nghỉ phép trong thời gian: [Số ngày] ngày (Từ ... đến ...)
Tại: [Nơi nghỉ phép]
Lý do: {topic} {_source_marks(citations)}

Số ngày nghỉ trên được tính vào thời gian nghỉ [hàng năm/việc riêng].

{_footer_signature()}
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
"""

def _form_van_ban_co_ten_loai(doc_type, topic, today, citations):
    return f"""{_header_standard(today)}

{doc_type.upper()}
{topic.upper()}

[Nội dung văn bản: AI tự động phân bổ mục lục dựa trên {doc_type}. 
Ví dụ Tờ trình cần có: 1. Sự cần thiết; 2. Nội dung đề xuất; 3. Kiến nghị.] 
Dữ liệu nguồn: {_source_marks(citations)}

{_footer_signature()}
"""

def _form_van_ban_kem_theo(doc_type, topic, today, citations):
    return f"""[TÊN CƠ QUAN BAN HÀNH]

{doc_type.upper()}
{topic.upper()}
(Kèm theo Quyết định số: ..../QĐ-... ngày ... tháng ... năm ... của ...)
-------
[AI soạn thảo nội dung quy chế/quy định/đề án chi tiết tại đây. 
Chia thành các Chương, Điều, Khoản dựa trên dữ liệu nguồn {_source_marks(citations)}.]
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

def _build_topic(request: str, doc_type: str) -> str:
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

def _build_no_source_draft(*, request: str, doc_type: str, topic: str, today: date) -> str:
    """Hàm xử lý khi kho tri thức không có tài liệu phù hợp"""
    return f"""{_header_standard(today)}

{doc_type.upper()}
Về: {topic}

Trạng thái: CHƯA ĐỦ NGUỒN KIỂM CHỨNG ĐỂ SINH BẢN NHÁP HOÀN CHỈNH

Yêu cầu người dùng:
"{request}"

Khung xử lý đề xuất:
1. Bổ sung văn bản mẫu hoặc tài liệu quy định liên quan vào kho tri thức (Tab Kho tri thức).
2. Kiểm tra lại từ khóa trong yêu cầu soạn thảo để hệ thống truy xuất chính xác hơn.
3. Bản nháp chi tiết chỉ được sinh ra khi hệ thống tìm thấy ít nhất một nguồn tham khảo tin cậy.

Nguồn tham khảo:
- (Chưa có nguồn phù hợp trong kho tri thức)

{_quality_note()}"""

def _quality_note() -> str:
    """Ghi chú kiểm soát chất lượng"""
    return (
        "Ghi chú kiểm soát: Đây là bản nháp hỗ trợ soạn thảo tự động. "
        "Người dùng bắt buộc phải rà soát lại thể thức, thẩm quyền, số liệu "
        "và tính pháp lý của nội dung trước khi ban hành."
    )