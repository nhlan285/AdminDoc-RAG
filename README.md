# AdminDoc-RAG

Đề tài: **Xây dựng AI hỗ trợ soạn thảo văn bản hành chính sử dụng mô hình RAG**.

Đây là bản Proof of Concept phục vụ học phần **Quản lý dự án**. Sản phẩm hướng tới vai trò trợ lý soạn thảo: nhận yêu cầu tiếng Việt tự nhiên, truy xuất tài liệu/mẫu liên quan, sinh bản nháp có nguồn tham khảo, kiểm tra chất lượng và xuất file để người dùng rà soát.

## Trạng thái hiện tại

- Nhánh ổn định: `main`.
- Nhánh thử nghiệm mở rộng: `schema-lab-doc-crawler-20260530`.
- Giao diện: Streamlit theo phong cách notebook, tập trung vào 3 vùng chính: nguồn tri thức, cuộc trò chuyện/soạn thảo, bảng phân tích/chất lượng.
- RAG: dùng hybrid search BM25 + vector SQLite, có chuẩn hóa tiếng Việt có dấu/không dấu và fallback BM25 khi vector chưa sẵn sàng.
- Sinh văn bản: ưu tiên template có kiểm soát cho loại văn bản đã có schema; có thể dùng Gemini/OpenAI khi cấu hình `.env`.
- Quản lý dự án: chia sprint rõ trong `SPRINTS.md`, có demo script và khung báo cáo trong `docs/`.

## Chức năng chính

- Nhập yêu cầu soạn thảo bằng tiếng Việt tự nhiên.
- Tự động nhận diện loại văn bản khi bật chế độ phân tích yêu cầu.
- Bóc tách thông tin như chủ thể, số ngày nghỉ, lý do, nơi nhận, thời gian, phạm vi.
- Phát hiện trường còn thiếu, hỏi lại tối đa 3 thông tin quan trọng và vẫn cho phép tạo với placeholder khi cần demo nhanh.
- Chuẩn hóa slot trước khi render form: ngày dạng `dd/mm/yyyy`, tự suy ngày kết thúc nghỉ phép từ ngày bắt đầu và số ngày nghỉ.
- Truy xuất tài liệu liên quan trong kho tri thức bằng hybrid search BM25 + vector.
- Sinh bản nháp có citation `[S1]`, `[S2]` và mục `Nguồn tham khảo`.
- Kiểm tra chất lượng theo rule: thể thức, nguồn, citation, human-in-the-loop.
- Xuất bản nháp dạng TXT/DOCX.
- Upload tài liệu riêng và lọc nguồn theo `system` / `user_upload`.
- Crawl một số nguồn công khai để mở rộng kho tri thức.
- Mở rộng loại văn bản bằng file JSON trong `data/doc_types/`.

## Phạm vi văn bản hiện có

Các loại văn bản trong danh mục hiện đã có schema/template và nguồn seed phục vụ truy xuất:

- Công văn.
- Thông báo.
- Tờ trình.
- Quyết định hành chính đơn giản.
- Nghị quyết.
- Quyết định.
- Chỉ thị.
- Quy chế.
- Quy định.
- Hướng dẫn.
- Thông cáo.
- Báo cáo.
- Biên bản.
- Chương trình.
- Kế hoạch.
- Phương án.
- Đề án.
- Dự án.
- Công điện.
- Bản ghi nhớ.
- Bản thỏa thuận.
- Hợp đồng.
- Giấy ủy quyền.
- Giấy mời.
- Giấy giới thiệu.
- Giấy nghỉ phép.
- Phiếu gửi.
- Phiếu chuyển.
- Phiếu báo.
- Thư công.

Nhánh schema lab đã bổ sung catalog JSON/spec cho toàn bộ danh mục trên. `data/doc_type_seed_docs.json` cung cấp nguồn mẫu nội bộ để truy xuất đúng loại văn bản, còn `data/form_test_cases.json` kiểm tra tự động form/template theo từng loại. Đây vẫn là prototype học thuật: template có khung đúng loại và placeholder rà soát, không thay thế kiểm duyệt pháp lý/thẩm quyền khi dùng thật.

## Cấu trúc thư mục

```text
AdminDoc-RAG/
├── app.py
├── crawler.py
├── data_auditor.py
├── DEMO_SCRIPT.md
├── README.md
├── SPRINTS.md
├── requirements.txt
├── data/
│   ├── admin_docs.json
│   ├── sprint2_sample_docs.json
│   ├── doc_type_seed_docs.json
│   ├── retrieval_test_cases.json
│   ├── generation_test_cases.json
│   ├── extraction_test_cases.json
│   ├── doc_types/
│   ├── templates/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── THUYET_TRINH_PROJECT_ADMIN_DOC_RAG.md
│   ├── KE_HOACH_CHINH_SUA_DEMO.md
│   ├── BAO_CAO_KINH_TE_KY_THUAT_KHUNG.md
│   └── BAO_CAO_DU_TOAN_KHUNG.md
├── scripts/
│   ├── crawl_public_sources.py
│   └── template_converter.py
└── src/
    ├── documents.py
    ├── embeddings.py
    ├── preprocessing.py
    ├── retriever.py
    ├── vector_store.py
    ├── extractor.py
    ├── doc_type_catalog.py
    ├── generator.py
    ├── llm.py
    ├── quality.py
    ├── docx_exporter.py
    ├── storage.py
    └── evaluation.py
```

