# Kế hoạch sprint demo cho hệ thống AI soạn thảo văn bản hành chính RAG

Nguyên tắc làm việc:

- Mỗi sprint phải kết thúc bằng một thành phẩm chạy được để demo.
- Không chuyển sang sprint tiếp theo cho đến khi người dùng xác nhận demo sprint hiện tại đã đạt.
- Sau mỗi sprint cần có: chức năng demo, dữ liệu kiểm thử, tiêu chí chấp nhận và ghi chú rủi ro còn lại.

## Trạng thái hiện tại

- Sprint hiện tại: Sprint 8 - Đồng bộ schema lab, demo và báo cáo.
- Trạng thái: Đang hoàn thiện tài liệu trình bày, báo cáo và kế hoạch demo.
- Nhánh làm việc: `schema-lab-doc-crawler-20260530`.
- Nguyên tắc: không merge/force vào `main` cho đến khi người dùng xác nhận bản lab đạt yêu cầu.

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
- Đã làm nền cho bản demo notebook-style và nhánh schema lab.

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

## Sprint 8 - Schema lab, crawler và đồng bộ báo cáo

Mục tiêu: Đồng bộ sản phẩm theo hướng RAG có kiểm soát, có schema loại văn bản, có dữ liệu crawl công khai và có tài liệu quản lý dự án đầy đủ.

Trạng thái triển khai:

- Đã tạo nhánh riêng `schema-lab-doc-crawler-20260530`, không merge vào `main`.
- Đã thêm catalog loại văn bản trong `data/doc_types/`.
- Đã thêm module `src/doc_type_catalog.py` để route loại văn bản, kiểm tra trường bắt buộc và render template.
- Đã nối catalog vào extractor, generator, LLM fallback và quality checker.
- Đã thêm script `scripts/crawl_public_sources.py` để crawl/tải một số nguồn công khai theo manifest.
- Đã tạo file thuyết trình `docs/THUYET_TRINH_PROJECT_ADMIN_DOC_RAG.md`.
- Đã đồng bộ README, demo script, báo cáo kinh tế kỹ thuật, báo cáo dự toán và kế hoạch chỉnh sửa demo theo cùng phạm vi.

Thành phẩm demo:

- Demo nhận diện `Giấy nghỉ phép` từ câu tự nhiên như `Xuân Tịnh xin nghỉ 4 ngày vì bị ốm`.
- Demo sinh văn bản theo template schema thay vì chỉ phụ thuộc prompt LLM.
- Demo giải thích cách mở rộng hàng chục loại văn bản bằng file JSON.
- Demo nguồn crawl công khai được nạp vào kho tri thức.
- Bộ tài liệu trình bày có cả phần kỹ thuật và phần quản lý dự án.

Tiêu chí chấp nhận:

- App chạy được trên nhánh lab.
- Tài liệu phản ánh đúng trạng thái code hiện tại.
- Báo cáo dự toán, báo cáo kinh tế kỹ thuật, Sprint và demo script dùng cùng phạm vi.
- Có câu trả lời sẵn cho câu hỏi về RAG, BM25, schema, crawler, LLM fallback, Scrum và rủi ro.
- Nhánh lab có thể push riêng để người dùng xem, không ảnh hưởng `main`.

## Sprint 9 - Hybrid retrieval và vector index local

Mục tiêu: Nâng cấp truy xuất từ BM25 thuần sang hybrid search để hỗ trợ cả tìm kiếm từ khóa và tìm kiếm gần nghĩa.

Đã thực hiện:

- Thêm module `src/embeddings.py` để cấu hình embedding provider.
- Thêm `local_hash` embedding chạy offline để demo không phụ thuộc API key.
- Hỗ trợ cấu hình OpenAI embedding qua `.env` khi muốn tìm kiếm ngữ nghĩa thật hơn.
- Thêm `src/vector_store.py` để lưu vector trong SQLite local tại `data/knowledge.sqlite`.
- Mở rộng `src/retriever.py` với 3 chế độ: `bm25`, `vector`, `hybrid`.
- Hybrid retriever gộp điểm BM25 và vector theo trọng số `HYBRID_BM25_WEIGHT` / `HYBRID_VECTOR_WEIGHT`.
- Giao diện mặc định dùng hybrid retrieval và có nút tạo lại chỉ mục vector.
- Giữ fallback BM25 nếu vector backend hoặc embedding provider gặp lỗi.

Tiêu chí chấp nhận:

- App vẫn chạy được ở chế độ demo không API key.
- Test retrieval/generation/quality/extraction hiện có vẫn đạt.
- Người dùng không cần chọn thuật toán truy xuất; app mặc định chạy hybrid.
- Vector index có thể tạo lại từ giao diện và được lưu bền vững trong SQLite.

## Sprint 10 - Clarification flow

Mục tiêu: Khi yêu cầu thiếu thông tin bắt buộc, hệ thống hỏi lại ngắn gọn trước khi sinh bản nháp.

Đã thực hiện:

- Tận dụng `missing_fields` từ `src/extractor.py`.
- Thêm trạng thái `pending_clarification` trong Streamlit để lưu yêu cầu đang chờ bổ sung.
- Hiển thị form hỏi tối đa 3 trường còn thiếu, ví dụ ngày bắt đầu nghỉ, nơi nhận, cơ quan phê duyệt.
- Merge câu trả lời của người dùng vào `RequestAnalysis.slots` trước khi gọi generator.
- Cho phép người dùng bỏ qua và tạo bản nháp với placeholder nếu muốn demo nhanh.

