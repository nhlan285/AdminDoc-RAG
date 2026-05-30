from __future__ import annotations
import json
from pathlib import Path
import streamlit as st

from src.documents import Document, load_documents
from src.docx_exporter import export_draft_to_docx
from src.evaluation import (
    load_extraction_test_cases,
    load_generation_test_cases,
    load_retrieval_test_cases,
    run_extraction_tests,
    run_quality_tests,
    run_generation_tests,
    run_retrieval_tests,
)
from src.extractor import analysis_to_rows, analyze_request
from src.llm import LLMConfig, describe_llm_status, generate_draft, load_llm_config
from src.preprocessing import build_chunks, extract_text_from_binary, parse_documents_from_text
from src.quality import evaluate_draft, report_to_rows
from src.retriever import retrieve
from src.storage import KnowledgeStore

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "admin_docs.json"
SPRINT2_SAMPLE_PATH = BASE_DIR / "data" / "sprint2_sample_docs.json"
RETRIEVAL_TEST_CASES_PATH = BASE_DIR / "data" / "retrieval_test_cases.json"
GENERATION_TEST_CASES_PATH = BASE_DIR / "data" / "generation_test_cases.json"
EXTRACTION_TEST_CASES_PATH = BASE_DIR / "data" / "extraction_test_cases.json"
USER_DATA_PATH = BASE_DIR / "data" / "user_docs.local.json"
TEMPLATE_DIR = BASE_DIR / "data" / "templates"
KNOWLEDGE_DB_PATH = BASE_DIR / "data" / "knowledge.sqlite"

DOCUMENT_TYPES = [
    "Tự động nhận diện (Tải hàng loạt)",
    "Công văn", "Thông báo", "Tờ trình", "Quyết định hành chính đơn giản",
    "Nghị quyết", "Quyết định", "Chỉ thị", "Quy chế", "Quy định",
    "Hướng dẫn", "Thông cáo", "Báo cáo", "Biên bản",
    "Chương trình", "Kế hoạch", "Phương án", "Đề án",
    "Dự án", "Công điện", "Bản ghi nhớ", "Bản thỏa thuận",
    "Hợp đồng", "Giấy ủy quyền", "Giấy mời", "Giấy giới thiệu", 
    "Giấy nghỉ phép", "Phiếu gửi", "Phiếu chuyển", "Phiếu báo", "Thư công"
]

SOURCE_SCOPE_OPTIONS = {
    "Tất cả nguồn": None,
    "Chỉ nguồn hệ thống/mẫu": "system",
    "Chỉ tài liệu upload": "user_upload",
}
SOURCE_KIND_LABELS = {"system": "Hệ thống/mẫu", "user_upload": "Upload riêng"}

@st.cache_data
def get_base_documents() -> list[Document]: return load_documents(DATA_PATH)
@st.cache_data
def get_sprint2_sample_documents() -> list[Document]: return load_documents(SPRINT2_SAMPLE_PATH)
@st.cache_data
def get_template_documents() -> list[Document]:
    documents: list[Document] = []
    if not TEMPLATE_DIR.exists():
        return documents
    for path in sorted(TEMPLATE_DIR.glob("*.txt")):
        documents.extend(
            parse_documents_from_text(
                filename=path.name,
                text=path.read_text(encoding="utf-8"),
                default_doc_type="auto",
                source_kind="system",
            )
        )
    return documents
@st.cache_data
def get_retrieval_test_cases(): return load_retrieval_test_cases(RETRIEVAL_TEST_CASES_PATH)
@st.cache_data
def get_generation_test_cases(): return load_generation_test_cases(GENERATION_TEST_CASES_PATH)
@st.cache_data
def get_extraction_test_cases(): return load_extraction_test_cases(EXTRACTION_TEST_CASES_PATH)

