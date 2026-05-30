# Khung báo cáo dự toán

## 1. Cơ sở lập dự toán

- Phạm vi dự án POC trong học phần Quản lý dự án CNTT.
- Kế hoạch Step Wise trong tài liệu yêu cầu.
- Tổng nỗ lực ước lượng: 52 man-days.
- Hạ tầng chính dùng máy cá nhân, VS Code, GitHub và Streamlit local.
- API LLM là tùy chọn; mock mode bảo đảm demo không phụ thuộc chi phí phát sinh.

## 2. Giả định đơn giá

Bảng dưới dùng cho báo cáo học thuật. Chi phí nhân sự là chi phí quy đổi nội bộ, không nhất thiết là dòng tiền thực chi.

| Hạng mục | Đơn giá tham khảo |
| --- | ---: |
| Ngày công sinh viên quy đổi | 250.000 VND/man-day |
| API LLM dự phòng demo | 300.000 VND/gói |
| In ấn/tài liệu/slide | 200.000 VND/gói |
| Internet/điện/nền tảng hỗ trợ | 300.000 VND/gói |
| Dự phòng rủi ro | 10% |

## 3. Dự toán nỗ lực theo giai đoạn

| Mã | Giai đoạn | Effort | Chi phí quy đổi |
| --- | --- | ---: | ---: |
| P1 | Khởi tạo và lập kế hoạch | 12 man-days | 3.000.000 VND |
| P2 | Phát triển kỹ thuật RAG | 22 man-days | 5.500.000 VND |
| P3 | Tích hợp và giao diện | 10 man-days | 2.500.000 VND |
| P4 | UAT và đóng gói | 8 man-days | 2.000.000 VND |
|  | Tổng nhân sự quy đổi | 52 man-days | 13.000.000 VND |

## 4. Dự toán chi phí tiền mặt

| Hạng mục | Số lượng | Thành tiền |
| --- | ---: | ---: |
| API LLM dự phòng | 1 | 300.000 VND |
| CSDL local SQLite | 1 | 0 VND |
| Công cụ crawl/tiền xử lý nguồn công khai | 1 | 0 VND |
| In ấn/tài liệu/slide | 1 | 200.000 VND |
| Internet/điện/nền tảng hỗ trợ | 1 | 300.000 VND |
| Tạm tính |  | 800.000 VND |
| Dự phòng 10% |  | 80.000 VND |
| Tổng tiền mặt dự kiến |  | 880.000 VND |

## 5. Tổng mức dự toán trình bày

- Chi phí quy đổi nhân sự: 13.000.000 VND.
- Chi phí tiền mặt dự kiến: 880.000 VND.
- Tổng giá trị kinh tế quy đổi: 13.880.000 VND.

## 6. Phương án tiết kiệm chi phí

- Dùng mock mode khi demo nếu API lỗi/hết quota.
- Chỉ dùng dữ liệu công khai miễn phí.
- Không thuê GPU/server.
- Không triển khai vector database cloud trong POC nếu BM25 cục bộ đáp ứng demo.
- Tận dụng máy cá nhân và công cụ miễn phí của nhóm.

## 7. Kiểm soát dự toán

- Schedule & Cost Lead theo dõi effort theo tuần.
- Mọi chi phí API/in ấn phải được nhóm xác nhận trước.
- Nếu vượt dự toán, ưu tiên cắt giảm API cloud, giữ mock mode và dữ liệu local.

## 8. Kết luận

Dự toán phù hợp cho một POC học thuật. Chi phí tiền mặt thấp nhờ dùng hạ tầng sẵn có và dữ liệu công khai; phần lớn giá trị nằm ở nỗ lực phân tích, xây dựng demo, kiểm thử và hoàn thiện báo cáo.
