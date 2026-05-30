# Kế hoạch chỉnh sửa demo AdminDoc-RAG

## Mục tiêu demo

Tên đề tài: "Xây dựng AI hỗ trợ soạn thảo văn bản hành chính sử dụng mô hình RAG".

Demo cần chứng minh được luồng cốt lõi:

1. Người dùng nhập yêu cầu soạn thảo.
2. Hệ thống truy xuất văn bản/mẫu liên quan trong kho tri thức.
3. Hệ thống sinh bản nháp có marker nguồn `[S1]`, `[S2]`, `[S3]`.
4. Hệ thống hiển thị checklist chất lượng, rủi ro và cảnh báo human-in-the-loop.
5. Người dùng tải bản nháp dạng TXT/DOCX.

Ý tưởng sản phẩm có thể diễn giải giống NotebookLM ở điểm: người dùng làm việc với kho tài liệu đã nạp, hệ thống trả lời/sinh nội dung kèm nguồn để kiểm chứng, nhưng phạm vi được giới hạn cho văn bản hành chính.

## Phạm vi chốt cho POC

In-scope:

- 4 loại văn bản chính: Công văn, Thông báo, Tờ trình, Quyết định hành chính đơn giản.
- Kho tri thức cục bộ bằng JSON/chunk text.
- Retriever BM25 nội bộ, hỗ trợ tiếng Việt có dấu và không dấu.
- Generator mock ổn định và tùy chọn gọi Gemini/OpenAI khi có API key.
- Upload tài liệu `.txt`, `.md`, `.json`, `.pdf`, `.docx`.
- Xuất TXT/DOCX và checklist chất lượng.
- Test demo ngay trên UI cho Retrieval, Generation và Quality.

Out-of-scope:

- Không tự động ký số, phê duyệt, ban hành văn bản.
- Không xử lý văn bản mật/dữ liệu nội bộ cơ quan.
- Không tư vấn pháp lý hoặc tự khẳng định hiệu lực văn bản pháp luật.
- Không liên thông hệ thống cấp quốc gia.
- Không huấn luyện mô hình AI mới.

## Việc đã sửa trong đợt này

- Bổ sung dependency còn thiếu vào `requirements.txt`.
- Tách dữ liệu upload riêng sang `data/user_docs.local.json` và ignore khỏi git.
- Nạp thêm các template trong `data/templates/` vào kho tri thức hệ thống.
- Thêm module `src/extractor.py` để phân tích yêu cầu và bóc tách slot.
- Thêm module `src/storage.py` để đồng bộ kho tri thức sang SQLite local.
- Chuẩn hóa generator cho 4 loại văn bản demo.
- Bổ sung sinh nháp theo slot cho `Giấy nghỉ phép`, ví dụ tên người nghỉ, số ngày nghỉ và lý do.
- Bổ sung mục `Nguồn tham khảo`, citation và ghi chú rà soát vào bản nháp.
- Sửa rule quality cho `Quyết định hành chính đơn giản`.
- Thêm panel chạy test Sprint 3/4/6 trong tab `Kho tri thức`.
- Thêm test `Phân tích yêu cầu`.
- Sửa reset kho tri thức để thực sự nạp lại dữ liệu nền.
- Cải thiện fallback LLM: nếu Gemini/OpenAI lỗi hoặc trả rỗng thì quay về mock an toàn.
- Nâng cấp `crawler.py` để đọc manifest, tìm nhiều loại file đính kèm và xuất JSON xử lý sau crawl.

## Tiêu chí nghiệm thu trước demo

- `python -m compileall -q app.py src crawler.py data_auditor.py scripts/template_converter.py` không lỗi.
- Bộ test nội bộ đạt:
  - Extraction: 3/3.
  - Retrieval: 5/5.
  - Generation: 5/5.
  - Quality: 5/5.
- Chạy Streamlit được bằng `python -m streamlit run app.py`.
- Demo 3-5 phút chạy được với ít nhất 3 kịch bản:
  - Công văn đề nghị cung cấp số liệu chuyển đổi số.
  - Thông báo tổ chức tập huấn an toàn thông tin.
  - Tờ trình phê duyệt kế hoạch triển khai phần mềm nội bộ.
  - Giấy nghỉ phép: `Xuân Tịnh xin nghỉ 4 ngày vì ốm`.
  - Một ca thiếu nguồn để chứng minh cảnh báo rủi ro cao.

## Backlog ưu tiên tiếp theo

1. Chuẩn hóa README theo trạng thái code mới.
2. Tạo video/script demo ngắn kèm ảnh chụp màn hình.
3. Mở rộng bộ dữ liệu mẫu công khai, nhưng vẫn giữ test nhỏ để demo ổn định.
4. Bổ sung trang/tài liệu giải thích kiến trúc RAG cho báo cáo.
5. Hoàn thiện báo cáo kinh tế kỹ thuật và báo cáo dự toán dựa trên hai khung trong thư mục `docs/`.
