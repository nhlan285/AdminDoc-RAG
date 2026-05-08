from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.documents import Document, load_documents
from src.docx_exporter import export_draft_to_docx
from src.evaluation import (
    load_generation_test_cases,
    load_retrieval_test_cases,
    run_quality_tests,
    run_generation_tests,
    run_retrieval_tests,
)
from src.llm import LLMConfig, describe_llm_status, generate_draft, load_llm_config
from src.preprocessing import build_chunks, decode_file_bytes, parse_documents_from_text
from src.quality import evaluate_draft, report_to_rows
from src.retriever import retrieve


BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "admin_docs.json"
SPRINT2_SAMPLE_PATH = BASE_DIR / "data" / "sprint2_sample_docs.json"
RETRIEVAL_TEST_CASES_PATH = BASE_DIR / "data" / "retrieval_test_cases.json"
GENERATION_TEST_CASES_PATH = BASE_DIR / "data" / "generation_test_cases.json"
DOCUMENT_TYPES = [
    "Công văn",
    "Thông báo",
    "Tờ trình",
    "Quyết định hành chính đơn giản",
]
SOURCE_SCOPE_OPTIONS = {
    "Tất cả nguồn": None,
    "Chỉ nguồn hệ thống/mẫu": "system",
    "Chỉ tài liệu upload": "user_upload",
}
SOURCE_KIND_LABELS = {
    "system": "Hệ thống/mẫu",
    "user_upload": "Upload riêng",
}


@st.cache_data
def get_base_documents() -> list[Document]:
    return load_documents(DATA_PATH)


@st.cache_data
def get_sprint2_sample_documents() -> list[Document]:
    return load_documents(SPRINT2_SAMPLE_PATH)


@st.cache_data
def get_retrieval_test_cases():
    return load_retrieval_test_cases(RETRIEVAL_TEST_CASES_PATH)


@st.cache_data
def get_generation_test_cases():
    return load_generation_test_cases(GENERATION_TEST_CASES_PATH)


def main() -> None:
    st.set_page_config(
        page_title="AI soạn thảo văn bản hành chính",
        layout="wide",
    )

    _ensure_knowledge_base()
    chunks = _current_chunks()
    llm_config = load_llm_config(BASE_DIR)

    st.title("AI hỗ trợ soạn thảo văn bản hành chính")
    st.caption("Bản nháp hành chính có nguồn tham khảo và bước rà soát của con người.")

    with st.sidebar:
        st.header("Cấu hình")
        doc_type = st.selectbox("Loại văn bản", DOCUMENT_TYPES)
        top_k = st.slider("Số tài liệu truy xuất", min_value=1, max_value=8, value=3)
        source_scope_label = st.selectbox("Nguồn dùng khi soạn", list(SOURCE_SCOPE_OPTIONS))
        source_scope = SOURCE_SCOPE_OPTIONS[source_scope_label]
        active_chunks = _filter_chunks_by_source_scope(chunks, source_scope)
        st.divider()
        st.metric("Chunk trong kho", len(chunks))
        st.metric("Chunk đang dùng", len(active_chunks))
        st.metric("Tài liệu gốc", len(_parent_ids(chunks)))
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
            documents=chunks,
            active_documents=active_chunks,
            doc_type=doc_type,
            top_k=top_k,
            llm_config=llm_config,
            source_scope_label=source_scope_label,
            agency_parent=agency_parent,
            agency_name=agency_name,
            place_name=place_name,
        )

    with knowledge_tab:
        _render_knowledge_tab(source_scope=source_scope, source_scope_label=source_scope_label)


def _ensure_knowledge_base() -> None:
    if "knowledge_chunks" in st.session_state:
        return

    base_chunks = build_chunks(get_base_documents())
    st.session_state["knowledge_chunks"] = base_chunks
    st.session_state["import_log"] = [
        f"Đã nạp {len(base_chunks)} chunk nền từ data/admin_docs.json."
    ]


def _current_chunks() -> list[Document]:
    return st.session_state.get("knowledge_chunks", [])


