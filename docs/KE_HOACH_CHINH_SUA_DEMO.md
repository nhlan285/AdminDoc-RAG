# Kế hoạch chỉnh sửa demo AdminDoc-RAG

Đề tài: **Xây dựng AI hỗ trợ soạn thảo văn bản hành chính sử dụng mô hình RAG**
Định hướng hiện tại: POC RAG có quản lý dự án theo Scrum, giao diện demo ổn định, catalog loại văn bản và kho tri thức mở rộng.

## 1. Mục tiêu demo

Demo cần chứng minh được luồng cốt lõi:

1. Người dùng nhập yêu cầu soạn thảo.
2. Hệ thống phân tích yêu cầu và nhận diện loại văn bản.
3. Hệ thống truy xuất nguồn liên quan trong kho tri thức.
4. Hệ thống sinh bản nháp có citation `[S1]`, `[S2]`.
5. Hệ thống hiển thị nguồn, phân tích yêu cầu, checklist chất lượng và rủi ro.
6. Người dùng có thể chỉnh sửa và tải bản nháp TXT/DOCX.

Ý tưởng sản phẩm có thể diễn giải gần NotebookLM ở điểm làm việc với kho tài liệu đã nạp và trả lời/sinh nội dung kèm nguồn. Điểm riêng của dự án là tập trung vào văn bản hành chính Việt Nam, có catalog loại văn bản, slot bắt buộc, template thể thức và checklist chất lượng.

## 2. Phạm vi chốt cho POC

In-scope:

- 5 loại văn bản demo: Công văn, Thông báo, Tờ trình, Quyết định hành chính đơn giản, Giấy nghỉ phép.
- Kho tri thức cục bộ bằng JSON, template text, dữ liệu xử lý sau crawl và upload riêng.
- Retriever BM25 nội bộ, hỗ trợ tiếng Việt có dấu và không dấu.
- Tự động nhận diện loại văn bản bằng rule/catalog.
- Bóc tách slot thông tin và phát hiện trường thiếu.
- Generator template/rule-based ổn định và tùy chọn gọi Gemini/OpenAI khi có API key.
- Upload tài liệu `.txt`, `.md`, `.json`, `.pdf`, `.docx`.
- Xuất TXT/DOCX và checklist chất lượng.
- Test demo cho extraction, retrieval, generation và quality.
- Tài liệu Scrum/Sprint, báo cáo kinh tế kỹ thuật, dự toán và thuyết trình.

Out-of-scope:

- Không tự động ký số, phê duyệt hoặc ban hành văn bản.
- Không xử lý văn bản mật/dữ liệu nội bộ cơ quan thật.
- Không tư vấn pháp lý hoặc tự khẳng định hiệu lực văn bản pháp luật.
- Không liên thông hệ thống cấp quốc gia.
- Không huấn luyện mô hình AI mới.
- Không triển khai production server trong phạm vi đồ án.

## 3. Việc đã hoàn thành

Nền tảng RAG:

- Tạo app Streamlit chạy local.
- Xây dựng kho dữ liệu mẫu và chunk tài liệu.
- Thêm module `src/preprocessing.py` để làm sạch, parse và chunk tài liệu.
- Thêm retriever BM25 trong `src/retriever.py`.
- Chuẩn hóa tìm kiếm tiếng Việt có dấu/không dấu.

Sinh văn bản:

- Chuẩn hóa generator cho các loại văn bản demo.
- Bổ sung citation và mục `Nguồn tham khảo`.
- Thêm cảnh báo khi không có nguồn đủ tin cậy.
- Thêm xuất TXT/DOCX qua `src/docx_exporter.py`.

Phân tích yêu cầu:

- Thêm `src/extractor.py` để nhận diện loại văn bản và bóc tách slot.
- Bổ sung ví dụ giấy nghỉ phép: `Xuân Tịnh xin nghỉ 4 ngày vì bị ốm`.
- Phát hiện thông tin còn thiếu và giữ placeholder.

Schema lab:

- Thêm `data/doc_types/*.json` để mô tả loại văn bản.
- Thêm `src/doc_type_catalog.py` để đọc catalog, route loại văn bản, kiểm tra slot bắt buộc và render template.
- Cho phép mở rộng thêm loại văn bản mới bằng JSON thay vì sửa nhiều code.