Tiêu chí chấp nhận:

- Ca thiếu thông tin không sinh ngay bản nháp đầy placeholder nếu người dùng chưa xác nhận.
- Thông tin bổ sung xuất hiện trong bản nháp sinh ra.
- Luồng cũ vẫn có đường thoát bằng nút tạo với placeholder.
- Test retrieval/generation/quality/extraction hiện có vẫn đạt.

## Sprint 11 - Chuẩn hóa form và kiểm thử tự động

Mục tiêu: Giảm lỗi form do dữ liệu người dùng nhập chưa chuẩn, đặc biệt các trường ngày tháng và placeholder.

Đã thực hiện:

- Thêm `src/slot_normalizer.py` để chuẩn hóa slot dùng chung trước khi render template.
- Chuẩn hóa ngày nhập về dạng `dd/mm/yyyy`, ví dụ `1/6/2026` thành `01/06/2026`.
- Loại bỏ tiền tố dư trong slot ngày như `từ ngày`, tránh lỗi `từ từ ngày`.
- Tự suy `end_date` cho giấy nghỉ phép khi có `start_date` và `leave_days`.
- Chuẩn hóa lý do nghỉ phép để không kéo theo cụm thời gian vào phần lý do.
- Bổ sung kiểm tra chất lượng cho cụm thời gian lặp, ngày nhập liệu không chuẩn và ngày kết thúc nghỉ phép.
- Thêm `data/form_test_cases.json` và nút `Chạy test form` trong giao diện kiểm thử.
- Bổ sung schema JSON có kiểm soát cho `Công điện`, `Giấy mời`, `Giấy giới thiệu`, `Biên bản`.
- Mở rộng khu vực `Chất lượng bản nháp` ngay dưới bản nháp để thấy rõ điểm, rủi ro, nguồn dùng, lỗi ưu tiên và toàn bộ checklist.
- Bổ sung phần thuyết trình chi tiết về chunking, hybrid retrieval, trả về `SearchResult`, sinh citation và cách chấm điểm chất lượng.

Tiêu chí chấp nhận:

- Giấy nghỉ phép không còn lỗi `từ từ ngày` và tự điền ngày kết thúc khi đủ dữ kiện.
- Các ngày dạng số trong bản nháp thống nhất `dd/mm/yyyy`.
- Các form `Công điện`, `Giấy mời`, `Giấy giới thiệu`, `Biên bản` có test tự động cho slot chính.
- UI hiển thị phần đánh giá bản nháp ở vùng rộng, không chỉ phụ thuộc bảng nhỏ trong cột Studio.
- Test form/template đạt cùng với test retrieval/generation/quality/extraction.

## Sprint 12 - Phủ catalog 30 loại văn bản

Mục tiêu: Không để các loại văn bản còn lại rơi về fallback/generic khi bị hỏi trong báo cáo; mỗi loại trong danh mục app phải có schema/template, nguồn truy xuất và test tự động.

Đã thực hiện:

- Bổ sung `data/doc_types/nd30_remaining.json` để phủ thêm Nghị quyết, Quyết định, Chỉ thị, Quy chế, Quy định, Hướng dẫn, Thông cáo, Báo cáo, Chương trình, Kế hoạch, Phương án, Đề án, Dự án, Bản ghi nhớ, Bản thỏa thuận, Hợp đồng, Giấy ủy quyền, Phiếu gửi, Phiếu chuyển, Phiếu báo, Thư công.
- Bổ sung `data/doc_type_seed_docs.json` để mỗi loại văn bản có ít nhất một nguồn seed đúng loại cho truy xuất.
- Mở rộng `data/retrieval_test_cases.json` để kiểm tra truy xuất toàn danh mục.
- Mở rộng `data/form_test_cases.json` để kiểm tra form/template 30/30 loại văn bản.
- Cập nhật UI kiểm thử thành `Chạy test truy xuất toàn danh mục`.
- Cập nhật README và thuyết trình để nói rõ: đã phủ đủ danh mục, nhưng vẫn là prototype cần human review cho pháp lý/thẩm quyền/số liệu.

Tiêu chí chấp nhận:

- Catalog load đủ 30 loại văn bản.
- Test retrieval toàn danh mục đạt.
- Test form/template đạt 30/30.
- Không còn mô tả sai rằng các loại ngoài nhóm demo chỉ là fallback/generic.

Backlog sau Sprint 12:

- Nâng độ sâu pháp lý/nghiệp vụ cho từng template theo lĩnh vực cụ thể.
- Thêm OCR cho PDF scan.
- Thử nghiệm embedding ngữ nghĩa tốt hơn: OpenAI embedding, sentence-transformers tiếng Việt, hoặc Qdrant/Chroma nếu cần scale.
- Thêm reranking để kiểm soát nguồn trước khi đưa vào prompt sinh văn bản.
- Thêm cơ chế duyệt nguồn trước khi đưa vào kho tri thức chính.
- Thêm lịch sử phiên soạn thảo, phân quyền và nhật ký thao tác.
- Đóng gói Docker hoặc triển khai server nội bộ.
