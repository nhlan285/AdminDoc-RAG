from __future__ import annotations
from dataclasses import replace
import html
import json
from pathlib import Path
import streamlit as st

from src.documents import Document, load_documents
from src.docx_exporter import export_draft_to_docx
from src.evaluation import (
    load_extraction_test_cases,
    load_form_test_cases,
    load_generation_test_cases,
    load_retrieval_test_cases,
    run_extraction_tests,
    run_form_tests,
    run_quality_tests,
    run_generation_tests,
    run_retrieval_tests,
)
from src.extractor import analysis_to_rows, analyze_request
from src.llm import LLMConfig, describe_llm_status, generate_draft, load_llm_config
from src.preprocessing import build_chunks, extract_text_from_binary, parse_documents_from_text
from src.quality import evaluate_draft, report_to_rows
from src.retriever import describe_retrieval_status, rebuild_vector_index, retrieve
from src.slot_normalizer import normalize_slots
from src.storage import KnowledgeStore

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "admin_docs.json"
SPRINT2_SAMPLE_PATH = BASE_DIR / "data" / "sprint2_sample_docs.json"
DOC_TYPE_SEED_PATH = BASE_DIR / "data" / "doc_type_seed_docs.json"
RETRIEVAL_TEST_CASES_PATH = BASE_DIR / "data" / "retrieval_test_cases.json"
GENERATION_TEST_CASES_PATH = BASE_DIR / "data" / "generation_test_cases.json"
EXTRACTION_TEST_CASES_PATH = BASE_DIR / "data" / "extraction_test_cases.json"
FORM_TEST_CASES_PATH = BASE_DIR / "data" / "form_test_cases.json"
USER_DATA_PATH = BASE_DIR / "data" / "user_docs.local.json"
TEMPLATE_DIR = BASE_DIR / "data" / "templates"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
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


