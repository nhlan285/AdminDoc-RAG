# AI hỗ trợ soạn thảo văn bản hành chính bằng RAG

Demo ban đầu cho đề tài: xây dựng hệ thống AI hỗ trợ soạn thảo văn bản hành chính ứng dụng mô hình RAG.

## Mục tiêu bản đầu

- Nhận yêu cầu soạn thảo từ người dùng.
- Truy xuất tài liệu/mẫu văn bản liên quan từ kho tri thức cục bộ.
- Sinh bản nháp văn bản hành chính kèm nguồn tham khảo.
- Giữ nguyên nguyên tắc human-in-the-loop: người dùng phải rà soát trước khi sử dụng.

## Cấu trúc

```text
ai_soan_thao_rag/
├── app.py
├── data/
│   └── admin_docs.json
├── src/
│   ├── documents.py
│   ├── generator.py
│   └── retriever.py
├── .env.example
├── .gitignore
└── requirements.txt
```

## Chạy demo

```bash
pip install -r requirements.txt
streamlit run app.py
```

Nếu đang dùng môi trường ảo đã tạo trong thư mục dự án:

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

## Demo Sprint 2

1. Mở tab `Kho tri thức`.
2. Bấm `Nạp 5 tài liệu mẫu Sprint 2`.
3. Kiểm tra bảng chunk xuất hiện thêm dữ liệu từ `data/sprint2_sample_docs.json`.
4. Ở phần `Kiểm tra truy xuất`, dùng câu:

```text
soạn công văn đề nghị cung cấp số liệu chuyển đổi số
```

Kết quả kỳ vọng: tài liệu `CV-MAU-002` xuất hiện trong nhóm kết quả đầu.

Ngoài bộ mẫu có sẵn, có thể upload file `.txt`, `.md` hoặc `.json`. Với `.json`, app hỗ trợ dạng danh sách tài liệu hoặc object có khóa `documents`.

## Demo Sprint 3

1. Mở tab `Kho tri thức`.
2. Bấm `Nạp 5 tài liệu mẫu Sprint 2/3/4`.
3. Bấm `Chạy test truy xuất Sprint 3`.
4. Kết quả kỳ vọng: đạt `5/5` test, các tài liệu `CV-MAU-002`, `TB-MAU-002`, `TT-MAU-002`, `QD-MAU-002`, `CV-MAU-003` đều xuất hiện đúng trong top 3.

Có thể thử truy vấn không dấu:

```text
cong van moi tham du hoi nghi so ket
```

Kết quả kỳ vọng: `CV-MAU-003` xuất hiện ở nhóm kết quả đầu.

Có thể thử truy vấn ngoài phạm vi:

```text
ky so tu dong lien thong quoc gia
```

Kết quả kỳ vọng: app cảnh báo chưa có nguồn đủ phù hợp thay vì tự lấy nguồn yếu.

## Demo Sprint 4

1. Mở tab `Kho tri thức`.
2. Bấm `Nạp 5 tài liệu mẫu Sprint 2/3/4`.
3. Bấm `Chạy test generator Sprint 4`.
4. Kết quả kỳ vọng: đạt `5/5` test generator.

Sau đó mở tab `Soạn thảo`, lần lượt chọn các loại văn bản và nhập các câu sau:

```text
soạn công văn đề nghị cung cấp số liệu chuyển đổi số
thông báo tổ chức tập huấn an toàn thông tin
tờ trình phê duyệt kế hoạch triển khai phần mềm nội bộ
quyết định thành lập tổ triển khai dự án công nghệ thông tin
```

Kết quả kỳ vọng: mỗi loại văn bản có bố cục riêng, có marker nguồn như `[S1]`, và có danh sách `Nguồn tham khảo`.

Ca không có nguồn:

```text
soạn công văn về ký số tự động liên thông quốc gia
```

Kết quả kỳ vọng: app sinh cảnh báo `CHƯA ĐỦ NGUỒN KIỂM CHỨNG` thay vì tạo bản nháp hoàn chỉnh.

## Demo Sprint 5

Mock mode vẫn là mặc định, nên app chạy được ngay cả khi chưa có API key.

