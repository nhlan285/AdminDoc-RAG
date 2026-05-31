# Kịch bản demo AdminDoc-RAG

Thời lượng mục tiêu: 3-5 phút.
Mục tiêu: chứng minh hệ thống có luồng RAG hoàn chỉnh, có quản lý nguồn, có phân tích yêu cầu, có kiểm soát chất lượng và có xuất file.

## 1. Chuẩn bị

Chạy app:

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

Nếu port 8501 đang bận:

```powershell
.\.venv\Scripts\python -m streamlit run app.py --server.port 8502
```

Mở trình duyệt tại URL Streamlit hiển thị trong terminal.

Trước khi demo nên kiểm tra:

- `.env` đã để `LLM_PROVIDER=mock` hoặc cấu hình Gemini/OpenAI hợp lệ.
- Kho tri thức đã có tài liệu mẫu.
- Không có lỗi đỏ trên giao diện.

## 2. Lời mở đầu

Nói ngắn gọn:

> Đây là hệ thống AI hỗ trợ soạn thảo văn bản hành chính bằng RAG. Hệ thống không thay thế người soạn thảo mà giúp tạo bản nháp nhanh hơn, có nguồn tham khảo và có checklist để con người rà soát.

## 3. Demo luồng RAG chính

1. Ở khu vực nguồn, chỉ ra kho tri thức gồm tài liệu hệ thống, template và dữ liệu đã xử lý.
2. Chọn nguồn dùng khi soạn là `Tất cả nguồn`.
3. Nhập yêu cầu:

```text
soạn công văn đề nghị cung cấp số liệu chuyển đổi số
```

4. Bấm `Tạo bản nháp`.
5. Trình bày các điểm chính:
   - Hệ thống truy xuất nguồn liên quan bằng BM25.
   - Bản nháp có marker nguồn như `[S1]`.
   - Có phần `Nguồn tham khảo`.
   - Có checklist chất lượng và mức rủi ro.
   - Có thể tải TXT/DOCX.

Thông điệp cần nhấn mạnh:

> Khác với chatbot viết tự do, hệ thống này luôn gắn bản nháp với nguồn truy xuất và cảnh báo khi thiếu căn cứ.

## 4. Demo tự động nhận diện yêu cầu

1. Giữ bật chế độ tự động nhận diện yêu cầu.
2. Nhập:

```text
Xuân Tịnh xin nghỉ 4 ngày vì bị ốm
```

3. Bấm `Tạo bản nháp`.
4. Trình bày:
   - Hệ thống nhận diện loại văn bản là `Giấy nghỉ phép`.
   - Bảng phân tích yêu cầu bóc tách `subject_name`, `leave_days`, `reason`.
   - Các trường thiếu như `start_date` được giữ bằng placeholder.
   - Bản nháp không tự bịa ngày nghỉ nếu người dùng chưa cung cấp.

Thông điệp cần nhấn mạnh:

> Đây là bước chuẩn bị để sau này hệ thống có thể tự hỏi lại thông tin thiếu trước khi sinh văn bản cuối.

## 5. Demo schema/catalog loại văn bản

Mở nhanh thư mục hoặc trình bày bằng lời:

- Các file schema nằm trong `data/doc_types/`.
- Mỗi loại văn bản có alias, ví dụ nhận diện, trường bắt buộc, section bắt buộc và template.
- Khi muốn thêm loại văn bản mới, không cần viết lại toàn bộ app; chỉ cần thêm file JSON và tài liệu mẫu tương ứng.

Ví dụ file:

```text
data/doc_types/giay_nghi_phep.json
data/doc_types/to_trinh.json
data/doc_types/thong_bao.json
```

Thông điệp cần nhấn mạnh:

> Thiết kế này giúp hệ thống mở rộng được từ vài loại văn bản lên nhiều loại văn bản khác nhau.

## 6. Demo upload hoặc crawl nguồn

Nếu còn thời gian:

1. Mở khu vực nguồn/kho tri thức.
2. Upload một file `.txt`, `.md`, `.json`, `.pdf` hoặc `.docx`.
3. Chỉ ra tài liệu upload được gắn nhóm nguồn riêng.
4. Đổi nguồn dùng khi soạn sang chỉ dùng upload để chứng minh hệ thống có kiểm soát nguồn.

Nếu trình bày crawler bằng lời:

```powershell
.\.venv\Scripts\python scripts\crawl_public_sources.py --manifest data\raw\manifest.json --output data\processed\crawled_public_docs.json
```

Nói rõ:

> Crawler là phần mở rộng kho tri thức. Dữ liệu sau crawl cần được kiểm tra lại vì một số PDF scan hoặc file DOC cũ có thể trích xuất không đầy đủ.

## 7. Demo kiểm soát rủi ro

Nhập:

```text
soạn công văn về ký số tự động liên thông quốc gia
```

Trình bày:

- Nếu kho tri thức không có nguồn đủ phù hợp, hệ thống cảnh báo.
- Đây là cơ chế giảm ảo giác.
- Người dùng cần bổ sung nguồn hoặc chỉnh phạm vi yêu cầu.

## 8. Liên hệ với Scrum

Nói ngắn gọn:

> Dự án được chia thành các sprint: đầu tiên là app mô phỏng, sau đó là kho tri thức, retriever BM25, generator theo loại văn bản, LLM provider, quality check, giao diện demo và cuối cùng là schema lab/crawler/tài liệu báo cáo. Mỗi sprint đều có tiêu chí nghiệm thu và sản phẩm chạy được.

## 9. Câu kết demo

> AdminDoc-RAG đã có luồng POC hoàn chỉnh: nhận yêu cầu, phân tích thông tin, truy xuất nguồn, sinh bản nháp, kiểm tra chất lượng và xuất file. Điểm quan trọng là hệ thống giữ vai trò trợ lý có kiểm soát, không thay thế con người trong việc kiểm duyệt văn bản hành chính.