def _inject_design_system() -> None:
    st.markdown(
        """
        <style>
        :root {
            --app-bg: #12161b;
            --panel: #20252b;
            --panel-soft: #191e24;
            --panel-raised: #252b33;
            --line: #343b45;
            --line-soft: #2b313a;
            --text: #f3f6fb;
            --muted: #a7b0bd;
            --muted-2: #76808f;
            --primary: #f5f5f2;
            --accent: #8ab4f8;
            --green: #7fdca8;
            --amber: #ffd37a;
            --red: #ff8d8d;
            --violet: #b8a5ff;
        }

        .stApp {
            background: var(--app-bg);
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: transparent;
            height: 0;
        }

        section[data-testid="stSidebar"] {
            display: none;
        }

        .block-container {
            max-width: 1880px;
            padding: 1.05rem 1.35rem 1.2rem 1.35rem;
        }

        .notebook-topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.9rem;
        }

        .notebook-title-wrap {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            min-width: 0;
        }

        .notebook-logo {
            width: 2.85rem;
            height: 2.85rem;
            display: grid;
            place-items: center;
            border-radius: 999px;
            background: #f8fafc;
            color: #101418 !important;
            font-weight: 900;
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.24);
        }

        .notebook-title {
            color: var(--text);
            font-size: 1.75rem;
            font-weight: 650;
            letter-spacing: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .notebook-subtitle {
            color: var(--muted);
            font-size: 0.85rem;
            margin-top: 0.08rem;
        }

        .topbar-actions {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.55rem;
            flex-wrap: wrap;
        }

        .topbar-status {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            min-height: 2rem;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            border: 1px solid var(--line);
            color: var(--muted);
            background: #171c22;
            font-size: 0.8rem;
            font-weight: 650;
        }

        .composer-shell {
            padding: 0.85rem;
            border: 1px solid var(--line-soft);
            border-radius: 1rem;
            background: var(--panel-soft);
            margin-bottom: 0.9rem;
        }

        .composer-hint {
            color: var(--muted);
            font-size: 0.8rem;
            margin: 0.35rem 0 0.65rem 0;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 1.05rem;
            box-shadow: none;
            overflow: visible;
        }

        [data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 0.95rem 1rem 1rem 1rem;
        }

        .panel-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.7rem;
            color: var(--text);
            font-size: 1.1rem;
            font-weight: 700;
            padding-bottom: 0.75rem;
            margin-bottom: 0.8rem;
            border-bottom: 1px solid var(--line-soft);
        }

        .panel-icon {
            color: var(--muted);
            font-size: 1.05rem;
        }

        .section-title {
            color: var(--text);
            font-size: 0.95rem;
            font-weight: 720;
            margin: 0.75rem 0 0.45rem 0;
        }

        .section-caption {
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.5;
            margin-bottom: 0.65rem;
        }

        .notebook-empty {
            min-height: 18rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: flex-start;
            max-width: 48rem;
            margin: 0 auto;
            padding: 2rem 1rem;
        }

        .empty-emoji {
            font-size: 3rem;
            line-height: 1;
            margin-bottom: 1rem;
        }

        .empty-title {
            color: var(--text);
            font-size: clamp(1.7rem, 3vw, 2.55rem);
            line-height: 1.06;
            letter-spacing: 0;
            font-weight: 520;
            margin-bottom: 1.05rem;
        }

        .empty-copy {
            color: #d5dbe4;
            font-size: 1.02rem;
            line-height: 1.6;
            max-width: 50rem;
        }

        .mini-stat-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.55rem;
            margin: 0.75rem 0;
        }

        .mini-stat {
            background: var(--panel-soft);
            border: 1px solid var(--line);
            border-radius: 0.8rem;
            padding: 0.72rem 0.78rem;
        }

        .mini-stat-label {
            color: var(--muted);
            font-size: 0.75rem;
        }

        .mini-stat-value {
            color: var(--text);
            font-size: 1.2rem;
            font-weight: 760;
            margin-top: 0.18rem;
        }

        .source-card,
        .studio-card,
        .draft-card {
            background: var(--panel-soft);
            border: 1px solid var(--line);
            border-radius: 0.86rem;
            padding: 0.78rem 0.85rem;
            margin-bottom: 0.58rem;
        }

        .source-title {
            color: var(--text);
            font-weight: 720;
            font-size: 0.9rem;
            line-height: 1.35;
        }

        .source-meta {
            color: var(--muted);
            font-size: 0.76rem;
            margin-top: 0.25rem;
            line-height: 1.4;
        }

        .source-score {
            color: var(--accent);
            font-weight: 740;
        }

        .studio-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.62rem;
            margin: 0.75rem 0 0.9rem 0;
        }

        .studio-card {
            min-height: 4.3rem;
            margin-bottom: 0;
            position: relative;
        }

        .studio-card strong {
            display: block;
            color: var(--text);
            font-size: 0.85rem;
            line-height: 1.35;
        }

        .studio-card span {
            display: block;
            color: var(--muted);
            font-size: 0.72rem;
            margin-top: 0.18rem;
        }

        .studio-card.blue { background: linear-gradient(135deg, #252b45, #283047); }
        .studio-card.green { background: linear-gradient(135deg, #213428, #26352c); }
        .studio-card.amber { background: linear-gradient(135deg, #393524, #333125); }
        .studio-card.pink { background: linear-gradient(135deg, #3a2935, #352b35); }

        .empty-state {
            background: var(--panel-soft);
            border: 1px dashed #46505d;
            border-radius: 0.9rem;
            padding: 1rem;
            color: var(--muted);
            line-height: 1.55;
        }

        .pill-row {
            display: flex;
            gap: 0.45rem;
            flex-wrap: wrap;
            margin: 0.45rem 0 0.8rem 0;
        }

        .pill {
            border-radius: 999px;
            padding: 0.3rem 0.68rem;
            border: 1px solid #3e536f;
            background: #243143;
            color: #dbeafe;
            font-size: 0.78rem;
            font-weight: 650;
        }

        .status-good { color: var(--green); font-weight: 760; }
        .status-warn { color: var(--amber); font-weight: 760; }
        .status-bad { color: var(--red); font-weight: 760; }

        div.stButton > button {
            border-radius: 999px;
            border: 1px solid var(--line);
            font-weight: 740;
            min-height: 2.5rem;
            color: var(--text);
            background: transparent;
        }

        div.stButton > button[kind="primary"] {
            background: var(--primary);
            border: none;
            color: #111418;
            box-shadow: none;
        }

        .stDownloadButton > button {
            border-radius: 999px;
            border: 1px solid var(--line);
            color: var(--text);
            background: transparent;
            font-weight: 740;
        }

        .stTextArea textarea,
        .stTextInput input {
            border-radius: 1rem;
            border: 1px solid #58606c;
            background: #1a1f26;
            color: var(--text);
            line-height: 1.55;
        }

        .stTextArea textarea::placeholder,
        .stTextInput input::placeholder {
            color: var(--muted-2);
        }

        .stSelectbox [data-baseweb="select"],
        .stMultiSelect [data-baseweb="select"] {
            border-radius: 999px;
            background: #1a1f26;
            border-color: #58606c;
        }

        label,
        [data-testid="stMarkdownContainer"] p,
        .stCaption {
            color: var(--muted);
        }

        [data-testid="stMetric"] {
            background: var(--panel-soft);
            border: 1px solid var(--line);
            border-radius: 0.85rem;
            padding: 0.75rem 0.85rem;
        }

        [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"] {
            color: var(--text) !important;
        }

        [data-testid="stDataFrame"] {
            border-radius: 0.85rem;
            overflow: hidden;
        }

        .stAlert {
            border-radius: 0.9rem;
        }

        .stExpander {
            border-color: var(--line);
            background: transparent;
        }

        hr {
            border-color: var(--line-soft);
        }

        .footer-note {
            text-align: center;
            color: var(--muted-2);
            font-size: 0.78rem;
            margin-top: 0.4rem;
        }

        @media (max-width: 900px) {
            .notebook-topbar {
                align-items: flex-start;
                flex-direction: column;
            }
            .notebook-title {
                font-size: 1.35rem;
            }
            .studio-grid,
            .mini-stat-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

@st.cache_data
def get_base_documents() -> list[Document]: return load_documents(DATA_PATH)
@st.cache_data
def get_sprint2_sample_documents() -> list[Document]: return load_documents(SPRINT2_SAMPLE_PATH)
@st.cache_data
def get_doc_type_seed_documents() -> list[Document]: return load_documents(DOC_TYPE_SEED_PATH)
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
def get_processed_documents() -> list[Document]:
    documents: list[Document] = []
    if not PROCESSED_DIR.exists():
        return documents
    for path in sorted(PROCESSED_DIR.glob("*.json")):
        try:
            documents.extend(load_documents(path))
        except Exception:
            continue
    return documents

@st.cache_data
def get_retrieval_test_cases(): return load_retrieval_test_cases(RETRIEVAL_TEST_CASES_PATH)
@st.cache_data
def get_generation_test_cases(): return load_generation_test_cases(GENERATION_TEST_CASES_PATH)
@st.cache_data
def get_extraction_test_cases(): return load_extraction_test_cases(EXTRACTION_TEST_CASES_PATH)
@st.cache_data
def get_form_test_cases(): return load_form_test_cases(FORM_TEST_CASES_PATH)


def _render_workspace_header(*, chunks: list[Document], active_chunks: list[Document], source_scope_label: str) -> None:
    st.markdown(
        f"""
        <section class="workspace-hero">
          <div>
            <div class="workspace-kicker">RAG workspace</div>
            <div class="workspace-title">AI hỗ trợ soạn thảo văn bản hành chính</div>
            <div class="workspace-subtitle">Bản nháp được tạo từ kho tri thức cục bộ, có nguồn tham khảo, kiểm tra chất lượng và bước rà soát của con người.</div>
          </div>
          <div class="hero-stats">
            <div class="hero-stat">
              <div class="hero-stat-label">Kho tri thức</div>
              <div class="hero-stat-value">{len(chunks)}</div>
            </div>
            <div class="hero-stat">
              <div class="hero-stat-label">Đang dùng</div>
              <div class="hero-stat-value">{len(active_chunks)}</div>
            </div>
            <div class="hero-stat">
              <div class="hero-stat-label">Phạm vi</div>
              <div class="hero-stat-value">{_escape(source_scope_label)}</div>
            </div>
            <div class="hero-stat">
              <div class="hero-stat-label">Tài liệu</div>
              <div class="hero-stat-value">{len({d.parent_id or d.id for d in chunks})}</div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

def main() -> None:
    st.set_page_config(
        page_title="AdminDoc Notebook",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_design_system()
    _ensure_knowledge_base()
    chunks = _current_chunks()
    llm_config = load_llm_config(BASE_DIR)

    _render_notebook_topbar(chunks=chunks, llm_config=llm_config)

    source_col, chat_col, studio_col = st.columns([1.05, 2.02, 1.05], gap="medium")

    with source_col:
        settings = _render_sources_panel(chunks=chunks, llm_config=llm_config)

    active_chunks = _filter_chunks_by_source_scope(
        _current_chunks(),
        settings["source_scope"],
    )

    with chat_col:
        _render_chat_panel(
            documents=_current_chunks(),
            active_documents=active_chunks,
            doc_type=settings["doc_type"],
            top_k=settings["top_k"],
            retrieval_mode=settings["retrieval_mode"],
            llm_config=llm_config,
            auto_detect_request=settings["auto_detect_request"],
            agency_parent=settings["agency_parent"],
            agency_name=settings["agency_name"],
            place_name=settings["place_name"],
        )

    with studio_col:
        _render_studio_panel(
            chunks=_current_chunks(),
            active_chunks=active_chunks,
            source_scope_label=settings["source_scope_label"],
        )

    st.markdown(
        '<div class="footer-note">AdminDoc có thể tạo thông tin chưa chính xác; hãy rà soát nguồn, thể thức và nội dung trước khi sử dụng.</div>',
        unsafe_allow_html=True,
    )

def _ensure_knowledge_base() -> None:
    if "knowledge_chunks" not in st.session_state:
        _reset_knowledge_base()

def _reset_knowledge_base() -> None:
    base_chunks = build_chunks(
        get_base_documents()
        + get_sprint2_sample_documents()
        + get_doc_type_seed_documents()
        + get_template_documents()
        + get_processed_documents()
    )
    user_chunks = _load_user_chunks_from_disk()
    st.session_state["knowledge_chunks"] = base_chunks + user_chunks
    _sync_knowledge_store(st.session_state["knowledge_chunks"])
    st.session_state["import_log"] = [
        f"Đã nạp {len(base_chunks)} chunk nền.",
        f"Khôi phục {len(user_chunks)} chunk upload riêng từ bộ nhớ cục bộ.",
    ]


def _current_chunks() -> list[Document]: return st.session_state.get("knowledge_chunks", [])


def _render_notebook_topbar(*, chunks: list[Document], llm_config: LLMConfig) -> None:
    document_count = len({d.parent_id or d.id for d in chunks})
    st.markdown(
        f"""
        <div class="notebook-topbar">
          <div class="notebook-title-wrap">
            <div class="notebook-logo">AD</div>
            <div>
              <div class="notebook-title">AdminDoc Notebook</div>
              <div class="notebook-subtitle">AI hỗ trợ soạn thảo văn bản hành chính bằng RAG</div>
            </div>
          </div>
          <div class="topbar-actions">
            <span class="topbar-status">{document_count} tài liệu</span>
            <span class="topbar-status">{_escape(describe_llm_status(llm_config))}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sources_panel(*, chunks: list[Document], llm_config: LLMConfig) -> dict[str, object]:
    with st.container(border=True):
        st.markdown(
            '<div class="panel-heading"><span>Nguồn</span><span class="panel-icon">▣</span></div>',
            unsafe_allow_html=True,
        )

        with st.expander("Tải lên tài liệu", expanded=False):
            upload_doc_type = st.selectbox(
                "Loại mặc định cho file tải lên",
                DOCUMENT_TYPES,
                key="source_upload_doc_type",
            )
            chunk_size = st.slider(
                "Số từ tối đa mỗi chunk",
                60,
                400,
                150,
                step=10,
                key="source_chunk_size",
            )
            uploaded_files = st.file_uploader(
                "Kéo thả PDF, DOCX, TXT, MD hoặc JSON",
                type=["txt", "md", "json", "pdf", "docx"],
                accept_multiple_files=True,
                key="source_file_uploader",
            )
            if st.button("Nạp file đã chọn", use_container_width=True) and uploaded_files:
                added_docs, errors = _parse_uploaded_files(
                    uploaded_files=uploaded_files,
                    default_doc_type=upload_doc_type,
                )
                added = _merge_chunks(
                    build_chunks(
                        added_docs,
                        chunk_size_words=chunk_size,
                        overlap_words=30,
                    )
                )
                chunks = _current_chunks()
                if added:
                    st.success(f"Nạp thành công {added} đoạn từ {len(added_docs)} tài liệu.")
                if errors:
                    st.error("\n".join(errors))

        st.markdown('<div class="section-title">Cấu hình soạn thảo</div>', unsafe_allow_html=True)
        doc_type = st.selectbox(
            "Loại dự phòng nếu hệ thống không chắc",
            DOCUMENT_TYPES[1:],
            key="source_doc_type",
        )
        auto_detect_request = st.toggle(
            "Tự động nhận diện yêu cầu",
            value=True,
            key="source_auto_detect",
        )
        top_k = st.slider("Số nguồn truy xuất", 1, 8, 3, key="source_top_k")
        retrieval_mode = "hybrid"
        source_scope_label = st.selectbox(
            "Nguồn dùng khi soạn",
            list(SOURCE_SCOPE_OPTIONS),
            key="source_scope_label",
        )
        source_scope = SOURCE_SCOPE_OPTIONS[source_scope_label]
        active_chunks = _filter_chunks_by_source_scope(chunks, source_scope)

        st.markdown(
            f"""
            <div class="mini-stat-grid">
              <div class="mini-stat">
                <div class="mini-stat-label">Chunk trong kho</div>
                <div class="mini-stat-value">{len(chunks)}</div>
              </div>
              <div class="mini-stat">
                <div class="mini-stat-label">Đang dùng</div>
                <div class="mini-stat-value">{len(active_chunks)}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(describe_llm_status(llm_config))
        st.caption(describe_retrieval_status(BASE_DIR))

        with st.expander("Thông tin xuất DOCX", expanded=False):
            agency_parent = st.text_input(
                "Cơ quan chủ quản",
                value="[TÊN CƠ QUAN CHỦ QUẢN]",
                key="docx_agency_parent",
            )
            agency_name = st.text_input(
                "Cơ quan ban hành",
                value="[TÊN CƠ QUAN BAN HÀNH]",
                key="docx_agency_name",
            )
            place_name = st.text_input("Địa danh", value="...", key="docx_place_name")

        workspace = st.session_state.get("last_draft_workspace")
        if workspace and workspace.get("results"):
            _render_retrieved_sources_preview(workspace["results"])
        else:
            _render_source_collection(active_chunks)

        with st.expander("Nâng cao", expanded=False):
            admin_left, admin_right = st.columns(2)
            if admin_left.button("Xóa upload", use_container_width=True):
                _delete_user_upload_chunks()
                chunks = _current_chunks()
            if admin_right.button("Reset kho", use_container_width=True):
                _reset_knowledge_base()
                chunks = _current_chunks()
            if st.button("Tạo lại chỉ mục vector", use_container_width=True):
                try:
                    stats = rebuild_vector_index(_current_chunks(), project_root=BASE_DIR)
                    st.success(
                        f"Vector index: {stats.indexed} chunk, làm mới {stats.refreshed}, xóa {stats.removed}."
                    )
                except Exception as error:
                    st.warning(f"Chưa thể tạo vector index: {error}")

    return {
        "doc_type": doc_type,
        "auto_detect_request": auto_detect_request,
        "top_k": top_k,
        "retrieval_mode": retrieval_mode,
        "source_scope_label": source_scope_label,
        "source_scope": source_scope,
        "agency_parent": agency_parent,
        "agency_name": agency_name,
        "place_name": place_name,
    }


def _render_source_collection(chunks: list[Document]) -> None:
    if not chunks:
        st.markdown(
            """
            <div class="empty-state">
              Các nguồn đã lưu sẽ xuất hiện ở đây. Hãy thêm file hoặc nạp bộ mẫu để bắt đầu.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    seen: set[str] = set()
    documents: list[Document] = []
    for chunk in chunks:
        source_id = chunk.parent_id or chunk.id
        if source_id in seen:
            continue
        seen.add(source_id)
        documents.append(chunk)

    with st.expander(f"Tài liệu trong kho ({len(documents)})", expanded=False):
        visible_documents = documents[:5]
        for document in visible_documents:
            st.markdown(
                f"""
                <div class="source-card">
                  <div class="source-title">{_escape(document.title or document.id)}</div>
                  <div class="source-meta">{_escape(document.doc_type)} · {_escape(SOURCE_KIND_LABELS.get(document.source_kind, document.source_kind))}</div>
                  <div class="source-meta">{_escape(document.source)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if len(documents) > len(visible_documents):
            st.caption(f"Còn {len(documents) - len(visible_documents)} tài liệu khác trong kho.")


def _render_retrieved_sources_preview(results) -> None:
    st.markdown('<div class="section-title">Nguồn được dùng</div>', unsafe_allow_html=True)
    visible_results = results[:3]
    for index, result in enumerate(visible_results, start=1):
        st.markdown(
            f"""
            <div class="source-card">
              <div class="source-title">{index}. {_escape(result.document.title or result.document.id)}</div>
              <div class="source-meta">{_escape(result.document.doc_type)} · {_escape(getattr(result, "retrieval_method", "bm25"))} · <span class="source-score">Điểm {result.score:.3f}</span></div>
              <div class="source-meta">Từ khóa: {_escape(", ".join(result.matched_terms) or "không có")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"Xem đoạn nguồn {index}", expanded=False):
            st.write(result.document.content)
    if len(results) > len(visible_results):
        st.caption(f"Còn {len(results) - len(visible_results)} nguồn truy xuất khác.")


def _render_chat_panel(
    *,
    documents,
    active_documents,
    doc_type,
    top_k,
    retrieval_mode,
    llm_config,
    auto_detect_request,
    agency_parent,
    agency_name,
    place_name,
) -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="panel-heading"><span>Cuộc trò chuyện</span><span class="panel-icon">⋮</span></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="composer-hint">Sửa prompt rồi bấm tạo lại nếu bản nháp chưa đúng ý.</div>',
            unsafe_allow_html=True,
        )
        with st.form("draft_composer", clear_on_submit=False):
            query = st.text_area(
                "Đặt câu hỏi hoặc tạo nội dung",
                key="draft_prompt",
                height=108,
                label_visibility="collapsed",
            )
            generate_clicked = st.form_submit_button(
                "Tạo / tạo lại bản nháp",
                type="primary",
                use_container_width=True,
            )

        if generate_clicked:
            if not query.strip():
                st.warning("Vui lòng nhập yêu cầu.")
                return
            if documents and not active_documents:
                st.warning("Không có tài liệu trong phạm vi lọc.")
                return
            _start_draft_or_clarification(
                query=query,
                documents=documents,
                active_documents=active_documents,
                doc_type=doc_type,
                top_k=top_k,
                retrieval_mode=retrieval_mode,
                llm_config=llm_config,
                auto_detect_request=auto_detect_request,
            )
            st.rerun()

        pending_clarification = st.session_state.get("pending_clarification")
        workspace = st.session_state.get("last_draft_workspace")
        if pending_clarification:
            _render_clarification_panel(
                pending=pending_clarification,
                documents=documents,
                active_documents=active_documents,
                doc_type=doc_type,
                top_k=top_k,
                retrieval_mode=retrieval_mode,
                llm_config=llm_config,
                auto_detect_request=auto_detect_request,
            )
        elif workspace:
            _render_chat_draft(
                workspace=workspace,
                agency_parent=agency_parent,
                agency_name=agency_name,
                place_name=place_name,
            )
        else:
            st.markdown(
                """
                <div class="notebook-empty">
                  <div class="empty-emoji">👋</div>
                  <div class="empty-title">Hãy bắt đầu soạn văn bản của bạn...</div>
                  <div class="empty-copy">
                    Đây là không gian để nhập yêu cầu, để hệ thống phân tích chủ thể, ý định,
                    truy xuất mẫu phù hợp và tạo bản nháp hành chính có nguồn tham khảo.
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _start_draft_or_clarification(
    *,
    query: str,
    documents,
    active_documents,
    doc_type,
    top_k,
    retrieval_mode,
    llm_config,
    auto_detect_request,
) -> None:
    analysis = analyze_request(query, default_doc_type=doc_type)
    effective_doc_type = (
        analysis.detected_doc_type
        if auto_detect_request and analysis.confidence >= 0.5
        else doc_type
    )
    if analysis.missing_fields:
        clarification_id = int(st.session_state.get("clarification_index", 0)) + 1
        st.session_state["clarification_index"] = clarification_id
        st.session_state["pending_clarification"] = {
            "id": clarification_id,
            "query": query,
            "analysis": analysis,
            "effective_doc_type": effective_doc_type,
            "selected_doc_type": doc_type,
        }
        st.session_state.pop("last_draft_workspace", None)
        return

    st.session_state.pop("pending_clarification", None)
    _generate_draft_workspace(
        query=query,
        documents=documents,
        active_documents=active_documents,
        doc_type=doc_type,
        top_k=top_k,
        retrieval_mode=retrieval_mode,
        llm_config=llm_config,
        auto_detect_request=auto_detect_request,
        analysis_override=analysis,
        effective_doc_type_override=effective_doc_type,
    )


def _render_clarification_panel(
    *,
    pending,
    documents,
    active_documents,
    doc_type,
    top_k,
    retrieval_mode,
    llm_config,
    auto_detect_request,
) -> None:
    query = pending["query"]
    analysis = pending["analysis"]
    effective_doc_type = pending["effective_doc_type"]
    clarification_id = pending.get("id", "current")
    fields_to_ask = list(analysis.missing_fields[:3])
    if not fields_to_ask:
        st.session_state.pop("pending_clarification", None)
        _generate_draft_workspace(
            query=query,
            documents=documents,
            active_documents=active_documents,
            doc_type=doc_type,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            llm_config=llm_config,
            auto_detect_request=auto_detect_request,
            analysis_override=analysis,
            effective_doc_type_override=effective_doc_type,
        )
        st.rerun()

    st.markdown('<div class="section-title">Cần bổ sung thông tin</div>', unsafe_allow_html=True)
    st.info(
        f"Hệ thống nhận diện loại văn bản là {effective_doc_type} và cần thêm "
        f"{len(fields_to_ask)} thông tin trước khi tạo bản nháp đầy đủ hơn."
    )
    with st.form("clarification_form", clear_on_submit=False):
        answers = {}
        for field in fields_to_ask:
            answers[field] = st.text_input(
                _clarification_label(field),
                value=analysis.slots.get(field, ""),
                key=f"clarify_{clarification_id}_{field}",
                placeholder=_clarification_placeholder(field),
            )
        submit_col, skip_col = st.columns(2)
        with submit_col:
            submit = st.form_submit_button(
                "Bổ sung và tạo bản nháp",
                type="primary",
                use_container_width=True,
            )
        with skip_col:
            skip = st.form_submit_button(
                "Tạo với placeholder",
                use_container_width=True,
            )

    if submit:
        cleaned_answers = {
            field: value.strip()
            for field, value in answers.items()
            if value and value.strip()
        }
        if not cleaned_answers:
            st.warning("Hãy nhập ít nhất một thông tin, hoặc chọn tạo với placeholder.")
            return
        updated_analysis = _apply_clarification_answers(analysis, cleaned_answers)
        st.session_state.pop("pending_clarification", None)
        _generate_draft_workspace(
            query=query,
            documents=documents,
            active_documents=active_documents,
            doc_type=doc_type,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            llm_config=llm_config,
            auto_detect_request=auto_detect_request,
            analysis_override=updated_analysis,
            effective_doc_type_override=effective_doc_type,
        )
        st.rerun()

    if skip:
        st.session_state.pop("pending_clarification", None)
        _generate_draft_workspace(
            query=query,
            documents=documents,
            active_documents=active_documents,
            doc_type=doc_type,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            llm_config=llm_config,
            auto_detect_request=auto_detect_request,
            analysis_override=analysis,
            effective_doc_type_override=effective_doc_type,
        )
        st.rerun()


def _generate_draft_workspace(
    *,
    query: str,
    documents,
    active_documents,
    doc_type,
    top_k,
    retrieval_mode,
    llm_config,
    auto_detect_request,
    analysis_override=None,
    effective_doc_type_override=None,
) -> None:
    analysis = analysis_override or analyze_request(query, default_doc_type=doc_type)
    effective_doc_type = effective_doc_type_override or (
        analysis.detected_doc_type
        if auto_detect_request and analysis.confidence >= 0.5
        else doc_type
    )
    retrieval_query = analysis.retrieval_query if auto_detect_request else query
    results = retrieve(
        retrieval_query,
        active_documents,
        doc_type=effective_doc_type,
        top_k=top_k,
        mode=retrieval_mode,
        project_root=BASE_DIR,
    )
    draft_result = generate_draft(
        request=query,
        doc_type=effective_doc_type,
        search_results=results,
        config=llm_config,
        request_analysis=analysis,
    )
    quality_report = evaluate_draft(
        draft=draft_result.text,
        doc_type=effective_doc_type,
        search_results=results,
    )
    draft_index = int(st.session_state.get("draft_editor_index", 0)) + 1
    st.session_state["draft_editor_index"] = draft_index
    editor_key = f"draft_editor_text_{draft_index}"
    st.session_state[editor_key] = draft_result.text
    st.session_state["last_draft_workspace"] = {
        "query": query,
        "analysis": analysis,
        "effective_doc_type": effective_doc_type,
        "selected_doc_type": doc_type,
        "results": results,
        "retrieval_mode": retrieval_mode,
        "draft_result": draft_result,
        "quality_report": quality_report,
        "editor_key": editor_key,
    }


def _apply_clarification_answers(analysis, answers: dict[str, str]):
    slots = dict(analysis.slots)
    slots.update(answers)
    slots = normalize_slots(analysis.detected_doc_type, slots)
    remaining_missing = [
        field for field in analysis.missing_fields if not slots.get(field)
    ]
    answer_text = " ".join(answers.values())
    retrieval_query = " ".join(
        part for part in [analysis.retrieval_query, answer_text] if part
    ).strip()
    notes = list(analysis.notes)
    notes.append("Người dùng đã bổ sung: " + ", ".join(sorted(answers)))
    return replace(
        analysis,
        slots=slots,
        missing_fields=remaining_missing,
        retrieval_query=retrieval_query,
        notes=notes,
    )


def _clarification_label(field: str) -> str:
    labels = {
        "subject_name": "Họ tên người liên quan",
        "leave_days": "Số ngày nghỉ",
        "start_date": "Ngày bắt đầu",
        "end_date": "Ngày kết thúc",
        "reason": "Lý do",
        "recipient": "Nơi nhận / Kính gửi",
        "topic": "Nội dung chính",
        "approval_target": "Cơ quan/người phê duyệt",
        "invitee": "Người/đơn vị được mời",
        "event_name": "Tên sự kiện/cuộc họp",
        "event_time": "Thời gian",
        "event_location": "Địa điểm",
        "destination": "Nơi đến",
        "purpose": "Mục đích",
        "position": "Chức vụ",
        "department": "Đơn vị công tác",
        "handover_person": "Người nhận bàn giao",
        "legal_basis": "Căn cứ pháp lý",
        "responsible_unit": "Đơn vị chịu trách nhiệm",
        "effective_date": "Ngày hiệu lực",
    }
    return labels.get(field, field.replace("_", " ").title())


def _clarification_placeholder(field: str) -> str:
    placeholders = {
        "subject_name": "Ví dụ: Nguyễn Văn A",
        "leave_days": "Ví dụ: 4",
        "start_date": "Ví dụ: 03/06/2026",
        "end_date": "Ví dụ: 06/06/2026",
        "reason": "Ví dụ: Ốm đau, cần điều trị",
        "recipient": "Ví dụ: Phòng Tổ chức - Hành chính",
        "topic": "Ví dụ: cung cấp số liệu chuyển đổi số",
        "approval_target": "Ví dụ: Ban Giám đốc",
        "invitee": "Ví dụ: Trưởng các đơn vị trực thuộc",
        "event_name": "Ví dụ: Hội nghị sơ kết",
        "event_time": "Ví dụ: 08:00 ngày 05/06/2026",
        "event_location": "Ví dụ: Hội trường tầng 3",
        "destination": "Ví dụ: Sở Nội vụ",
        "purpose": "Ví dụ: liên hệ công tác",
    }
    return placeholders.get(field, "Nhập thông tin bổ sung")


def _render_chat_draft(*, workspace, agency_parent, agency_name, place_name) -> None:
    query = workspace["query"]
    effective_doc_type = workspace["effective_doc_type"]
    selected_doc_type = workspace["selected_doc_type"]
    results = workspace["results"]
    draft_result = workspace["draft_result"]
    retrieval_mode = workspace.get("retrieval_mode", "hybrid")

    st.markdown(
        f"""
        <div class="pill-row">
          <span class="pill">Yêu cầu: {_escape(query[:96])}</span>
          <span class="pill">Loại: {_escape(effective_doc_type)}</span>
          <span class="pill">Nguồn: {len(results)}</span>
          <span class="pill">Truy xuất: {_escape(retrieval_mode)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if effective_doc_type != selected_doc_type:
        st.info(f"Tự động nhận diện loại văn bản: {effective_doc_type}")
    if draft_result.used_llm:
        st.success(f"Sinh bằng {draft_result.provider.upper()} API.")
    if draft_result.fallback_used and draft_result.error:
        st.warning(f"Đã dùng bản sinh dự phòng: {draft_result.error}")

    editor_key = workspace.get("editor_key") or "draft_editor_text_legacy"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = st.session_state.get(
            "draft_editor_text",
            draft_result.text,
        )

    edited_draft = st.text_area(
        "Bản nháp",
        key=editor_key,
        height=540,
        label_visibility="collapsed",
    )
    docx_bytes = export_draft_to_docx(
        draft=edited_draft,
        doc_type=effective_doc_type,
        agency_parent=agency_parent,
        agency_name=agency_name,
        place_name=place_name,
    )
    d1, d2 = st.columns(2)
    d1.download_button(
        "Tải TXT",
        data=edited_draft.encode("utf-8"),
        file_name=f"{effective_doc_type}.txt",
        mime="text/plain",
        use_container_width=True,
    )
    d2.download_button(
        "Tải DOCX",
        data=docx_bytes,
        file_name=f"{effective_doc_type}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )

    live_quality_report = evaluate_draft(
        draft=edited_draft,
        doc_type=effective_doc_type,
        search_results=results,
    )
    workspace["quality_report"] = live_quality_report
    _render_quality_report(
        live_quality_report,
        source_count=len(results),
        retrieval_mode=retrieval_mode,
    )


def _render_studio_panel(*, chunks: list[Document], active_chunks: list[Document], source_scope_label: str) -> None:
    workspace = st.session_state.get("last_draft_workspace")
    with st.container(border=True):
        st.markdown(
            '<div class="panel-heading"><span>Studio</span><span class="panel-icon">▣</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="mini-stat-grid">
              <div class="mini-stat">
                <div class="mini-stat-label">Phạm vi</div>
                <div class="mini-stat-value">{_escape(source_scope_label)}</div>
              </div>
              <div class="mini-stat">
                <div class="mini-stat-label">Chunk</div>
                <div class="mini-stat-value">{len(active_chunks)}/{len(chunks)}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if workspace:
            _render_analysis_panel(workspace["analysis"])
            _render_quality_report(workspace["quality_report"], compact=True)
        else:
            st.markdown(
                """
                <div class="empty-state">
                  Đầu ra của Studio sẽ được lưu ở đây. Sau khi tạo bản nháp,
                  bạn sẽ thấy phân tích yêu cầu, điểm chất lượng và các mục cần rà soát.
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_drafting_tab(*, documents, active_documents, doc_type, top_k, llm_config, source_scope_label, auto_detect_request, agency_parent, agency_name, place_name) -> None:
    prompt_col, action_col = st.columns([5, 1.25], vertical_alignment="bottom")
    with prompt_col:
        st.markdown('<div class="section-title">Yêu cầu soạn thảo</div>', unsafe_allow_html=True)
        query = st.text_area(
            "Yêu cầu soạn thảo",
            height=132,
            label_visibility="collapsed",
        )
    with action_col:
        generate_clicked = st.button("Tạo bản nháp", type="primary", use_container_width=True)

    if generate_clicked:
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

        quality_report = evaluate_draft(draft=draft_result.text, doc_type=effective_doc_type, search_results=results)
        st.session_state["last_draft_workspace"] = {
            "query": query,
            "analysis": analysis,
            "effective_doc_type": effective_doc_type,
            "selected_doc_type": doc_type,
            "results": results,
            "draft_result": draft_result,
            "quality_report": quality_report,
        }

    workspace = st.session_state.get("last_draft_workspace")
    if workspace:
        _render_draft_workspace(
            workspace=workspace,
            agency_parent=agency_parent,
            agency_name=agency_name,
            place_name=place_name,
        )
    else:
        st.markdown(
            """
            <div class="empty-state">
              <strong>Chưa có bản nháp trong phiên này.</strong>
              <div class="pill-row">
                <span class="pill">Công văn</span>
                <span class="pill">Giấy nghỉ phép</span>
                <span class="pill">Tờ trình</span>
                <span class="pill">Quyết định</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def _render_draft_workspace(*, workspace, agency_parent, agency_name, place_name) -> None:
    query = workspace["query"]
    analysis = workspace["analysis"]
    effective_doc_type = workspace["effective_doc_type"]
    selected_doc_type = workspace["selected_doc_type"]
    results = workspace["results"]
    draft_result = workspace["draft_result"]
    quality_report = workspace["quality_report"]

    st.markdown(
        f"""
        <div class="pill-row">
          <span class="pill">Yêu cầu: {_escape(query[:80])}</span>
          <span class="pill">Loại: {_escape(effective_doc_type)}</span>
          <span class="pill">Nguồn: {len(results)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([2.05, 1], gap="large")
    with left:
        st.markdown('<div class="section-title">Bản nháp</div>', unsafe_allow_html=True)
        if effective_doc_type != selected_doc_type:
            st.info(f"Tự động nhận diện loại văn bản: {effective_doc_type}")
        if draft_result.used_llm:
            st.success(f"Sinh bằng {draft_result.provider.upper()} API.")
        if draft_result.fallback_used and draft_result.error:
            st.warning(f"Đã dùng bản sinh dự phòng: {draft_result.error}")

        edited_draft = st.text_area(
            "Nội dung sinh ra",
            value=draft_result.text,
            height=620,
            label_visibility="collapsed",
        )
        docx_bytes = export_draft_to_docx(
            draft=edited_draft,
            doc_type=effective_doc_type,
            agency_parent=agency_parent,
            agency_name=agency_name,
            place_name=place_name,
        )
        d1, d2 = st.columns(2)
        d1.download_button(
            "Tải TXT",
            data=edited_draft.encode("utf-8"),
            file_name=f"{effective_doc_type}.txt",
            mime="text/plain",
            use_container_width=True,
        )
        d2.download_button(
            "Tải DOCX",
            data=docx_bytes,
            file_name=f"{effective_doc_type}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

    with right:
        _render_analysis_panel(analysis)
        _render_search_results(results)

    live_quality_report = evaluate_draft(
        draft=edited_draft,
        doc_type=effective_doc_type,
        search_results=results,
    )
    workspace["quality_report"] = live_quality_report
    _render_quality_report(live_quality_report, source_count=len(results))

def _render_analysis_panel(analysis) -> None:
    st.markdown('<div class="section-title">Phân tích yêu cầu</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.dataframe(analysis_to_rows(analysis), use_container_width=True, hide_index=True)
        if analysis.missing_fields:
            st.caption("Cần bổ sung: " + ", ".join(analysis.missing_fields))

def _render_knowledge_tab(*, source_scope, source_scope_label) -> None:
    st.markdown('<div class="section-title">Kho tri thức</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="section-title">Nguồn truy xuất</div>', unsafe_allow_html=True)
    if not results:
        st.markdown(
            """
            <div class="empty-state">
              Không có nguồn đủ phù hợp trong phạm vi đang chọn.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for r in results:
        st.markdown(
            f"""
            <div class="source-card">
              <div class="source-title">{_escape(r.document.title or r.document.id)}</div>
              <div class="source-meta">{_escape(r.document.doc_type)} · {_escape(SOURCE_KIND_LABELS.get(r.document.source_kind, r.document.source_kind))} · {_escape(getattr(r, "retrieval_method", "bm25"))} · Điểm {r.score:.3f}</div>
              <div class="source-meta">Từ khóa: {_escape(", ".join(r.matched_terms) or "không có")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Xem đoạn nguồn"):
            st.write(r.document.content)

def _render_quality_report(
    report,
    *,
    compact: bool = False,
    source_count: int | None = None,
    retrieval_mode: str | None = None,
) -> None:
    st.markdown('<div class="section-title">Chất lượng bản nháp</div>', unsafe_allow_html=True)
    all_rows = report_to_rows(report)
    failed_checks = [check for check in report.checks if not check.passed]
    failed_rows = [
        row
        for row, check in zip(all_rows, report.checks)
        if not check.passed
    ]

    if compact:
        c1, c2, c3 = st.columns([1, 1, 2])
        c1.metric("Điểm", f"{report.score}/100")
        c2.metric("Rủi ro", report.risk_level)
        c3.metric("Mục cần kiểm tra", len(failed_checks))
        rows_to_show = failed_rows or all_rows
        st.dataframe(
            rows_to_show,
            use_container_width=True,
            hide_index=True,
            height=260,
        )
        return

    metric_columns = st.columns(4)
    c1, c2, c3, c4 = metric_columns
    c1.metric("Điểm", f"{report.score}/100")
    c2.metric("Rủi ro", report.risk_level)
    c3.metric("Mục cần kiểm tra", len(failed_checks))
    if source_count is None:
        c4.metric("Checklist", len(report.checks))
    else:
        source_label = f"{source_count}"
        if retrieval_mode:
            source_label = f"{source_count} ({retrieval_mode})"
        c4.metric("Nguồn dùng", source_label)

    if failed_rows:
        st.warning("Các mục dưới đây cần rà soát trước khi tải hoặc ban hành bản nháp.")
        st.dataframe(
            failed_rows,
            use_container_width=True,
            hide_index=True,
            height=min(260, 80 + len(failed_rows) * 48),
            column_config={
                "status": st.column_config.TextColumn("Trạng thái", width="small"),
                "severity": st.column_config.TextColumn("Mức", width="small"),
                "check": st.column_config.TextColumn("Hạng mục", width="medium"),
                "message": st.column_config.TextColumn("Gợi ý rà soát", width="large"),
            },
        )
    else:
        st.success("Không phát hiện mục lỗi trong checklist tự động.")

    with st.expander("Xem toàn bộ checklist đánh giá", expanded=not failed_rows):
        st.dataframe(
            all_rows,
            use_container_width=True,
            hide_index=True,
            height=min(460, 90 + len(all_rows) * 42),
            column_config={
                "status": st.column_config.TextColumn("Trạng thái", width="small"),
                "severity": st.column_config.TextColumn("Mức", width="small"),
                "check": st.column_config.TextColumn("Hạng mục", width="medium"),
                "message": st.column_config.TextColumn("Thông điệp", width="large"),
            },
        )

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
    with st.expander("Kiểm thử demo Sprint 3/4/6/11/12", expanded=False):
        t1, t2, t3, t4, t5 = st.columns(5)
        if t1.button("Chạy test truy xuất toàn danh mục", use_container_width=True):
            _store_test_result("Truy xuất toàn danh mục", run_retrieval_tests(get_retrieval_test_cases(), chunks))
        if t2.button("Chạy test generator Sprint 4", use_container_width=True):
            _store_test_result("Generator Sprint 4", run_generation_tests(get_generation_test_cases(), chunks))
        if t3.button("Chạy test chất lượng Sprint 6", use_container_width=True):
            _store_test_result("Chất lượng Sprint 6", run_quality_tests(get_generation_test_cases(), chunks))
        if t4.button("Chạy test phân tích yêu cầu", use_container_width=True):
            _store_test_result("Phân tích yêu cầu", run_extraction_tests(get_extraction_test_cases()))
        if t5.button("Chạy test form", use_container_width=True):
            _store_test_result("Form/template", run_form_tests(get_form_test_cases(), chunks))

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

def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)
    
if __name__ == "__main__":
    main()
