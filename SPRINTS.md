# Kế hoạch sprint demo cho hệ thống AI soạn thảo văn bản hành chính RAG

Nguyên tắc làm việc:

- Mỗi sprint phải kết thúc bằng một thành phẩm chạy được để demo.
- Không chuyển sang sprint tiếp theo cho đến khi người dùng xác nhận demo sprint hiện tại đã đạt.
- Sau mỗi sprint cần có: chức năng demo, dữ liệu kiểm thử, tiêu chí chấp nhận và ghi chú rủi ro còn lại.

## Trạng thái hiện tại

- Sprint hiện tại: Sprint 7
- Trạng thái: Sẵn sàng demo
- Điều kiện mở Sprint 8: Người dùng xác nhận "Sprint 7 demo xong" hoặc nội dung tương đương.

## Sprint 1 - Nền demo RAG mô phỏng

Mục tiêu: Có ứng dụng demo chạy được với luồng cơ bản: nhập yêu cầu, truy xuất tài liệu mẫu, tạo bản nháp và hiển thị nguồn tham khảo.

Thành phẩm demo:

- Giao diện Streamlit chạy local.
- Người dùng chọn loại văn bản: Công văn, Thông báo, Tờ trình, Quyết định hành chính đơn giản.
- Hệ thống truy xuất tài liệu từ `data/admin_docs.json`.
- Hệ thống sinh bản nháp theo thể thức hành chính cơ bản.
- Hiển thị nguồn/citation để người dùng kiểm chứng.

Tiêu chí chấp nhận:

- App chạy bằng `streamlit run app.py`.
- Nhập một yêu cầu hợp lệ thì có bản nháp tiếng Việt.
- Có ít nhất một nguồn tham khảo hiển thị bên cạnh bản nháp.
- Có cảnh báo human-in-the-loop.

## Sprint 2 - Kho tri thức và tiền xử lý dữ liệu

Mục tiêu: Thay dữ liệu mẫu quá nhỏ bằng kho tri thức có cấu trúc hơn, chuẩn bị nền cho RAG thật.

Trạng thái triển khai:

- Đã thêm module làm sạch văn bản, đọc `.txt/.md/.json` và chunking tại `src/preprocessing.py`.
- Đã thêm bộ 5 tài liệu mẫu tại `data/sprint2_sample_docs.json`.
- Đã thêm tab "Kho tri thức" trong app để nạp mẫu, upload file, xem danh sách chunk và kiểm tra truy xuất.
- Đã được người dùng xác nhận để chuyển sang Sprint 3.

Thành phẩm demo:

- Trang/quy trình nạp tài liệu mẫu từ file `.txt`, `.md` hoặc `.json`.
- Module làm sạch văn bản: bỏ khoảng trắng thừa, chuẩn hóa tiêu đề, chia đoạn.
- Module chunking chia văn bản thành đoạn nhỏ có metadata.
- Màn hình hiển thị danh sách tài liệu/chunk đã nạp.

Tiêu chí chấp nhận:

- Có thể thêm ít nhất 5 văn bản mẫu mới vào kho tri thức.
- Mỗi chunk có `id`, `source`, `doc_type`, `title`, `content`.
- Demo được việc thêm dữ liệu rồi retrieve ra tài liệu mới.

## Sprint 3 - Retriever tốt hơn

Mục tiêu: Cải thiện truy xuất để kết quả liên quan hơn, gần với cơ chế RAG thực tế.

Trạng thái triển khai:

- Đã thay retriever đếm từ đơn giản bằng BM25 cục bộ tại `src/retriever.py`.
- Đã chuẩn hóa tìm kiếm không dấu để truy vấn như `cong van moi tham du hoi nghi so ket` vẫn tìm đúng tài liệu tiếng Việt có dấu.
- Đã thêm bộ 5 test case tại `data/retrieval_test_cases.json`.
- Đã thêm màn chạy test truy xuất Sprint 3 trong tab "Kho tri thức".
- Đã được người dùng xác nhận để chuyển sang Sprint 4.

Thành phẩm demo:

