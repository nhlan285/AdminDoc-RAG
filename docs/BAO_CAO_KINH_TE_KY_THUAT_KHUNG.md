# Khung báo cáo kinh tế kỹ thuật

## 1. Thông tin chung

- Tên dự án: Xây dựng AI hỗ trợ soạn thảo văn bản hành chính sử dụng mô hình RAG.
- Loại dự án: Proof of Concept phục vụ học phần Quản lý dự án CNTT.
- Đơn vị thực hiện: Nhóm sinh viên.
- Người dùng giả định: Cán bộ/nhân viên hành chính văn phòng cần công cụ hỗ trợ soạn thảo bản nháp.

## 2. Sự cần thiết đầu tư

Quy trình soạn thảo văn bản hành chính thường mất thời gian ở khâu tra cứu mẫu, đối chiếu thể thức và tổng hợp thông tin. AI tạo sinh có thể hỗ trợ viết nháp nhanh, nhưng dễ phát sinh rủi ro ảo giác nếu không có nguồn kiểm chứng. Vì vậy, dự án chọn RAG để kết hợp khả năng sinh nội dung của LLM với kho tri thức văn bản hành chính đã kiểm soát.

## 3. Mục tiêu

- Xây dựng demo nhận yêu cầu, truy xuất tài liệu liên quan và sinh bản nháp hành chính.
- Giữ nguyên nguyên tắc human-in-the-loop: con người kiểm duyệt trước khi sử dụng.
- Hạn chế ảo giác bằng citation và cảnh báo khi thiếu nguồn.
- Cung cấp bằng chứng kiểm thử cho retrieval, generation và quality.

## 4. Phạm vi kỹ thuật

Thành phần chính:

- Giao diện Streamlit.
- Kho tri thức JSON và tài liệu upload.
- SQLite local để quản lý chunk/metadata ở mức POC.
- Tiền xử lý/chunking tài liệu.
- Phân tích yêu cầu và bóc tách slot.
- Retriever BM25 cục bộ.
- Generator mock và lớp provider LLM.
- Quality checker rule-based.
- Xuất TXT/DOCX.

Phạm vi văn bản demo:

- Công văn.
- Thông báo.
- Tờ trình.
- Quyết định hành chính đơn giản.

## 5. Phương án công nghệ

- Python cho backend và xử lý tài liệu.
- Streamlit cho giao diện demo.
- BM25 cục bộ cho truy xuất, phù hợp POC vì dễ giải thích và không cần hạ tầng vector database thật.
- Gemini/OpenAI API là tùy chọn; mock mode là phương án dự phòng để demo không phụ thuộc quota.
- `python-docx` để xuất DOCX theo thể thức cơ bản.
- `pypdf` và `python-docx` để đọc tài liệu upload.
- SQLite chuẩn thư viện Python để lưu metadata/chunk cục bộ trước khi nâng cấp lên PostgreSQL hoặc vector database.

## 6. Kiến trúc đề xuất

Luồng xử lý:

1. User Query.
2. Request Extractor nhận diện loại văn bản và bóc tách trường thông tin.
3. Preprocessing/Normalize.
4. Retriever tìm top-k nguồn liên quan theo query đã làm giàu.
5. Generator nhận query + slot + context + loại văn bản.
6. Quality checker đánh giá thể thức, citation, rủi ro thiếu nguồn.
7. UI hiển thị bản nháp, nguồn, phân tích yêu cầu, checklist và nút tải file.

## 7. Hiệu quả kỳ vọng

- Giảm thời gian tra cứu mẫu và tạo bản nháp ban đầu.
- Tăng khả năng kiểm chứng do luôn kèm nguồn.
- Giảm rủi ro pháp lý nhờ cảnh báo thiếu nguồn và yêu cầu người dùng rà soát.
- Phù hợp năng lực nhóm và thời gian học kỳ vì không train model mới.

## 8. Quản trị rủi ro

| Mã | Rủi ro | Mức độ | Biện pháp |
| --- | --- | --- | --- |
| R01 | AI ảo giác, tự thêm căn cứ | Cao | Bắt buộc dùng context truy xuất, citation, quality check |
| R02 | Dữ liệu sai/hết hiệu lực | Cao | Chỉ dùng nguồn công khai, người dùng kiểm duyệt cuối |
| R03 | API lỗi/hết quota | Trung bình | Mock fallback, provider layer |
| R04 | Phình phạm vi | Trung bình | Giới hạn POC vào 4 loại văn bản |
| R05 | Lộ dữ liệu upload | Cao | Lưu local ignored, không commit `.env`/upload riêng |

## 9. Tiêu chí thành công

- Demo chạy ổn định trong 3-5 phút.
- Retrieval/generation/quality test đạt 100% trên bộ test mẫu.
- Bản nháp có nguồn tham khảo và citation.
- Ca thiếu nguồn được đánh dấu rủi ro cao.
- Có thể xuất DOCX để kiểm tra thể thức.

## 10. Kết luận

Dự án khả thi về kỹ thuật và chi phí trong phạm vi POC. Giải pháp RAG giúp cân bằng giữa khả năng sinh nội dung và yêu cầu kiểm chứng của văn bản hành chính. Sản phẩm nên được trình bày như công cụ hỗ trợ soạn thảo, không thay thế trách nhiệm chuyên môn của cán bộ hành chính.
