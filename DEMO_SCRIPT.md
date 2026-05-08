# Kịch bản demo Sprint 7

Thời lượng mục tiêu: 3-5 phút.

## 1. Chuẩn bị

Chạy app:

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

Mở `http://localhost:8501`.

## 2. Luồng demo chính

1. Mở tab `Kho tri thức`.
2. Bấm `Nạp 5 tài liệu mẫu Sprint 2/3/4`.
3. Chỉ ra các cột `source_kind`, `doc_type`, `source`, `preview` trong bảng chunk.
4. Ở sidebar chọn:
   - `Loại văn bản`: `Công văn`
   - `Nguồn dùng khi soạn`: `Tất cả nguồn`
5. Mở tab `Soạn thảo`, nhập:

```text
soạn công văn đề nghị cung cấp số liệu chuyển đổi số
```

6. Bấm `Tạo bản nháp`.
7. Trình bày 4 điểm:
   - Có nguồn truy xuất và điểm BM25.
   - Bản nháp có citation `[S1]`.
   - Có checklist chất lượng và mức rủi ro.
   - Có thể tải `TXT` và `DOCX` chuẩn thể thức.

## 3. Demo upload riêng

1. Mở tab `Kho tri thức`.
2. Upload file `.txt`, `.md` hoặc `.json` dùng cho demo.
3. Chỉ ra cảnh báo bảo mật và nhãn `Upload riêng`.
4. Ở sidebar đổi `Nguồn dùng khi soạn` thành `Chỉ tài liệu upload`.
5. Thử truy xuất hoặc soạn thảo lại để chứng minh app chỉ dùng tài liệu upload.
6. Bấm `Xóa upload riêng` để xóa dữ liệu upload khỏi phiên làm việc.

## 4. Câu kết demo

Hệ thống đã có đủ luồng RAG demo: nạp tri thức, truy xuất, sinh bản nháp có nguồn, kiểm tra chất lượng, lọc nguồn người dùng và xuất bản nháp ra file.
