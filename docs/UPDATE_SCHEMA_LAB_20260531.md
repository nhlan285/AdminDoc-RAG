# Ghi chép cập nhật schema-lab (so với AdminDoc-RAG)

Ngày: 31/05/2026
Nguồn so sánh: AdminDoc-RAG (bản cũ) vs AdminDoc-RAG-schema-lab (bản hiện tại)

## Tổng quan

Bản schema-lab mở rộng demo RAG cơ bản thành một hệ thống có catalog loại văn bản, hybrid retrieval (BM25 + vector), chuẩn hóa slot đầu vào và bộ kiểm thử form theo từng loại văn bản.

## Các nâng cấp chính

### 1) Danh mục loại văn bản + template

- Thêm `src/doc_type_catalog.py` để load spec JSON, route loại văn bản, xác định section bắt buộc và render template.
- Bổ sung catalog JSON trong `data/doc_types/` cho các loại như Công văn, Thông báo, Tờ trình, Công điện, Giấy mời, Giấy giới thiệu, Giấy nghỉ phép, Biên bản, Quyết định hành chính đơn giản; phần còn lại gom trong `nd30_remaining.json`.
- Thêm nguồn seed nội bộ `data/doc_type_seed_docs.json` để đảm bảo truy xuất đúng loại văn bản.
- `src/generator.py` ưu tiên template từ catalog nếu có, trước khi gọi LLM.
- `src/llm.py` khóa template khi spec có `template_lines` (provider = template).

### 2) Hybrid retrieval + vector index

- Thêm `src/embeddings.py` (local hash, OpenAI, sentence-transformers).
- Thêm `src/vector_store.py` (SQLite vector index, rebuild, search).
- `src/retriever.py` hỗ trợ mode `bm25`/`vector`/`hybrid`, gộp điểm BM25 + vector theo trọng số và đọc config từ `.env`.
- `.env.example` bổ sung các cấu hình retrieval/embedding: `RETRIEVAL_MODE`, trọng số hybrid, `VECTOR_DB_PATH`, `EMBEDDING_PROVIDER`.
- `app.py` hiển thị trạng thái retrieval và có nút tạo lại chỉ mục vector.

### 3) Chuẩn hóa slot + kiểm tra form

- Thêm `src/slot_normalizer.py` để chuẩn hóa ngày, trim cụm thừa, suy ngày kết thúc nghỉ phép.
- `src/extractor.py`:
  - Route loại văn bản theo catalog (fallback theo rule cũ).
  - Bổ sung trích xuất cho Công điện và Biên bản; tách thời gian/địa điểm; cải tiến trích xuất topic.
  - Dùng `missing_required_slots` từ catalog và normalize slot trước khi kiểm tra thiếu dữ liệu.
- `src/quality.py` thêm kiểm tra form: lặp cụm thời gian, chuẩn hóa ngày dd/mm/yyyy, placeholder `{{...}}`, kiểm tra ngày kết thúc nghỉ phép.

### 4) Kiểm thử & trải nghiệm demo

- `src/evaluation.py` thêm `FormTestCase` và `run_form_tests`.
- Thêm `data/form_test_cases.json` để test form tự động theo từng loại văn bản.
- `app.py` bổ sung luồng hỏi bổ sung thông tin thiếu (tối đa 3 trường), vẫn cho phép tạo bản nháp với placeholder.
- Bổ sung script crawl dữ liệu công khai `scripts/crawl_public_sources.py` cùng dữ liệu raw/processed phục vụ demo.

### 5) Tài liệu dự án

- `README.md` cập nhật hướng dẫn, cấu hình, demo nhanh và mô tả hybrid retrieval.
- Thêm `docs/THUYET_TRINH_PROJECT_ADMIN_DOC_RAG.md` cho nội dung thuyết trình.
- Cập nhật `DEMO_SCRIPT.md`, `SPRINTS.md` và các khung báo cáo trong `docs/`.

## Tệp thay đổi nổi bật

- Code: `app.py`, `src/retriever.py`, `src/extractor.py`, `src/quality.py`, `src/evaluation.py`, `src/generator.py`, `src/llm.py`.
- Catalog + data: `data/doc_types/*.json`, `data/doc_type_seed_docs.json`, `data/form_test_cases.json`, `data/retrieval_test_cases.json`, `data/raw/*`.
- Docs: `README.md`, `DEMO_SCRIPT.md`, `SPRINTS.md`, `docs/*`.
- Config: `.env.example`, `requirements.txt`.