def _render_drafting_tab(
    *,
    documents: list[Document],
    active_documents: list[Document],
    doc_type: str,
    top_k: int,
    llm_config: LLMConfig,
    source_scope_label: str,
    agency_parent: str,
    agency_name: str,
    place_name: str,
) -> None:
    st.caption(
        f"Luồng Sprint 7: nhập yêu cầu -> truy xuất ({source_scope_label}) -> sinh nháp -> rà soát -> tải TXT/DOCX."
    )
    query = st.text_area(
        "Yêu cầu soạn thảo",
        height=150,
        placeholder="Ví dụ: soạn công văn đề nghị phối hợp tổ chức buổi tập huấn chuyển đổi số cho cán bộ văn phòng",
    )

    submitted = st.button("Tạo bản nháp", type="primary", use_container_width=True)

    if submitted:
        if not query.strip():
            st.warning("Vui lòng nhập yêu cầu soạn thảo trước khi tạo bản nháp.")
            return
        if documents and not active_documents:
            st.warning(
                f"Không có tài liệu trong phạm vi `{source_scope_label}`. Hãy đổi bộ lọc nguồn hoặc nạp thêm tài liệu."
            )
            return

        results = retrieve(query, active_documents, doc_type=doc_type, top_k=top_k)
        draft_result = generate_draft(
            request=query,
            doc_type=doc_type,
            search_results=results,
            config=llm_config,
        )

        left, right = st.columns([2, 1])
        quality_report = evaluate_draft(
            draft=draft_result.text,
            doc_type=doc_type,
            search_results=results,
        )
        with left:
            st.subheader("Bản nháp")
            if draft_result.used_llm:
                st.success(
                    f"Đã sinh bằng {draft_result.provider.upper()} API ({draft_result.model})."
                )
            elif draft_result.fallback_used and draft_result.error:
                st.warning(draft_result.error)
            st.text_area("Nội dung sinh ra", value=draft_result.text, height=560)
            docx_bytes = export_draft_to_docx(
                draft=draft_result.text,
                doc_type=doc_type,
                agency_parent=agency_parent,
                agency_name=agency_name,
                place_name=place_name,
            )
            download_txt_col, download_docx_col = st.columns(2)
            with download_txt_col:
                st.download_button(
                    "Tải bản nháp TXT",
                    data=draft_result.text.encode("utf-8"),
                    file_name=_txt_file_name(doc_type),
                    mime="text/plain; charset=utf-8",
                    use_container_width=True,
                )
            with download_docx_col:
                st.download_button(
                    "Tải bản nháp DOCX chuẩn thể thức",
                    data=docx_bytes,
                    file_name=_docx_file_name(doc_type),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            st.caption(
                "DOCX dùng khổ A4, Times New Roman, lề trái 30 mm, lề phải 15 mm, lề trên/dưới 20 mm, cỡ chữ nội dung 13, giãn dòng 1.15 và số trang căn giữa ở lề trên, ẩn trang đầu."
            )

        with right:
            st.subheader("Nguồn truy xuất")
            _render_search_results(results)
            st.warning(
                "Bản nháp chỉ dùng để hỗ trợ. Cần con người rà soát căn cứ pháp lý, thể thức và thẩm quyền ban hành."
            )

        _render_quality_report(quality_report)
    else:
        st.info("Chưa có bản nháp.")


def _render_knowledge_tab(*, source_scope: str | None, source_scope_label: str) -> None:
    st.subheader("Nạp và kiểm tra kho tri thức")

    chunks = _current_chunks()
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Chunk", len(chunks))
    col_b.metric("Tài liệu gốc", len(_parent_ids(chunks)))
    col_c.metric("Upload riêng", len(_filter_chunks_by_source_scope(chunks, "user_upload")))
    col_d.metric("Loại văn bản", len({document.doc_type for document in chunks}))

    action_col, delete_upload_col, reset_col = st.columns([2, 1, 1])
    with action_col:
        if st.button("Nạp 5 tài liệu mẫu Sprint 2/3/4", type="primary"):
            sample_chunks = build_chunks(get_sprint2_sample_documents())
            added = _merge_chunks(sample_chunks)
            st.success(f"Đã nạp thêm {added} chunk từ bộ dữ liệu mẫu Sprint 2/3/4.")

    with delete_upload_col:
        if st.button("Xóa upload riêng"):
            removed = _delete_user_upload_chunks()
            st.success(f"Đã xóa {removed} chunk upload riêng khỏi phiên làm việc.")

    with reset_col:
        if st.button("Reset kho tri thức"):
            base_chunks = build_chunks(get_base_documents())
            st.session_state["knowledge_chunks"] = base_chunks
            st.session_state["import_log"] = [
                f"Đã reset về {len(base_chunks)} chunk nền từ data/admin_docs.json."
            ]
            st.success("Đã reset kho tri thức về dữ liệu nền.")

    with st.expander("Upload tài liệu riêng .txt, .md hoặc .json", expanded=True):
        st.warning(
            "Chỉ upload tài liệu được phép dùng cho demo. Không đưa tài liệu mật, dữ liệu cá nhân hoặc file chưa được phép chia sẻ vào kho tri thức."
        )
        upload_doc_type = st.selectbox("Loại mặc định cho file txt/md", DOCUMENT_TYPES)
        chunk_size = st.slider("Số từ tối đa mỗi chunk", 60, 220, 120, step=20)
        overlap = st.slider("Số từ overlap giữa các chunk", 0, 60, 20, step=10)
        uploaded_files = st.file_uploader(
            "Chọn file",
            type=["txt", "md", "json"],
            accept_multiple_files=True,
        )

        if st.button("Nạp file đã chọn"):
            if not uploaded_files:
                st.warning("Vui lòng chọn ít nhất một file trước khi nạp.")
            else:
                added_documents, errors = _parse_uploaded_files(
                    uploaded_files=uploaded_files,
                    default_doc_type=upload_doc_type,
                )
                uploaded_chunks = build_chunks(
                    added_documents,
                    chunk_size_words=chunk_size,
                    overlap_words=overlap,
                )
                added = _merge_chunks(uploaded_chunks)

                if added:
                    st.success(
                        f"Đã nạp thêm {added} chunk upload riêng từ {len(added_documents)} tài liệu."
                    )
                if errors:
                    st.error("\n".join(errors))

    st.divider()
    st.subheader("Danh sách chunk trong kho")
    rows = _chunk_rows(_current_chunks())
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("Kiểm tra truy xuất")
    st.caption(f"Đang kiểm tra với phạm vi nguồn: {source_scope_label}.")
    preview_query = st.text_input(
        "Câu hỏi kiểm tra",
        value="soạn công văn đề nghị cung cấp số liệu chuyển đổi số",
    )
    preview_doc_type = st.selectbox(
        "Ưu tiên loại văn bản",
        ["Không lọc"] + DOCUMENT_TYPES,
    )
    if preview_query.strip():
        doc_type_filter = None if preview_doc_type == "Không lọc" else preview_doc_type
        results = retrieve(
            preview_query,
            _filter_chunks_by_source_scope(_current_chunks(), source_scope),
            doc_type=doc_type_filter,
            top_k=5,
        )
        _render_search_results(results)

    _render_retrieval_test_panel()
    _render_generation_test_panel()
    _render_quality_test_panel()

    with st.expander("Nhật ký nạp dữ liệu"):
        for line in st.session_state.get("import_log", []):
            st.write(f"- {line}")


def _parse_uploaded_files(
    *,
    uploaded_files,
    default_doc_type: str,
) -> tuple[list[Document], list[str]]:
    documents: list[Document] = []
    errors: list[str] = []

    for uploaded_file in uploaded_files:
        try:
            text = decode_file_bytes(uploaded_file.getvalue())
            parsed = parse_documents_from_text(
                filename=uploaded_file.name,
                text=text,
                default_doc_type=default_doc_type,
                source_kind="user_upload",
            )
            documents.extend(parsed)
        except json.JSONDecodeError as error:
            errors.append(f"{uploaded_file.name}: JSON không hợp lệ ({error.msg}).")
        except ValueError as error:
            errors.append(f"{uploaded_file.name}: {error}.")

    return documents, errors


def _merge_chunks(new_chunks: list[Document]) -> int:
    current_chunks = _current_chunks()
    existing_ids = {document.id for document in current_chunks}
    unique_new_chunks = [
        document for document in new_chunks if document.id not in existing_ids
    ]

    st.session_state["knowledge_chunks"] = current_chunks + unique_new_chunks
    st.session_state.setdefault("import_log", []).append(
        f"Đã nạp {len(unique_new_chunks)} chunk mới, bỏ qua {len(new_chunks) - len(unique_new_chunks)} chunk trùng."
    )
    return len(unique_new_chunks)


def _delete_user_upload_chunks() -> int:
    current_chunks = _current_chunks()
    kept_chunks = [
        document for document in current_chunks if document.source_kind != "user_upload"
    ]
    removed = len(current_chunks) - len(kept_chunks)
    st.session_state["knowledge_chunks"] = kept_chunks
    st.session_state.setdefault("import_log", []).append(
        f"Đã xóa {removed} chunk upload riêng khỏi kho tri thức phiên hiện tại."
    )
    return removed


def _render_retrieval_test_panel() -> None:
    st.subheader("Bộ test truy xuất Sprint 3")
    test_cases = get_retrieval_test_cases()
    st.caption(
        "Các test này kiểm tra kết quả top 3 của BM25 retriever trên bộ dữ liệu mẫu."
    )

    with st.expander("Danh sách test case"):
        st.dataframe(
            [
                {
                    "id": case.id,
                    "query": case.query,
                    "doc_type": case.doc_type or "Không lọc",
                    "expected": case.expected_parent_id,
                    "description": case.description,
                }
                for case in test_cases
            ],
            use_container_width=True,
            hide_index=True,
        )

    if st.button("Chạy test truy xuất Sprint 3"):
        rows = run_retrieval_tests(test_cases, _current_chunks(), top_k=3)
        passed_count = sum(1 for row in rows if row["passed"])
        total_count = len(rows)

        if passed_count == total_count:
            st.success(f"Đạt {passed_count}/{total_count} test truy xuất.")
        else:
            st.warning(
                f"Đạt {passed_count}/{total_count} test. Nếu chưa nạp dữ liệu mẫu Sprint 2/3/4, hãy nạp trước rồi chạy lại."
            )

        st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_generation_test_panel() -> None:
    st.subheader("Bộ test generator Sprint 4")
    test_cases = get_generation_test_cases()
    st.caption(
        "Các test này kiểm tra template riêng cho từng loại văn bản và ca không có nguồn."
    )

    with st.expander("Danh sách test generator"):
        st.dataframe(
            [
                {
                    "id": case.id,
                    "query": case.query,
                    "doc_type": case.doc_type,
                    "description": case.description,
                }
                for case in test_cases
            ],
            use_container_width=True,
            hide_index=True,
        )

    if st.button("Chạy test generator Sprint 4"):
        rows = run_generation_tests(test_cases, _current_chunks(), top_k=3)
        passed_count = sum(1 for row in rows if row["passed"])
        total_count = len(rows)

        if passed_count == total_count:
            st.success(f"Đạt {passed_count}/{total_count} test generator.")
        else:
            st.warning(
                f"Đạt {passed_count}/{total_count} test. Nếu chưa nạp dữ liệu mẫu Sprint 2/3/4, hãy nạp trước rồi chạy lại."
            )

        st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_quality_test_panel() -> None:
    st.subheader("Bộ test chất lượng Sprint 6")
    test_cases = get_generation_test_cases()
    st.caption(
        "Các test này kiểm tra checklist thể thức, citation và rủi ro thiếu nguồn."
    )

    if st.button("Chạy test chất lượng Sprint 6"):
        rows = run_quality_tests(test_cases, _current_chunks(), top_k=3)
        passed_count = sum(1 for row in rows if row["passed"])
        total_count = len(rows)

        if passed_count == total_count:
            st.success(f"Đạt {passed_count}/{total_count} test chất lượng.")
        else:
            st.warning(
                f"Đạt {passed_count}/{total_count} test. Hãy nạp dữ liệu mẫu Sprint 2/3/4 trước khi chạy."
            )

        st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_quality_report(report) -> None:
    st.subheader("Checklist chất lượng")
    metric_a, metric_b = st.columns(2)
    metric_a.metric("Điểm chất lượng", f"{report.score}/100")
    metric_b.metric("Mức rủi ro", report.risk_level)

    if report.risk_level == "Cao":
        st.error("Rủi ro cao: cần bổ sung nguồn hoặc rà soát kỹ trước khi sử dụng.")
    elif report.risk_level == "Trung bình":
        st.warning("Rủi ro trung bình: cần kiểm tra các mục chưa đạt.")
    else:
        st.success("Rủi ro thấp: vẫn cần con người rà soát lần cuối.")

    st.dataframe(report_to_rows(report), use_container_width=True, hide_index=True)


def _render_search_results(results) -> None:
    if not results:
        st.warning("Chưa có nguồn đủ phù hợp trong kho tri thức. Cần bổ sung dữ liệu trước khi sinh nội dung.")
        return

    for result in results:
        document = result.document
        chunk_label = (
            f"chunk {document.chunk_index}/{document.total_chunks}"
            if document.chunk_index and document.total_chunks
            else "toàn văn"
        )
        with st.expander(f"{document.id} · {document.title}", expanded=True):
            st.caption(
                f"{_source_kind_label(document.source_kind)} · {document.doc_type} · {chunk_label} · điểm BM25 {result.score:.3f}"
            )
            st.write(document.content)
            st.caption(f"Nguồn: {document.source}")
            if result.matched_terms:
                st.caption(f"Từ khóa khớp: {', '.join(result.matched_terms)}")


def _chunk_rows(chunks: list[Document]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for document in chunks:
        rows.append(
            {
                "id": document.id,
                "parent_id": document.parent_id,
                "doc_type": document.doc_type,
                "source_kind": _source_kind_label(document.source_kind),
                "title": document.title,
                "source": document.source,
                "chunk": _chunk_label(document),
                "words": len(document.content.split()),
                "preview": document.content[:160],
            }
        )

    return rows


def _chunk_label(document: Document) -> str:
    if document.chunk_index and document.total_chunks:
        return f"{document.chunk_index}/{document.total_chunks}"

    return "-"


def _parent_ids(chunks: list[Document]) -> set[str]:
    return {document.parent_id or document.id for document in chunks}


def _filter_chunks_by_source_scope(
    chunks: list[Document],
    source_scope: str | None,
) -> list[Document]:
    if source_scope is None:
        return chunks

    return [document for document in chunks if document.source_kind == source_scope]


def _source_kind_label(source_kind: str) -> str:
    return SOURCE_KIND_LABELS.get(source_kind, source_kind or "Không rõ")


def _docx_file_name(doc_type: str) -> str:
    mapping = {
        "Công văn": "cong-van",
        "Thông báo": "thong-bao",
        "Tờ trình": "to-trinh",
        "Quyết định hành chính đơn giản": "quyet-dinh",
    }
    return f"ban-nhap-{mapping.get(doc_type, 'van-ban')}.docx"


def _txt_file_name(doc_type: str) -> str:
    mapping = {
        "Công văn": "cong-van",
        "Thông báo": "thong-bao",
        "Tờ trình": "to-trinh",
        "Quyết định hành chính đơn giản": "quyet-dinh",
    }
    return f"ban-nhap-{mapping.get(doc_type, 'van-ban')}.txt"


if __name__ == "__main__":
    main()