Khuyến nghị cho demo free là Gemini Flash-Lite. Tạo file `.env` trong thư mục dự án:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_new_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_MAX_OUTPUT_TOKENS=1800
```

Sau đó chạy lại app:

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

Nếu muốn dùng OpenAI thay Gemini, cấu hình:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.5
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_OUTPUT_TOKENS=1800
```

Kịch bản demo:

1. Chưa tạo `.env`: sidebar hiển thị `Mock mode`, app vẫn sinh bản nháp.
2. Tạo `.env` với `LLM_PROVIDER=gemini` nhưng để trống `GEMINI_API_KEY`: app fallback sang mock và hiện cảnh báo thiếu key.
3. Tạo `.env` có Gemini API key hợp lệ: app gọi Gemini để sinh bản nháp.
4. Nhập truy vấn không có nguồn phù hợp: app không gọi LLM và trả cảnh báo chưa đủ nguồn kiểm chứng.

## Demo Sprint 6

1. Mở tab `Kho tri thức`.
2. Bấm `Nạp 5 tài liệu mẫu Sprint 2/3/4`.
3. Bấm `Chạy test chất lượng Sprint 6`.
4. Kết quả kỳ vọng: đạt `5/5` test chất lượng.

Sau đó mở tab `Soạn thảo`, nhập:

```text
soạn công văn đề nghị cung cấp số liệu chuyển đổi số
```

Kết quả kỳ vọng: app hiển thị `Checklist chất lượng`, điểm chất lượng và mức rủi ro thấp/trung bình.
Ở sidebar, nhập `Cơ quan chủ quản`, `Cơ quan ban hành`, `Địa danh`, rồi bấm `Tải bản nháp DOCX chuẩn thể thức`.

File DOCX xuất ra có khổ A4, font Times New Roman, lề trái 30 mm, lề phải 15 mm, lề trên/dưới 20 mm, cỡ chữ nội dung 13, giãn dòng 1.15, giãn đoạn sau 6 pt, quốc hiệu/tiêu ngữ căn giữa, số trang căn giữa ở lề trên và ẩn ở trang đầu.

Ca thiếu nguồn:

```text
soạn công văn về ký số tự động liên thông quốc gia
```

Kết quả kỳ vọng: app đánh dấu rủi ro `Cao` và cảnh báo cần bổ sung nguồn.

## Demo Sprint 7

Mục tiêu demo trong 3-5 phút: cho thấy app đã có luồng hoàn chỉnh từ nạp dữ liệu, lọc nguồn, sinh nháp, kiểm tra chất lượng đến tải file.

1. Mở tab `Kho tri thức`, bấm `Nạp 5 tài liệu mẫu Sprint 2/3/4`.
2. Trong sidebar, chọn `Nguồn dùng khi soạn` là `Tất cả nguồn`.
3. Mở tab `Soạn thảo`, chọn `Công văn`, nhập:

```text
soạn công văn đề nghị cung cấp số liệu chuyển đổi số
```

4. Bấm `Tạo bản nháp`, kiểm tra `Nguồn truy xuất`, `Checklist chất lượng`, sau đó tải thử cả `TXT` và `DOCX`.
5. Quay lại tab `Kho tri thức`, upload một file `.txt/.md/.json` riêng. File upload sẽ được gắn nhãn `Upload riêng`.
6. Trong sidebar, đổi `Nguồn dùng khi soạn` thành `Chỉ tài liệu upload` để chứng minh app có thể lọc nguồn.
7. Bấm `Xóa upload riêng` để xóa tài liệu người dùng khỏi phiên làm việc.

Kịch bản demo nhanh nằm ở `DEMO_SCRIPT.md`; bộ câu lệnh mẫu nằm ở `data/demo_queries.json`.

## Ghi chú phạm vi

Bản này mặc định chạy ở mock mode để demo ổn định, đồng thời có thể gọi OpenAI API khi cấu hình `.env`. Dữ liệu mẫu trong `data/` dùng cho trình diễn kỹ thuật, cần thay bằng văn bản công khai đã kiểm chứng khi làm bản nộp cuối.