def main() -> None:
    st.set_page_config(page_title="AI soạn thảo văn bản hành chính", layout="wide")
    _ensure_knowledge_base()
    chunks = _current_chunks()
    llm_config = load_llm_config(BASE_DIR)

    st.title("AI hỗ trợ soạn thảo văn bản hành chính")
    st.caption("Bản nháp hành chính có nguồn tham khảo và bước rà soát của con người.")

    with st.sidebar:
        st.header("Cấu hình")
        doc_type = st.selectbox("Loại văn bản", DOCUMENT_TYPES[1:])
        auto_detect_request = st.checkbox("Tự động nhận diện yêu cầu", value=True)
        top_k = st.slider("Số tài liệu truy xuất", 1, 8, 3)
        source_scope_label = st.selectbox("Nguồn dùng khi soạn", list(SOURCE_SCOPE_OPTIONS))
        source_scope = SOURCE_SCOPE_OPTIONS[source_scope_label]
        active_chunks = _filter_chunks_by_source_scope(chunks, source_scope)
        st.divider()
        st.metric("Chunk trong kho", len(chunks))
        st.metric("Chunk đang dùng", len(active_chunks))
        st.divider()
        st.subheader("LLM")
        st.caption(describe_llm_status(llm_config))
        st.divider()
        st.subheader("Xuất DOCX")
        agency_parent = st.text_input("Cơ quan chủ quản", value="[TÊN CƠ QUAN CHỦ QUẢN]")
        agency_name = st.text_input("Cơ quan ban hành", value="[TÊN CƠ QUAN BAN HÀNH]")
        place_name = st.text_input("Địa danh", value="...")

    draft_tab, knowledge_tab = st.tabs(["Soạn thảo", "Kho tri thức"])

    with draft_tab:
        _render_drafting_tab(
            documents=chunks, active_documents=active_chunks, doc_type=doc_type, top_k=top_k, 
            llm_config=llm_config, source_scope_label=source_scope_label, auto_detect_request=auto_detect_request,
            agency_parent=agency_parent, agency_name=agency_name, place_name=place_name,
        )

    with knowledge_tab:
        _render_knowledge_tab(source_scope=source_scope, source_scope_label=source_scope_label)

def _ensure_knowledge_base() -> None:
    if "knowledge_chunks" not in st.session_state:
        _reset_knowledge_base()

def _reset_knowledge_base() -> None:
    base_chunks = build_chunks(get_base_documents() + get_template_documents())
    user_chunks = _load_user_chunks_from_disk()
    st.session_state["knowledge_chunks"] = base_chunks + user_chunks
    _sync_knowledge_store(st.session_state["knowledge_chunks"])
    st.session_state["import_log"] = [
        f"Đã nạp {len(base_chunks)} chunk nền.",
        f"Khôi phục {len(user_chunks)} chunk upload riêng từ bộ nhớ cục bộ.",
    ]


def _current_chunks() -> list[Document]: return st.session_state.get("knowledge_chunks", [])

