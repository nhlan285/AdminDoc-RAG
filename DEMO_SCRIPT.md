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
2. Bấm `Nạp tài liệu mẫu`.
3. Chỉ ra các cột `Nhóm nguồn`, `Loại`, `Nguồn`, `Nội dung` trong bảng chunk.
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

## 2.1. Luồng phân tích yêu cầu cụ thể

1. Giữ bật `Tự động nhận diện yêu cầu` ở sidebar.
2. Nhập:

```text
Xuân Tịnh xin nghỉ 4 ngày vì ốm
```

3. Bấm `Tạo bản nháp`.
4. Trình bày:
   - Hệ thống nhận diện `Giấy nghỉ phép`.
   - Bảng `Phân tích yêu cầu` bóc tách `subject_name`, `leave_days`, `reason`.
   - Bản nháp điền tên `Xuân Tịnh`, thời gian nghỉ `4 ngày`, lý do `ốm`.
   - Trường thiếu như ngày bắt đầu/kết thúc vẫn để placeholder để người dùng bổ sung.

## 3. Demo upload riêng

1. Mở tab `Kho tri thức`.
2. Upload file `.txt`, `.md` hoặc `.json` dùng cho demo.
3. Chỉ ra cảnh báo bảo mật và nhãn `Upload riêng`.
4. Ở sidebar đổi `Nguồn dùng khi soạn` thành `Chỉ tài liệu upload`.
5. Thử truy xuất hoặc soạn thảo lại để chứng minh app chỉ dùng tài liệu upload.
6. Bấm `Xóa upload riêng` để xóa dữ liệu upload khỏi phiên làm việc.

## 4. Câu kết demo

Hệ thống đã có đủ luồng RAG demo: nạp tri thức, truy xuất, sinh bản nháp có nguồn, kiểm tra chất lượng, lọc nguồn người dùng và xuất bản nháp ra file.