Kho tri thức/crawler:

- Thêm script `scripts/crawl_public_sources.py`.
- Cập nhật `data/raw/manifest.json`.
- Tải và xử lý một số nguồn công khai như Nghị định 30/2020/NĐ-CP, Quyết định 28/2018/QĐ-TTg.
- Nạp dữ liệu xử lý vào `data/processed/crawled_public_docs.json`.

Giao diện và demo:

- Nâng cấp giao diện theo hướng notebook.
- Sửa lỗi session state khi sinh lại bản nháp sau khi chỉnh prompt.
- Tối giản nút thừa, tập trung vào nguồn, cuộc trò chuyện và bảng phân tích.
- Cập nhật `DEMO_SCRIPT.md`.
- Tạo `docs/THUYET_TRINH_PROJECT_ADMIN_DOC_RAG.md`.

Quản lý dự án:

- Cập nhật `SPRINTS.md`.
- Đồng bộ khung báo cáo kinh tế kỹ thuật.
- Đồng bộ khung báo cáo dự toán.
- Ghi rõ rủi ro, phạm vi, tiêu chí nghiệm thu và hướng phát triển.

## 4. Tiêu chí nghiệm thu trước demo

Kỹ thuật:

- App chạy được bằng `python -m streamlit run app.py`.
- Không còn lỗi đỏ khi sinh lại bản nháp nhiều lần.
- `compileall` chạy không lỗi.
- Có thể demo luồng công văn và giấy nghỉ phép.
- Có thể tải DOCX.

Kiểm thử:

- Extraction: đạt bộ test mẫu.
- Retrieval: đạt bộ test mẫu.
- Generation: đạt bộ test mẫu.
- Quality: đạt bộ test mẫu.

Nghiệp vụ:

- Bản nháp có quốc hiệu/tiêu ngữ hoặc section phù hợp.
- Có nguồn tham khảo/citation khi có nguồn.
- Có cảnh báo khi thiếu nguồn hoặc thiếu thông tin.
- Không tự bịa trường quan trọng như ngày bắt đầu nghỉ.

Quản lý dự án:

- Sprint plan rõ ràng.
- Demo script sẵn sàng.
- Báo cáo kinh tế kỹ thuật và dự toán cùng phạm vi.
- File thuyết trình có cả câu hỏi lý thuyết và code.

## 5. Backlog ưu tiên tiếp theo

1. Bổ sung nhiều loại văn bản hơn bằng `data/doc_types/*.json`.
2. Thêm OCR cho PDF scan.
3. Nâng cấp embedding/vector backend: OpenAI embedding, sentence-transformers, Chroma hoặc Qdrant nếu kho dữ liệu lớn hơn.
4. Tạo ảnh chụp màn hình demo đưa vào báo cáo.
5. Chuẩn hóa dữ liệu crawl: trạng thái downloaded/partial/failed.
6. Mở rộng test form cho nhiều mẫu và biến thể nhập liệu hơn.
7. Viết test riêng cho catalog loại văn bản.
8. Đóng gói Docker nếu cần chạy trên máy khác.

## 6. Kịch bản demo chốt

Luồng 1: Công văn RAG

```text
soạn công văn đề nghị cung cấp số liệu chuyển đổi số
```

Luồng 2: Giấy nghỉ phép tự động nhận diện

```text
Xuân Tịnh xin nghỉ 4 ngày vì bị ốm
```

Luồng 3: Cảnh báo thiếu nguồn

```text
soạn công văn về ký số tự động liên thông quốc gia
```

Luồng 4 nếu còn thời gian:

- Upload file riêng.
- Lọc nguồn chỉ dùng upload.
- Tải DOCX.

## 7. Kết luận

Hướng thống nhất của project là: **RAG có kiểm soát + schema loại văn bản + Scrum/Sprint rõ ràng**. Các file tài liệu, demo và báo cáo cần cùng kể một câu chuyện: sản phẩm là prototype hỗ trợ soạn thảo văn bản hành chính, có nguồn kiểm chứng, có chất lượng đầu ra, có khả năng mở rộng và có quản lý dự án bài bản.