def _render_drafting_tab(*, documents, active_documents, doc_type, top_k, llm_config, source_scope_label, auto_detect_request, agency_parent, agency_name, place_name) -> None:
    query = st.text_area("Yêu cầu soạn thảo", height=150, placeholder="Ví dụ: Xuân Tịnh xin nghỉ 4 ngày vì ốm")
    if st.button("Tạo bản nháp", type="primary", use_container_width=True):
        if not query.strip(): return st.warning("Vui lòng nhập yêu cầu.")
        if documents and not active_documents: return st.warning("Không có tài liệu trong phạm vi lọc.")

        analysis = analyze_request(query, default_doc_type=doc_type)
        effective_doc_type = analysis.detected_doc_type if auto_detect_request and analysis.confidence >= 0.5 else doc_type
        retrieval_query = analysis.retrieval_query if auto_detect_request else query
        results = retrieve(retrieval_query, active_documents, doc_type=effective_doc_type, top_k=top_k)
        draft_result = generate_draft(
            request=query,
            doc_type=effective_doc_type,
            search_results=results,
            config=llm_config,
            request_analysis=analysis,
        )

        left, right = st.columns([2, 1])
        quality_report = evaluate_draft(draft=draft_result.text, doc_type=effective_doc_type, search_results=results)
        
        with left:
            st.subheader("Bản nháp")
            if effective_doc_type != doc_type:
                st.info(f"Tự động nhận diện loại văn bản: {effective_doc_type}")
            if draft_result.used_llm: st.success(f"Sinh bằng {draft_result.provider.upper()} API.")
            if draft_result.fallback_used and draft_result.error:
                st.warning(f"Đã dùng bản sinh dự phòng: {draft_result.error}")
            st.text_area("Nội dung sinh ra", value=draft_result.text, height=560)
            
            docx_bytes = export_draft_to_docx(draft=draft_result.text, doc_type=effective_doc_type, agency_parent=agency_parent, agency_name=agency_name, place_name=place_name)
            d1, d2 = st.columns(2)
            d1.download_button("Tải bản nháp TXT", data=draft_result.text.encode("utf-8"), file_name=f"{effective_doc_type}.txt", mime="text/plain", use_container_width=True)
            d2.download_button("Tải bản nháp DOCX chuẩn", data=docx_bytes, file_name=f"{effective_doc_type}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            
        with right:
            st.subheader("Phân tích yêu cầu")
            st.dataframe(analysis_to_rows(analysis), use_container_width=True, hide_index=True)
            st.subheader("Nguồn truy xuất")
            _render_search_results(results)
        _render_quality_report(quality_report)
    else: st.info("Chưa có bản nháp.")

def _render_knowledge_tab(*, source_scope, source_scope_label) -> None:
    st.subheader("Nạp và kiểm tra kho tri thức")
    chunks = _current_chunks()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Chunk", len(chunks))
    c2.metric("Tài liệu gốc", len({d.parent_id or d.id for d in chunks}))
    c3.metric("Upload riêng", len(_filter_chunks_by_source_scope(chunks, "user_upload")))
    c4.metric("SQLite chunks", _knowledge_store().stats().chunks)
    
    a1, a2, a3 = st.columns([2, 1, 1])
    with a1:
        if st.button("Nạp tài liệu mẫu", type="primary"):
            _merge_chunks(build_chunks(get_sprint2_sample_documents()))
            chunks = _current_chunks()
    with a2:
        if st.button("Xóa upload riêng"):
            _delete_user_upload_chunks()
            chunks = _current_chunks()
    with a3:
        if st.button("Reset kho"):
            _reset_knowledge_base()
            chunks = _current_chunks()

    with st.expander("Upload tài liệu nghiệp vụ (PDF, DOCX, TXT, MD, JSON)", expanded=True):
        upload_doc_type = st.selectbox("Loại mặc định cho file tải lên", DOCUMENT_TYPES)
        chunk_size = st.slider("Số từ tối đa mỗi chunk", 60, 400, 150, step=10)
        uploaded_files = st.file_uploader("Kéo thả file vào đây", type=["txt", "md", "json", "pdf", "docx"], accept_multiple_files=True)
        if st.button("Nạp file đã chọn") and uploaded_files:
            added_docs, errors = _parse_uploaded_files(uploaded_files=uploaded_files, default_doc_type=upload_doc_type)
            added = _merge_chunks(build_chunks(added_docs, chunk_size_words=chunk_size, overlap_words=30))
            chunks = _current_chunks()
            if added: st.success(f"Nạp thành công {added} đoạn từ {len(added_docs)} tài liệu.")
            if errors: st.error("\n".join(errors))

    _render_test_panel(chunks)

    st.dataframe(_chunk_rows(chunks), use_container_width=True, hide_index=True)

def _parse_uploaded_files(*, uploaded_files, default_doc_type) -> tuple[list[Document], list[str]]:
    documents, errors = [], []
    for uploaded_file in uploaded_files:
        try:
            text = extract_text_from_binary(uploaded_file.getvalue(), uploaded_file.name)
            parsed = parse_documents_from_text(filename=uploaded_file.name, text=text, default_doc_type=default_doc_type, source_kind="user_upload")
            documents.extend(parsed)
        except Exception as error:
            errors.append(f"{uploaded_file.name}: {str(error)}")
    return documents, errors

def _merge_chunks(new_chunks):
    current = _current_chunks()
    existing_ids = {d.id for d in current}
    unique = [d for d in new_chunks if d.id not in existing_ids]
    
    updated_chunks = current + unique
    st.session_state["knowledge_chunks"] = updated_chunks
    
    _save_user_chunks_to_disk(updated_chunks)
    _sync_knowledge_store(updated_chunks)
    
    return len(unique)

def _delete_user_upload_chunks():
    kept = [d for d in _current_chunks() if d.source_kind != "user_upload"]
    st.session_state["knowledge_chunks"] = kept
    
    _save_user_chunks_to_disk(kept)
    _sync_knowledge_store(kept)
    
def _render_search_results(results):
    for r in results:
        with st.expander(f"{r.document.id} - Điểm {r.score:.3f}"):
            st.caption(f"{SOURCE_KIND_LABELS.get(r.document.source_kind, r.document.source_kind)} | {r.document.doc_type} | Từ khóa khớp: {', '.join(r.matched_terms)}")
            st.write(r.document.content)

def _render_quality_report(report):
    st.subheader("Chất lượng bản nháp")
    c1, c2 = st.columns(2)
    c1.metric("Điểm", f"{report.score}/100")
    c2.metric("Rủi ro", report.risk_level)
    st.dataframe(report_to_rows(report), use_container_width=True, hide_index=True)

def _chunk_rows(chunks):
    return [
        {
            "id": d.id,
            "Loại": d.doc_type,
            "Nhóm nguồn": SOURCE_KIND_LABELS.get(d.source_kind, d.source_kind),
            "Nguồn": d.source,
            "Nội dung": d.content[:120],
        }
        for d in chunks
    ]

def _render_test_panel(chunks) -> None:
    with st.expander("Kiểm thử demo Sprint 3/4/6", expanded=False):
        t1, t2, t3, t4 = st.columns(4)
        if t1.button("Chạy test truy xuất Sprint 3", use_container_width=True):
            _store_test_result("Truy xuất Sprint 3", run_retrieval_tests(get_retrieval_test_cases(), chunks))
        if t2.button("Chạy test generator Sprint 4", use_container_width=True):
            _store_test_result("Generator Sprint 4", run_generation_tests(get_generation_test_cases(), chunks))
        if t3.button("Chạy test chất lượng Sprint 6", use_container_width=True):
            _store_test_result("Chất lượng Sprint 6", run_quality_tests(get_generation_test_cases(), chunks))
        if t4.button("Chạy test phân tích yêu cầu", use_container_width=True):
            _store_test_result("Phân tích yêu cầu", run_extraction_tests(get_extraction_test_cases()))

        test_result = st.session_state.get("last_test_result")
        if test_result:
            name, rows = test_result
            passed = sum(1 for row in rows if row.get("passed"))
            st.success(f"{name}: đạt {passed}/{len(rows)} test.")
            st.dataframe(rows, use_container_width=True, hide_index=True)

def _store_test_result(name: str, rows: list[dict[str, object]]) -> None:
    st.session_state["last_test_result"] = (name, rows)

def _filter_chunks_by_source_scope(chunks, scope):
    if not scope: return chunks
    return [d for d in chunks if d.source_kind == scope]

def _save_user_chunks_to_disk(chunks):
    """Lưu dữ liệu upload riêng vào file local đã được ignore khỏi git."""
    # Chỉ lọc và lưu những file người dùng upload riêng
    user_chunks = [c for c in chunks if c.source_kind == "user_upload"]
    data_to_save = []
    
    for c in user_chunks:
        data_to_save.append({
            "id": c.id,
            "title": c.title,
            "doc_type": c.doc_type,
            "source": c.source,
            "content": c.content,
            "source_kind": c.source_kind,
            "parent_id": getattr(c, "parent_id", None),
            "chunk_index": getattr(c, "chunk_index", None),
            "total_chunks": getattr(c, "total_chunks", None)
        })
        
    USER_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)

def _load_user_chunks_from_disk():
    """Khôi phục dữ liệu từ ổ cứng lên lại RAM khi F5"""
    if not USER_DATA_PATH.exists():
        return []
    try:
        with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Document(**item) for item in data]
    except Exception as e:
        st.warning(f"Không thể khôi phục dữ liệu upload riêng: {e}")
        return []

def _knowledge_store() -> KnowledgeStore:
    return KnowledgeStore(KNOWLEDGE_DB_PATH)

def _sync_knowledge_store(chunks: list[Document]) -> None:
    _knowledge_store().replace_chunks(chunks)
    
if __name__ == "__main__":
    main()