- Retriever tách riêng thành interface rõ ràng.
- Có tìm kiếm keyword nâng cấp hoặc TF-IDF/BM25 cục bộ.
- Có bộ câu hỏi test truy xuất.
- Màn hình demo hiển thị điểm liên quan, từ khóa khớp và metadata nguồn.

Tiêu chí chấp nhận:

- Với 5 câu hỏi kiểm thử, hệ thống trả về tài liệu đúng loại văn bản hoặc đúng chủ đề trong top 3.
- Có thể điều chỉnh `top_k`.
- Khi không tìm thấy nguồn đủ tốt, hệ thống cảnh báo thay vì tự bịa.

## Sprint 4 - Generator và prompt theo loại văn bản

Mục tiêu: Sinh bản nháp có cấu trúc rõ theo từng loại văn bản, dựa trên context truy xuất.

Trạng thái triển khai:

- Đã thay generator chung bằng 4 template riêng tại `src/generator.py`.
- Đã gắn citation dạng `[S1]`, `[S2]`, `[S3]` vào nội dung và danh sách nguồn.
- Đã thêm ca không có nguồn: generator trả về cảnh báo "chưa đủ nguồn kiểm chứng" thay vì sinh nội dung hoàn chỉnh.
- Đã thêm bộ 5 test generator tại `data/generation_test_cases.json`.
- Đã thêm màn chạy test generator Sprint 4 trong tab "Kho tri thức".
- Đã được người dùng xác nhận để chuyển sang Sprint 5.

Thành phẩm demo:

- Template riêng cho Công văn, Thông báo, Tờ trình, Quyết định hành chính đơn giản.
- Generator chỉ sử dụng context được retrieve.
- Bản nháp có các phần: quốc hiệu/tiêu ngữ, kính gửi hoặc căn cứ, nội dung, tổ chức thực hiện, nơi nhận/chữ ký gợi ý.
- Citation gắn với nội dung tham khảo.

Tiêu chí chấp nhận:

- Mỗi loại văn bản sinh ra bố cục khác nhau, phù hợp nghiệp vụ.
- Không có đoạn "căn cứ pháp lý" nếu không có nguồn trong context.
- Người dùng thấy rõ phần cần tự rà soát/chỉnh sửa.

## Sprint 5 - Tích hợp LLM thật có chế độ an toàn

Mục tiêu: Cho phép dùng LLM qua API nhưng vẫn giữ fallback mô phỏng khi chưa có API key.

Trạng thái triển khai:

- Đã thêm provider layer tại `src/llm.py`.
- Đã hỗ trợ `LLM_PROVIDER=mock`, `LLM_PROVIDER=gemini` và `LLM_PROVIDER=openai`.
- Đã đặt `gemini-2.5-flash-lite` làm lựa chọn khuyến nghị cho demo free.
- Đã dùng OpenAI Responses API qua Python SDK khi có `OPENAI_API_KEY`.
- Đã dùng Google GenAI SDK khi có `GEMINI_API_KEY`.
- Đã giữ fallback mock khi thiếu API key, không có nguồn truy xuất, provider sai hoặc API lỗi.
- Đã thêm trạng thái LLM trong sidebar của app.
- Đã được người dùng xác nhận để chuyển sang Sprint 6.

Thành phẩm demo:

- Cấu hình provider qua `.env`.
- Có `MockGenerator` và `LLMGenerator`.
- Prompt yêu cầu AI chỉ dựa trên context, không tự thêm điều luật.
- Xử lý lỗi API/quota/time-out thân thiện.

Tiêu chí chấp nhận:

- Không có API key thì app vẫn chạy bằng mock mode.
- Có API key thì sinh văn bản bằng LLM.
- Khi LLM lỗi, app hiển thị lỗi rõ và không mất dữ liệu người dùng đã nhập.

## Sprint 6 - Kiểm thử chất lượng và chống ảo giác

Mục tiêu: Có cơ chế kiểm tra đầu ra trước khi người dùng sử dụng.

Trạng thái triển khai:

