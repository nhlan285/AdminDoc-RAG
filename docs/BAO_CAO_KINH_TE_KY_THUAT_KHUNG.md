# Khung báo cáo kinh tế kỹ thuật

Tên dự án: **Xây dựng AI hỗ trợ soạn thảo văn bản hành chính sử dụng mô hình RAG**
Loại dự án: Proof of Concept phục vụ học phần Quản lý dự án
Phiên bản tài liệu: đồng bộ với nhánh schema lab `schema-lab-doc-crawler-20260530`

## 1. Thông tin chung

- Chủ đầu tư/đơn vị giả định: nhóm sinh viên thực hiện đồ án.
- Người dùng giả định: cán bộ/nhân viên hành chính cần hỗ trợ tạo bản nháp văn bản.
- Phạm vi triển khai: ứng dụng web local bằng Streamlit.
- Sản phẩm đầu ra: prototype có thể demo, tài liệu kỹ thuật, kịch bản demo và khung báo cáo.

## 2. Sự cần thiết đầu tư

Việc soạn thảo văn bản hành chính thường tốn thời gian ở các bước tra cứu mẫu, xác định thể thức, tổng hợp thông tin và rà soát nguồn. Nếu dùng chatbot tạo sinh trực tiếp, hệ thống có thể sinh nội dung không có căn cứ hoặc sai thể thức.

Giải pháp RAG giúp giảm rủi ro bằng cách truy xuất tài liệu/mẫu liên quan trước khi sinh bản nháp. Với nhánh schema lab, hệ thống còn bổ sung catalog loại văn bản để kiểm soát cấu trúc từng loại văn bản, giúp mở rộng từ vài loại văn bản lên nhiều loại văn bản khác nhau.

## 3. Mục tiêu đầu tư

- Xây dựng demo AI hỗ trợ soạn thảo văn bản hành chính.
- Nhận yêu cầu tiếng Việt tự nhiên và tự động nhận diện loại văn bản.
- Trích xuất thông tin quan trọng như chủ thể, số ngày, lý do, nơi nhận, thời gian.
- Truy xuất nguồn liên quan từ kho tri thức.
- Sinh bản nháp có citation và nguồn tham khảo.
- Kiểm tra chất lượng bản nháp trước khi người dùng tải về.
- Xuất file DOCX theo định dạng hành chính cơ bản.
- Thể hiện quy trình quản lý dự án theo Scrum/Sprint.

## 4. Phạm vi kỹ thuật

Thành phần chính:

- Giao diện Streamlit trong `app.py`.
- Kho tri thức JSON, template text, dữ liệu crawl và upload riêng.
- Tiền xử lý/chunking tài liệu trong `src/preprocessing.py`.
- Data model trong `src/documents.py`.
- Phân tích yêu cầu trong `src/extractor.py`.
- Catalog loại văn bản trong `src/doc_type_catalog.py` và `data/doc_types/*.json`.
- Retriever BM25 trong `src/retriever.py`.
- Generator template/rule-based trong `src/generator.py`.
- Provider LLM trong `src/llm.py`.
- Quality checker trong `src/quality.py`.
- Export DOCX trong `src/docx_exporter.py`.
- SQLite local trong `src/storage.py`.
- Crawler nguồn công khai trong `scripts/crawl_public_sources.py`.

Phạm vi văn bản demo:

- Công văn.
- Thông báo.
- Tờ trình.
- Quyết định hành chính đơn giản.
- Giấy nghỉ phép.

## 5. Phương án công nghệ

| Nhóm | Công nghệ | Lý do chọn |
| --- | --- | --- |
| Ngôn ngữ | Python | Phù hợp xử lý dữ liệu, AI và demo nhanh |
| Giao diện | Streamlit | Dễ dựng prototype, chạy local ổn định |
| Truy xuất | BM25 cục bộ | Dễ giải thích, không cần hạ tầng vector database |
| Xử lý tài liệu | pypdf, python-docx | Đọc PDF/DOCX và xuất DOCX |
| Crawl | requests, BeautifulSoup | Tải và parse nguồn công khai |
| LLM | Mock, Gemini, OpenAI | Có fallback demo và tùy chọn API thật |
| Lưu trữ | JSON, SQLite local | Đơn giản, phù hợp POC, dễ chuyển lên DB thật |
| Quản lý mã nguồn | Git/GitHub | Theo dõi sprint, branch, commit |

## 6. Kiến trúc xử lý

```text
User Request
  -> Streamlit UI
  -> Request Extractor
  -> Document Type Catalog
  -> Knowledge Base / Chunks
  -> BM25 Retriever
  -> Template/LLM Generator
  -> Quality Checker
  -> TXT/DOCX Export
```

