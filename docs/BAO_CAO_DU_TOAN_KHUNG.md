# Khung báo cáo dự toán

Tên dự án: **Xây dựng AI hỗ trợ soạn thảo văn bản hành chính sử dụng mô hình RAG**
Phạm vi: Proof of Concept phục vụ học phần Quản lý dự án
Phiên bản dự toán: đồng bộ với nhánh schema lab `schema-lab-doc-crawler-20260530`

## 1. Cơ sở lập dự toán

- Phạm vi dự án là prototype chạy local, không triển khai production.
- Quy trình phát triển theo Scrum/Sprint, mỗi sprint có đầu ra demo được.
- Hạ tầng chính sử dụng máy cá nhân, VS Code, GitHub, Streamlit local.
- Kho tri thức dùng JSON, SQLite local, tài liệu mẫu và dữ liệu công khai.
- API LLM là tùy chọn; mock mode bảo đảm demo không phụ thuộc chi phí API.
- Chưa tính chi phí server, GPU, cloud database, domain hoặc vận hành dài hạn.

## 2. Giả định đơn giá

Chi phí nhân sự là chi phí quy đổi phục vụ báo cáo học thuật, không nhất thiết là dòng tiền thực chi.

| Hạng mục | Đơn giá tham khảo |
| --- | ---: |
| Ngày công sinh viên quy đổi | 250.000 VND/man-day |
| API LLM dự phòng demo | 300.000 VND/gói |
| In ấn/tài liệu/slide | 250.000 VND/gói |
| Internet/điện/công cụ hỗ trợ | 300.000 VND/gói |
| Dự phòng xử lý dữ liệu/OCR thủ công | 200.000 VND/gói |
| Dự phòng rủi ro | 10% |

## 3. Dự toán nỗ lực theo giai đoạn

| Mã | Giai đoạn | Nội dung | Effort | Chi phí quy đổi |
| --- | --- | --- | ---: | ---: |
| P1 | Khởi tạo và lập kế hoạch | Xác định yêu cầu, backlog, sprint plan, phạm vi POC | 10 man-days | 2.500.000 VND |
| P2 | Dữ liệu và kho tri thức | Dữ liệu mẫu, upload, preprocessing, chunking, crawler công khai | 14 man-days | 3.500.000 VND |
| P3 | Lõi RAG và AI | BM25 retriever, extractor, catalog loại văn bản, generator, LLM provider | 18 man-days | 4.500.000 VND |
| P4 | Giao diện và đầu ra | Streamlit UI, notebook layout, quality checker, export TXT/DOCX | 12 man-days | 3.000.000 VND |
| P5 | Kiểm thử, demo, báo cáo | Test case, demo script, báo cáo kinh tế kỹ thuật, dự toán, thuyết trình | 10 man-days | 2.500.000 VND |
|  | Tổng nhân sự quy đổi |  | 64 man-days | 16.000.000 VND |

## 4. Dự toán chi phí tiền mặt

| Hạng mục | Số lượng | Thành tiền |
| --- | ---: | ---: |
| API LLM dự phòng | 1 | 300.000 VND |
| Công cụ phát triển mã nguồn | 1 | 0 VND |
| Streamlit local | 1 | 0 VND |
| CSDL local SQLite | 1 | 0 VND |
| Công cụ crawl/tiền xử lý nguồn công khai | 1 | 0 VND |
| In ấn/tài liệu/slide | 1 | 250.000 VND |
| Internet/điện/công cụ hỗ trợ | 1 | 300.000 VND |
| Dự phòng xử lý dữ liệu/OCR thủ công | 1 | 200.000 VND |
| Tạm tính |  | 1.050.000 VND |
| Dự phòng 10% |  | 105.000 VND |
| Tổng tiền mặt dự kiến |  | 1.155.000 VND |

## 5. Tổng mức dự toán trình bày

- Chi phí quy đổi nhân sự: 16.000.000 VND.
- Chi phí tiền mặt dự kiến: 1.155.000 VND.
- Tổng giá trị kinh tế quy đổi: 17.155.000 VND.

## 6. Phân bổ theo sprint

| Sprint | Nội dung chính | Effort ước tính |
| --- | --- | ---: |
| Sprint 1 | Nền demo RAG mô phỏng | 6 man-days |
| Sprint 2 | Kho tri thức và tiền xử lý | 8 man-days |
| Sprint 3 | BM25 retriever và test retrieval | 8 man-days |
| Sprint 4 | Generator theo loại văn bản | 8 man-days |
| Sprint 5 | Provider LLM và fallback | 7 man-days |
| Sprint 6 | Quality check và export DOCX | 8 man-days |
| Sprint 7 | UI demo, upload riêng, demo script | 8 man-days |
| Sprint 8 | Schema lab, crawler, báo cáo/thuyết trình | 11 man-days |
| Tổng |  | 64 man-days |

## 7. Phương án tiết kiệm chi phí

- Dùng mock mode khi demo nếu API lỗi, hết quota hoặc không có mạng.
- Không thuê GPU/server trong phạm vi POC.
- Dùng BM25 local thay vì vector database cloud ở giai đoạn đầu.
- Chỉ dùng dữ liệu công khai và tài liệu mẫu nội bộ phục vụ học thuật.
- Tận dụng GitHub, VS Code, Python và Streamlit miễn phí.
- Chỉ bật LLM thật khi cần so sánh chất lượng hoặc demo nâng cao.

## 8. Kiểm soát dự toán

- Product Owner xác nhận phạm vi trước mỗi sprint.
- Scrum Master theo dõi effort và rủi ro phát sinh.
- Development Team chỉ bổ sung chức năng nếu không làm ảnh hưởng demo chính.
- Mọi chi phí API/in ấn phải được nhóm xác nhận trước.
- Nếu vượt dự toán, ưu tiên giữ luồng RAG cốt lõi và cắt giảm phần mở rộng như OCR/vector database.

## 9. Rủi ro ảnh hưởng chi phí

| Rủi ro | Tác động chi phí | Biện pháp |
| --- | --- | --- |
| API LLM hết quota | Tăng chi phí API | Dùng mock mode/fallback |
| Dữ liệu crawl trích xuất kém | Tăng thời gian làm sạch | Giới hạn nguồn, kiểm tra thủ công |
| Giao diện thay đổi nhiều | Tăng effort frontend | Chốt layout notebook tối giản |
| Mở rộng quá nhiều loại văn bản | Tăng effort kiểm thử | Dùng catalog JSON, ưu tiên loại demo |
| Cần OCR/vector database | Tăng chi phí công cụ | Đưa vào hướng phát triển sau POC |

## 10. Kết luận

Dự toán phù hợp với một POC học thuật. Chi phí tiền mặt thấp nhờ tận dụng công cụ miễn phí và hạ tầng cá nhân; phần lớn giá trị nằm ở công sức phân tích nghiệp vụ, xây dựng RAG, kiểm thử, demo và hoàn thiện tài liệu quản lý dự án.