## Luồng xử lý

```text
Người dùng nhập yêu cầu
  -> app.py nhận input
  -> src/extractor.py phân tích yêu cầu
  -> src/doc_type_catalog.py chọn loại văn bản/schema
  -> src/retriever.py truy xuất nguồn liên quan bằng hybrid BM25 + vector
  -> src/generator.py hoặc src/llm.py sinh bản nháp
  -> src/quality.py kiểm tra chất lượng
  -> src/docx_exporter.py xuất DOCX
```

## Cài đặt

```powershell
cd E:\.vscode\Ki_6\RAG\AdminDoc-RAG-schema-lab
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Nếu đã có môi trường ảo:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Chạy demo

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

Nếu port 8501 đang bận:

```powershell
.\.venv\Scripts\python -m streamlit run app.py --server.port 8502
```

## Cấu hình LLM

Mock mode giúp demo chạy ổn định ngay cả khi không có API key:

```env
LLM_PROVIDER=mock
```

Dùng Gemini:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_TIMEOUT_SECONDS=30
GEMINI_MAX_OUTPUT_TOKENS=1800
```

Dùng OpenAI:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=your_model_here
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_OUTPUT_TOKENS=1800
```

Không commit `.env` lên git.

## Cấu hình truy xuất hybrid

Mặc định hệ thống chạy `RETRIEVAL_MODE=hybrid`: BM25 giữ độ chính xác từ khóa, vector search hỗ trợ truy vấn gần nghĩa. Vector index được lưu cùng SQLite local tại `data/knowledge.sqlite`.

```env
RETRIEVAL_MODE=hybrid
HYBRID_BM25_WEIGHT=0.7
HYBRID_VECTOR_WEIGHT=0.3
VECTOR_DB_PATH=data/knowledge.sqlite
HYBRID_ALLOW_VECTOR_ONLY=false
EMBEDDING_PROVIDER=local_hash
EMBEDDING_DIMENSIONS=384
```

`local_hash` chạy offline để demo không cần API key. App mặc định dùng hybrid và không nhận nguồn chỉ có vector để tránh kéo nhầm nguồn yếu vào bản nháp. Khi cần tìm kiếm ngữ nghĩa tốt hơn, có thể đổi sang OpenAI embedding:

```env
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Trong giao diện người dùng không cần chọn thuật toán truy xuất; hệ thống tự chạy hybrid. Phần `Nâng cao` vẫn có nút tạo lại chỉ mục vector khi dữ liệu thay đổi nhiều.

## Demo nhanh

Luồng công văn:

```text
soạn công văn đề nghị cung cấp số liệu chuyển đổi số
```

Luồng tự động nhận diện giấy nghỉ phép:

```text
Xuân Tịnh xin nghỉ 4 ngày vì bị ốm
```

Ca thiếu nguồn:

```text
soạn công văn về ký số tự động liên thông quốc gia
```

Kịch bản demo chi tiết nằm ở `DEMO_SCRIPT.md`. Nội dung thuyết trình và câu hỏi vấn đáp nằm ở `docs/THUYET_TRINH_PROJECT_ADMIN_DOC_RAG.md`.

## Crawl dữ liệu công khai

Script crawl trong nhánh lab:

```powershell
.\.venv\Scripts\python scripts\crawl_public_sources.py --manifest data\raw\manifest.json --output data\processed\crawled_public_docs.json
```

Lưu ý:

- Crawl chỉ là phần mở rộng kho tri thức, không bắt buộc cho demo chính.
- PDF scan hoặc file `.doc` cũ có thể trích xuất kém.
- Nội dung sau crawl cần được kiểm tra thủ công trước khi dùng làm nguồn chính thức.

## Kiểm thử nhanh

```powershell
.\.venv\Scripts\python -m compileall -q app.py src scripts\crawl_public_sources.py crawler.py data_auditor.py
```

Bộ test demo nằm trong:

- `data/extraction_test_cases.json`
- `data/retrieval_test_cases.json` - gồm test truy xuất toàn danh mục loại văn bản.
- `data/generation_test_cases.json`
- `data/form_test_cases.json` - phủ 30/30 loại văn bản trong catalog.

## Tài liệu quản lý dự án

- `SPRINTS.md`: kế hoạch sprint, tiêu chí nghiệm thu, trạng thái từng sprint.
- `DEMO_SCRIPT.md`: kịch bản demo ngắn 3-5 phút.
- `docs/THUYET_TRINH_PROJECT_ADMIN_DOC_RAG.md`: nội dung thuyết trình và bộ câu hỏi có thể bị hỏi.
- `docs/BAO_CAO_KINH_TE_KY_THUAT_KHUNG.md`: khung báo cáo kinh tế kỹ thuật.
- `docs/BAO_CAO_DU_TOAN_KHUNG.md`: khung dự toán.
- `docs/KE_HOACH_CHINH_SUA_DEMO.md`: kế hoạch chỉnh sửa demo.

## Phạm vi và giới hạn

Sản phẩm hiện là prototype học thuật. Hệ thống chỉ hỗ trợ tạo bản nháp, không tự ban hành văn bản, không ký số, không thay thế trách nhiệm kiểm duyệt của người có thẩm quyền. Khi triển khai thật cần bổ sung phân quyền, kiểm duyệt nguồn, nhật ký thao tác, bảo mật dữ liệu, OCR tốt hơn và quy trình pháp lý rõ ràng.