Luồng chi tiết:

1. Người dùng nhập yêu cầu.
2. Hệ thống phân tích loại văn bản, ý định và slot thông tin.
3. Catalog xác định trường bắt buộc và template tương ứng.
4. Retriever tìm top-k chunk liên quan.
5. Generator sinh bản nháp dựa trên slot, template và nguồn.
6. Quality checker đánh giá thể thức, citation và rủi ro.
7. Người dùng chỉnh sửa và tải file.

## 7. Hiệu quả kỳ vọng

Hiệu quả nghiệp vụ:

- Giảm thời gian tạo bản nháp ban đầu.
- Hỗ trợ người dùng ít kinh nghiệm nhớ đúng cấu trúc văn bản.
- Tăng khả năng kiểm chứng nhờ nguồn/citation.
- Giảm lỗi bỏ sót thông tin bắt buộc.

Hiệu quả kỹ thuật:

- Có prototype chạy được trong phạm vi học kỳ.
- Có thiết kế module rõ ràng.
- Có khả năng mở rộng loại văn bản bằng JSON.
- Không cần train mô hình mới.
- Không phụ thuộc tuyệt đối vào API LLM nhờ mock mode.

Hiệu quả quản lý dự án:

- Có sprint plan, demo script và tiêu chí nghiệm thu.
- Có backlog và rủi ro được ghi nhận.
- Có tài liệu phục vụ thuyết trình và vấn đáp.

## 8. Quản trị rủi ro

| Mã | Rủi ro | Mức độ | Biện pháp kiểm soát |
| --- | --- | --- | --- |
| R01 | AI sinh nội dung không có căn cứ | Cao | RAG, citation, cảnh báo thiếu nguồn, human-in-the-loop |
| R02 | Sai thể thức văn bản | Cao | Template theo catalog, checklist section bắt buộc |
| R03 | Người dùng nhập thiếu thông tin | Trung bình | Bóc tách slot, hiển thị `missing_fields`, dùng placeholder |
| R04 | Dữ liệu crawl thiếu hoặc rác | Trung bình | Manifest nguồn, kiểm tra thủ công sau crawl |
| R05 | PDF scan/file DOC cũ không trích xuất tốt | Trung bình | Đánh dấu nguồn partial, hướng phát triển OCR |
| R06 | API LLM lỗi/hết quota | Trung bình | Mock mode, fallback provider |
| R07 | Lộ dữ liệu nhạy cảm | Cao | `.env`/upload local ignored, không commit dữ liệu riêng |
| R08 | Phình phạm vi | Trung bình | Chốt POC, ưu tiên luồng demo cốt lõi |

## 9. Tiêu chí thành công

- App chạy được local bằng Streamlit.
- Demo hoàn chỉnh trong 3-5 phút.
- Hệ thống truy xuất được nguồn liên quan.
- Bản nháp có citation và nguồn tham khảo.
- Hệ thống tự nhận diện được ít nhất một ca cụ thể như giấy nghỉ phép.
- Có checklist chất lượng và mức rủi ro.
- Có thể xuất DOCX.
- Tài liệu Scrum/Sprint, demo script và báo cáo được đồng bộ.

## 10. Phạm vi chưa triển khai trong POC

- Chưa triển khai phân quyền người dùng.
- Chưa có cơ chế phê duyệt/ban hành văn bản.
- Chưa ký số hoặc liên thông hệ thống hành chính thật.
- Chưa dùng vector database thật.
- Chưa có OCR hoàn chỉnh cho PDF scan.
- Chưa có quy trình pháp lý để xác nhận hiệu lực nguồn ở mức sản xuất.

## 11. Hướng phát triển

- Thêm bước hỏi lại thông tin thiếu trước khi sinh bản nháp.
- Bổ sung nhiều loại văn bản hơn bằng catalog JSON.
- Dùng vector database và embedding cho truy xuất ngữ nghĩa.
- Thêm OCR và pipeline kiểm duyệt dữ liệu crawl.
- Lưu lịch sử phiên soạn thảo.
- Thêm phân quyền, nhật ký thao tác và bảo mật dữ liệu.
- Đóng gói Docker hoặc triển khai server nội bộ.

## 12. Kết luận

Dự án khả thi về mặt kỹ thuật và phù hợp phạm vi học phần. Hệ thống đã chứng minh được luồng RAG từ nhập yêu cầu, truy xuất nguồn, sinh bản nháp, kiểm tra chất lượng đến xuất file. Thiết kế schema/catalog giúp sản phẩm có hướng mở rộng rõ ràng, còn Scrum/Sprint giúp quá trình phát triển có kiểm soát và có đầu ra sau từng giai đoạn.