- Đã thêm module rule-based quality check tại `src/quality.py`.
- Đã kiểm tra thể thức cơ bản: quốc hiệu, tiêu ngữ, ngày tháng và thành phần riêng theo loại văn bản.
- Đã kiểm tra nguồn/citation `[S1]`, `[S2]`, `[S3]` và mục `Nguồn tham khảo`.
- Đã cảnh báo rủi ro cao khi không có nguồn truy xuất phù hợp.
- Đã thêm checklist chất lượng ngay sau bản nháp trong tab "Soạn thảo".
- Đã thêm nút chạy test chất lượng Sprint 6 trong tab "Kho tri thức".
- Đã thêm xuất DOCX theo profile thể thức hành chính: A4, Times New Roman, lề chuẩn, cỡ chữ nội dung 13, giãn dòng 1.15, quốc hiệu/tiêu ngữ và số trang đúng vị trí.
- Đã được người dùng xác nhận để chuyển sang Sprint 7.

Thành phẩm demo:

- Bộ test case cho retrieve/generate.
- Bộ kiểm tra rule-based cho thể thức cơ bản.
- Cảnh báo các câu có dấu hiệu thiếu citation.
- Bảng checklist chất lượng ngay trong app.
- Nút tải DOCX để kiểm tra bản nháp trong Word thay vì chỉ xem text trên màn hình.

Tiêu chí chấp nhận:

- Chạy được test tự động.
- App hiển thị checklist: thể thức, nguồn tham khảo, nội dung cần con người kiểm tra.
- Nếu không có nguồn phù hợp, bản nháp bị đánh dấu rủi ro cao.

## Sprint 7 - Hoàn thiện trải nghiệm demo và xuất bản nháp

Mục tiêu: Biến app thành bản demo cuối có thể trình bày trước giảng viên.

Trạng thái triển khai:

- Đã nâng cấp luồng demo nhập yêu cầu -> truy xuất -> sinh nháp -> rà soát -> xuất TXT/DOCX.
- Đã bổ sung phân loại nguồn `system` / `user_upload`, lọc nguồn khi soạn thảo và xóa tài liệu upload riêng.
- Đã bổ sung kịch bản demo 3-5 phút tại `DEMO_SCRIPT.md` và bộ câu lệnh demo tại `data/demo_queries.json`.
- Đã khôi phục và chuẩn hóa bộ dữ liệu/test demo: `admin_docs.json`, `sprint2_sample_docs.json`, `retrieval_test_cases.json`, `generation_test_cases.json`.
- Đang chờ người dùng demo và xác nhận trước khi mở Sprint 8.

Thành phẩm demo:

- Giao diện sạch, có luồng nhập yêu cầu -> truy xuất -> sinh nháp -> rà soát -> xuất nội dung.
- Nâng cấp upload tài liệu riêng: gắn nhãn `system` / `user_upload`, cảnh báo bảo mật, lọc nguồn và xóa tài liệu upload.
- Cho phép tải bản nháp dạng `.txt` hoặc `.docx`.
- Có dữ liệu demo và kịch bản demo sẵn.
- Có README hướng dẫn chạy và video/script demo.

Tiêu chí chấp nhận:

- Người xem có thể chạy demo từ README.
- Demo hoàn chỉnh trong 3-5 phút.
- Có ít nhất 3 kịch bản demo: Công văn, Thông báo, Tờ trình.

## Sprint 8 - Đóng gói báo cáo kỹ thuật

Mục tiêu: Chuẩn bị phần tài liệu kỹ thuật khớp với sản phẩm đã làm.

Thành phẩm demo:

- Sơ đồ kiến trúc RAG.
- Mô tả module: Data, Retriever, Generator, UI, Quality Check.
- Bảng đối chiếu yêu cầu đề tài với chức năng đã triển khai.
- Danh sách rủi ro và cách giảm thiểu trong code.

Tiêu chí chấp nhận:

- Tài liệu kỹ thuật phản ánh đúng app đang chạy.
- Có ảnh chụp màn hình hoặc mô tả luồng demo.
- Sẵn sàng đưa vào báo cáo/slide nhóm.
