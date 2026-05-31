# Nội dung thuyết trình đồ án: AdminDoc-RAG

Đề tài: Xây dựng AI hỗ trợ soạn thảo văn bản hành chính sử dụng mô hình RAG
Môn học: Quản lý dự án
Phiên bản trình bày: schema lab branch `schema-lab-doc-crawler-20260530`
Ngày chuẩn bị: 30/05/2026

---

## 1. Tóm tắt dự án

AdminDoc-RAG là hệ thống demo hỗ trợ người dùng soạn thảo văn bản hành chính bằng cách kết hợp:

- Giao diện nhập yêu cầu theo dạng hội thoại.
- Kho tri thức cục bộ gồm văn bản mẫu, dữ liệu upload và tài liệu công khai đã crawl.
- Bộ truy xuất tài liệu liên quan theo mô hình RAG.
- Bộ phân tích yêu cầu để nhận diện loại văn bản và bóc tách thông tin như chủ thể, số ngày nghỉ, lý do, nơi nhận.
- Bộ sinh bản nháp theo thể thức từng loại văn bản.
- Bộ kiểm tra chất lượng và xuất file DOCX.

Mục tiêu của dự án không phải thay thế hoàn toàn cán bộ soạn thảo, mà là tạo bản nháp có căn cứ, có nguồn tham khảo và có checklist để con người rà soát trước khi sử dụng.

---

## 2. Vấn đề đặt ra

Trong thực tế, việc soạn thảo văn bản hành chính gặp một số khó khăn:

- Người dùng không phải lúc nào cũng nhớ đúng thể thức từng loại văn bản.
- Mỗi loại văn bản có bố cục, thành phần bắt buộc và cách diễn đạt khác nhau.
- Nếu chỉ dùng chatbot thông thường, mô hình có thể tự bịa căn cứ hoặc sinh văn bản không đúng mẫu.
- Tài liệu mẫu phân tán ở nhiều nguồn, khó tra cứu nhanh.
- Người dùng thường nhập yêu cầu thiếu thông tin, ví dụ: "Xuân Tịnh xin nghỉ 4 ngày" nhưng thiếu ngày bắt đầu, lý do, đơn vị nhận.

Vì vậy, dự án chọn hướng RAG để AI không chỉ sinh văn bản từ kiến thức sẵn có của mô hình, mà còn dựa vào kho tài liệu đã kiểm soát.

---

## 3. Mục tiêu sản phẩm

Mục tiêu chức năng:

- Nhận yêu cầu soạn thảo bằng tiếng Việt tự nhiên.
- Tự động nhận diện loại văn bản phù hợp.
- Trích xuất các trường thông tin quan trọng từ yêu cầu.
- Truy xuất tài liệu mẫu/quy định liên quan từ kho tri thức.
- Sinh bản nháp văn bản hành chính theo cấu trúc phù hợp.
- Hiển thị nguồn tham khảo và chỉ báo chất lượng.
- Cho phép tải bản nháp dạng TXT hoặc DOCX.
- Hỗ trợ mở rộng thêm loại văn bản mới bằng file cấu hình JSON.

Mục tiêu quản lý dự án:

- Chia dự án thành nhiều sprint nhỏ, mỗi sprint có sản phẩm chạy được.
- Có backlog, tiêu chí nghiệm thu, kiểm thử và demo sau từng giai đoạn.
- Kiểm soát rủi ro về dữ liệu, sai thể thức, ảo giác AI và lỗi API.
- Có sản phẩm đủ ổn định để trình bày trong 3-5 phút.

---

## 4. Ý tưởng chính: RAG cho văn bản hành chính

RAG là viết tắt của Retrieval-Augmented Generation, tức là sinh nội dung có tăng cường bằng truy xuất tài liệu.

Luồng cơ bản:

1. Người dùng nhập yêu cầu.
2. Hệ thống phân tích yêu cầu và xác định loại văn bản.
3. Hệ thống truy xuất các tài liệu/mẫu liên quan trong kho tri thức.
4. Bộ sinh văn bản nhận yêu cầu + thông tin đã bóc tách + tài liệu truy xuất.
5. Bản nháp được sinh ra kèm nguồn tham khảo.
6. Hệ thống kiểm tra lại các thành phần thể thức và cảnh báo rủi ro.

Lý do dùng RAG:

- Giảm ảo giác so với việc chỉ hỏi LLM trực tiếp.
- Dễ kiểm soát nguồn tài liệu.
- Có thể cập nhật tri thức bằng cách thêm tài liệu mới mà không cần huấn luyện lại mô hình.
- Phù hợp với bài toán hành chính vì mẫu và quy định có thể được lưu thành kho tri thức.

---

## 5. Chức năng hiện có

### 5.1. Soạn thảo văn bản

Người dùng nhập yêu cầu như:

```text
Xuân Tịnh xin nghỉ 4 ngày vì bị ốm
```

Hệ thống có thể:

- Nhận diện loại văn bản là `Giấy nghỉ phép`.
- Trích xuất `subject_name = Xuân Tịnh`.
- Trích xuất `leave_days = 4`.
- Trích xuất `reason = bị ốm`.
- Phát hiện còn thiếu `start_date`.
- Sinh bản nháp có placeholder cho thông tin chưa có.

### 5.2. Tự động nhận diện loại văn bản

Thay vì bắt buộc người dùng chọn thủ công, hệ thống có module `src/doc_type_catalog.py` và thư mục `data/doc_types/`.

Mỗi loại văn bản được mô tả bằng một JSON spec trong catalog, có thể là file riêng hoặc được nhóm trong file `nd30_remaining.json`. Ví dụ:

- `cong_van.json`
- `giay_nghi_phep.json`
- `thong_bao.json`
- `to_trinh.json`
- `quyet_dinh_hanh_chinh_don_gian.json`
- `cong_dien.json`
- `giay_moi.json`
- `giay_gioi_thieu.json`
- `bien_ban.json`
- `nd30_remaining.json`

Phạm vi hiện tại sau Sprint 12:

| Mức hỗ trợ | Loại văn bản | Ý nghĩa khi demo |
| --- | --- | --- |
| Có schema/template và test form | Công văn, Thông báo, Tờ trình, Quyết định hành chính đơn giản, Nghị quyết, Quyết định, Chỉ thị, Quy chế, Quy định, Hướng dẫn, Thông cáo, Báo cáo, Biên bản, Chương trình, Kế hoạch, Phương án, Đề án, Dự án, Công điện, Bản ghi nhớ, Bản thỏa thuận, Hợp đồng, Giấy ủy quyền, Giấy mời, Giấy giới thiệu, Giấy nghỉ phép, Phiếu gửi, Phiếu chuyển, Phiếu báo, Thư công | Toàn bộ 30 loại trong danh mục app đều có spec, template khung, nguồn seed để truy xuất đúng loại và test form tự động. |
| Cần rà soát khi dùng thật | Tất cả các loại | Đây là prototype học thuật. Template đã đúng khung loại văn bản, nhưng các thông tin pháp lý, thẩm quyền, số liệu, điều khoản chi tiết và chữ ký vẫn phải được người dùng có chuyên môn kiểm duyệt. |

Trong mỗi file có:

- Tên loại văn bản.
- Các alias/từ khóa nhận diện.
- Ví dụ câu lệnh người dùng.
- Các trường bắt buộc.
- Các trường tùy chọn.
- Các section bắt buộc.
- Template sinh văn bản.

### 5.3. Kho tri thức

Kho tri thức gồm nhiều nguồn:

- `data/admin_docs.json`: dữ liệu mẫu ban đầu.
- `data/sprint2_sample_docs.json`: dữ liệu sprint 2.
- `data/doc_type_seed_docs.json`: nguồn seed nội bộ để mỗi loại văn bản trong catalog đều có ít nhất một nguồn truy xuất đúng loại.
- `data/templates/`: mẫu văn bản dạng TXT.
- `data/processed/crawled_public_docs.json`: dữ liệu đã crawl từ nguồn công khai.
- Tài liệu người dùng upload trong giao diện.

Hệ thống chia tài liệu thành các chunk nhỏ để truy xuất hiệu quả hơn.

### 5.4. Truy xuất tài liệu

Module `src/retriever.py` hiện dùng hybrid retrieval:

- Chuẩn hóa tiếng Việt có dấu và không dấu.
- Loại bỏ stop words.
- Tính điểm BM25 giữa truy vấn và từng chunk.
- Tính điểm vector bằng embedding lưu trong SQLite local.
- Gộp điểm BM25 + vector theo trọng số cấu hình trong `.env`.
- Mặc định chỉ dùng vector để bổ trợ/rerank nguồn BM25, tránh kéo nguồn yếu vào ca thiếu căn cứ.
- Ưu tiên đúng loại văn bản nếu có.
- Trả về top K tài liệu liên quan.

Ví dụ:

```text
soạn công văn đề nghị cung cấp số liệu chuyển đổi số
```

Hệ thống truy xuất các mẫu công văn liên quan, sau đó dùng làm căn cứ cho bản nháp.

### 5.5. Sinh bản nháp

Có hai hướng sinh:

- Sinh theo template nội bộ nếu loại văn bản đã có cấu trúc chuẩn trong `data/doc_types/`.
- Gọi LLM nếu cấu hình provider thật như Gemini hoặc OpenAI.

Trong bản lab, các loại văn bản có catalog sẽ ưu tiên template để siết chặt thể thức. Điều này giúp bản nháp ổn định hơn khi demo.

### 5.6. Kiểm tra chất lượng

Module `src/quality.py` kiểm tra:

- Có quốc hiệu, tiêu ngữ hay không.
- Có section bắt buộc theo loại văn bản hay không.
- Có nguồn tham khảo hay không.
- Có citation như `[S1]`, `[S2]` hay không.
- Có cảnh báo human-in-the-loop hay không.
- Mức rủi ro: thấp, trung bình, cao.

### 5.7. Xuất file DOCX

Module `src/docx_exporter.py` hỗ trợ xuất bản nháp ra DOCX với các thông số:

- Khổ giấy A4.
- Font Times New Roman.
- Cỡ chữ nội dung 13.
- Lề trái 30 mm, lề phải 15 mm, lề trên/dưới 20 mm.
- Quốc hiệu/tiêu ngữ căn giữa.
- Bố cục phù hợp hơn khi mở bằng Word.

### 5.8. Crawl dữ liệu công khai

Script `scripts/crawl_public_sources.py` đọc `data/raw/manifest.json`, tải tài liệu PDF/DOCX nếu có, trích xuất text và lưu vào `data/processed/crawled_public_docs.json`.

Nguồn đã thử crawl:

- Nghị định 30/2020/NĐ-CP về công tác văn thư.
- Quyết định 28/2018/QĐ-TTg về gửi, nhận văn bản điện tử.
- Một số công văn trên cổng văn bản Chính phủ.

Lưu ý khi thuyết trình: crawl dữ liệu là phần mở rộng, không phải điều kiện bắt buộc để demo chính. Một số nguồn cũ dạng `.doc` hoặc PDF scan có thể trích xuất kém, nên hệ thống cần kiểm tra thủ công chất lượng dữ liệu sau khi crawl.

---

## 6. Kiến trúc hệ thống

### 6.1. Các lớp chính

```text
Người dùng
  ↓
Streamlit UI - app.py
  ↓
Phân tích yêu cầu - src/extractor.py
  ↓
Catalog loại văn bản - src/doc_type_catalog.py + data/doc_types/*.json
  ↓
Tiền xử lý/kho tri thức - src/preprocessing.py + src/documents.py
  ↓
Truy xuất hybrid BM25 + vector - src/retriever.py
  ↓
Sinh bản nháp - src/generator.py hoặc src/llm.py
  ↓
Kiểm tra chất lượng - src/quality.py
  ↓
Xuất DOCX - src/docx_exporter.py
```

### 6.2. Luồng xử lý chi tiết

1. UI nhận yêu cầu từ người dùng.
2. `analyze_request()` phân tích câu nhập.
3. `route_doc_type()` trong catalog chọn loại văn bản tốt nhất.
4. Extractor bóc tách slot như tên người, số ngày, lý do, nơi nhận.
5. Hệ thống tạo `retrieval_query` giàu ngữ cảnh hơn câu gốc.
6. Retriever tìm chunk liên quan trong kho tri thức.
7. Generator sinh bản nháp dựa trên loại văn bản, slot và citation.
8. Quality checker chấm điểm và cảnh báo.
9. UI hiển thị bản nháp, nguồn, phân tích yêu cầu và nút tải file.

### 6.3. Vì sao tách catalog loại văn bản?

Nếu viết cứng tất cả logic trong code, mỗi lần thêm loại văn bản mới phải sửa nhiều hàm Python. Với catalog JSON, muốn thêm loại văn bản mới chỉ cần thêm file mới trong `data/doc_types/` gồm:

- `id`
- `name`
- `aliases`
- `examples`
- `required_slots`
- `optional_slots`
- `retrieval_doc_types`
- `required_sections`
- `template_lines`

Nhờ vậy, hệ thống dễ mở rộng từ 5 loại văn bản lên hàng chục loại văn bản.

### 6.4. Chi tiết pipeline RAG và đánh giá

Pipeline của hệ thống không chỉ là "nhập prompt rồi gọi AI", mà đi qua nhiều bước có thể kiểm tra được.

#### Bước 1: Nạp nguồn và chia chunk

Nguồn dữ liệu đầu vào gồm dữ liệu mẫu JSON, template TXT, tài liệu đã crawl, và file người dùng upload. Module `src/preprocessing.py` làm sạch nội dung bằng `clean_text()`, sau đó `build_chunks()` chia tài liệu thành các đoạn nhỏ:

- Mặc định mỗi chunk khoảng 120 từ.
- Mặc định overlap 20 từ để đoạn sau vẫn giữ một phần ngữ cảnh của đoạn trước.
- Khi upload trên UI, người dùng có thể chỉnh kích thước chunk từ 60 đến 400 từ.
- Mỗi chunk giữ metadata: `id`, `parent_id`, `chunk_index`, `total_chunks`, `doc_type`, `source`, `source_kind`.

Ví dụ một tài liệu mẫu "Công văn đề nghị cung cấp số liệu" có thể được tách thành các chunk:

```text
DOC-ABC-CH001: phần đầu, quốc hiệu, kính gửi, trích yếu
DOC-ABC-CH002: nội dung đề nghị, thời hạn, nơi nhận
```

Cách chia này giúp retriever lấy đúng đoạn liên quan thay vì đưa toàn bộ tài liệu dài vào generator.

#### Bước 2: Phân tích yêu cầu và chuẩn hóa slot

Module `src/extractor.py` gọi `analyze_request()` để nhận diện loại văn bản, bóc tách thông tin và tạo truy vấn truy xuất. Với yêu cầu:

```text
Nguyễn Xuân Tịnh xin nghỉ 4 ngày vì ốm từ ngày 1/6/2026
```

Kết quả mong muốn:

```text
doc_type      = Giấy nghỉ phép
subject_name  = Nguyễn Xuân Tịnh
leave_days    = 4
reason        = ốm
start_date    = 01/06/2026
end_date      = 04/06/2026
```

Module `src/slot_normalizer.py` chuẩn hóa các lỗi thường gặp:

- `1/6/2026` thành `01/06/2026`.
- Bỏ tiền tố thừa như `từ ngày`, để template không sinh ra lỗi `từ từ ngày`.
- Suy ra `end_date` từ `start_date + leave_days - 1` khi đủ dữ liệu.
- Chuẩn hóa các trường thời gian như `event_time`, `deadline`, `valid_until`.

Nếu thiếu trường bắt buộc, UI hỏi lại tối đa 3 thông tin quan trọng trước khi sinh bản nháp. Người dùng vẫn có thể chọn tạo với placeholder khi muốn demo nhanh.

#### Bước 3: Truy xuất RAG theo hướng hybrid

Module `src/retriever.py` trả về danh sách `SearchResult`. Mỗi kết quả có:

```text
document         = chunk được chọn
score            = điểm tổng hợp
matched_terms    = từ khóa hoặc nhãn semantic
retrieval_method = bm25 | vector | hybrid
bm25_score       = điểm từ khóa
vector_score     = điểm ngữ nghĩa
```

Luồng hybrid gồm hai nhánh:

- BM25 bắt tốt từ khóa hành chính, tên loại văn bản, số hiệu, nơi nhận, thời hạn.
- Vector search dùng embedding lưu trong SQLite local để hỗ trợ truy vấn gần nghĩa.
- Hybrid merge chuẩn hóa điểm BM25/vector rồi gộp theo trọng số cấu hình.
- Mặc định không để vector-only kéo nguồn yếu vào bản nháp; vector chủ yếu dùng để bổ trợ/rerank.

Ví dụ truy vấn:

```text
soạn công điện khẩn gửi UBND các tỉnh về ứng phó bão, thời hạn trước 17:00 ngày 5/6/2026
```

Retriever ưu tiên các chunk có `doc_type = Công điện` hoặc nội dung gần với "khẩn", "thời hạn", "báo cáo", "ứng phó". UI hiển thị top K nguồn, điểm, phương thức truy xuất và đoạn nguồn để người dùng kiểm chứng.

#### Bước 4: Sinh bản nháp có citation

Module `src/generator.py` hoặc `src/llm.py` sinh bản nháp. Nếu loại văn bản đã có catalog trong `data/doc_types/`, hệ thống ưu tiên `render_template_draft()` để giữ cấu trúc ổn định:

- Điền slot đã trích xuất vào template.
- Chèn citation như `[S1]`, `[S2]` theo nguồn truy xuất.
- Giữ placeholder cho dữ liệu chưa chắc chắn thay vì tự bịa.
- Thêm ghi chú human-in-the-loop để người dùng rà soát trước khi dùng.

Với ví dụ giấy nghỉ phép ở trên, template sinh dòng:

```text
Được nghỉ phép trong thời gian: 4 ngày (từ 01/06/2026 đến 04/06/2026).
```

Nếu không có nguồn phù hợp, bản nháp phải có cảnh báo kiểu `CHƯA ĐỦ NGUỒN KIỂM CHỨNG` để tránh người dùng hiểu nhầm rằng nội dung đã được xác thực.

#### Bước 5: Đánh giá chất lượng bản nháp

Module `src/quality.py` tạo `QualityReport` gồm `score`, `risk_level`, và danh sách `QualityCheck`. Điểm bắt đầu từ 100 và bị trừ theo mức nghiêm trọng:

- `high`: lỗi quan trọng như thiếu quốc hiệu, thiếu tiêu ngữ, thiếu section bắt buộc, thiếu nguồn.
- `medium`: lỗi cần rà soát như ngày tháng chưa thống nhất, citation thiếu, thời gian bị lặp.
- `low`: cảnh báo nhẹ như placeholder còn cần người dùng điền.

Các nhóm kiểm tra chính:

| Nhóm kiểm tra | Ví dụ |
| --- | --- |
| Thể thức chung | Quốc hiệu, tiêu ngữ, dòng ngày tháng |
| Thể thức theo loại | Công văn cần `Kính gửi`, Tờ trình cần `Kiến nghị`, Quyết định cần các `Điều` |
| Nhất quán form | Không có `từ từ ngày`, ngày dạng số phải là `dd/mm/yyyy`, không còn `{{placeholder}}` |
| Nguồn và citation | Có nguồn truy xuất, có mục nguồn tham khảo, có marker `[S1]` |
| Chống ảo giác | Không tự thêm căn cứ pháp lý nếu căn cứ đó không nằm trong nguồn |
| Human review | Có nhắc người dùng rà soát trước khi ban hành |

Ví dụ lỗi đã phát hiện trong quá trình test:

```text
Input: Nguyễn Xuân Tịnh xin nghỉ 4 ngày vì ốm từ ngày 1/6/2026
Lỗi cũ: từ từ ngày 1/6/2026 đến [Ngày kết thúc]
Sau sửa: từ 01/06/2026 đến 04/06/2026
```

UI hiện hiển thị phần đánh giá rộng ngay dưới bản nháp: điểm, mức rủi ro, số mục cần kiểm tra, số nguồn dùng, danh sách lỗi ưu tiên và toàn bộ checklist. Cột Studio vẫn giữ bản tóm tắt nhanh.

---

## 7. Công nghệ sử dụng

Ngôn ngữ và framework:

- Python 3.12.
- Streamlit cho giao diện demo web local.

Xử lý dữ liệu:

- `pydantic` hoặc dataclass cho mô hình dữ liệu.
- `pypdf` để trích xuất nội dung PDF.
- `python-docx` để xuất file DOCX.
- `requests` và `beautifulsoup4` để crawl nguồn công khai.

AI/LLM:

- Mock mode để demo ổn định khi không có API key.
- Google Gemini qua `google-genai`.
- OpenAI qua package `openai`.

Truy xuất:

- Hybrid search trong `src/retriever.py`.
- BM25 cục bộ để giữ độ chính xác từ khóa, số hiệu, tên loại văn bản.
- Vector search lưu embedding trong SQLite local qua `src/vector_store.py`.
- Cấu hình embedding qua `src/embeddings.py`, mặc định `local_hash` để chạy offline, có thể đổi sang OpenAI embedding khi cần ngữ nghĩa tốt hơn.
- Chuẩn hóa tiếng Việt có dấu/không dấu bằng `unicodedata`.

Lưu trữ:

- JSON cho dữ liệu mẫu và catalog loại văn bản.
- SQLite local trong `src/storage.py` để lưu chunk và metadata.
- Bảng vector trong SQLite để lưu embedding bền vững cho hybrid retrieval.
- File upload riêng được lưu local và ignore khỏi git.

Quản lý mã nguồn:

- Git/GitHub.
- Nhánh chính `main` giữ bản ổn định.
- Nhánh thử nghiệm `schema-lab-doc-crawler-20260530` chứa phần catalog và crawler.

---

## 8. Cách triển khai và chạy demo

### 8.1. Cài môi trường

```powershell
cd E:\.vscode\Ki_6\RAG\AdminDoc-RAG-schema-lab
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Nếu đã có `.venv` thì chỉ cần:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 8.2. Chạy app

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

Nếu port 8501 đang bận:

```powershell
.\.venv\Scripts\python -m streamlit run app.py --server.port 8502
```

### 8.3. Cấu hình LLM

File `.env` không đưa lên git. Demo có thể chạy mock mode không cần API key.

Gemini:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_TIMEOUT_SECONDS=30
GEMINI_MAX_OUTPUT_TOKENS=1800
```

OpenAI:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=your_model_here
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_OUTPUT_TOKENS=1800
```

Mock mode:

```env
LLM_PROVIDER=mock
```

### 8.4. Chạy kiểm tra nhanh

```powershell
.\.venv\Scripts\python -m compileall -q app.py src scripts\crawl_public_sources.py crawler.py data_auditor.py
```

### 8.5. Chạy crawler

```powershell
.\.venv\Scripts\python scripts\crawl_public_sources.py --manifest data\raw\manifest.json --output data\processed\crawled_public_docs.json
```

---

## 9. Kịch bản demo đề xuất

### Demo 1: Luồng chính RAG

Nhập:

```text
soạn công văn đề nghị cung cấp số liệu chuyển đổi số
```

Trình bày:

- Hệ thống nhận yêu cầu.
- Truy xuất nguồn liên quan.
- Sinh bản nháp công văn.
- Bản nháp có citation `[S1]`.
- Có checklist chất lượng.
- Có thể tải DOCX.

### Demo 2: Tự động nhận diện và bóc tách thông tin

Nhập:

```text
Xuân Tịnh xin nghỉ 4 ngày vì bị ốm
```

Trình bày:

- Hệ thống tự nhận diện `Giấy nghỉ phép`.
- Bóc tách tên, số ngày nghỉ, lý do.
- Phát hiện thiếu ngày bắt đầu.
- Giữ placeholder để người dùng bổ sung.

### Demo 3: Thêm nguồn tri thức

Trình bày:

- Upload file `.txt`, `.md`, `.json`, `.pdf` hoặc `.docx`.
- Hệ thống parse và chunk tài liệu.
- Người dùng có thể lọc nguồn: tất cả nguồn, nguồn hệ thống, hoặc chỉ upload riêng.

### Demo 4: Kiểm soát rủi ro

Nhập một yêu cầu quá xa kho tri thức:

```text
soạn công văn về ký số tự động liên thông quốc gia
```

Trình bày:

- Nếu không có nguồn phù hợp, hệ thống cảnh báo.
- Không nên sinh tự tin khi thiếu căn cứ.
- Đây là điểm khác biệt giữa RAG có kiểm soát và chatbot thông thường.

---

## 10. Quản lý dự án theo Scrum

### 10.1. Vai trò Scrum

Product Owner:

- Xác định nhu cầu: AI hỗ trợ soạn thảo văn bản hành chính.
- Ưu tiên các chức năng demo quan trọng.
- Nghiệm thu từng sprint.

Scrum Master:

- Theo dõi tiến độ sprint.
- Loại bỏ trở ngại như lỗi chạy app, lỗi API, lỗi giao diện.
- Đảm bảo sprint có đầu ra rõ ràng.

Development Team:

- Xây dựng UI.
- Xây dựng xử lý dữ liệu.
- Xây dựng retrieval/generation.
- Kiểm thử và đóng gói demo.

Trong đồ án cá nhân/nhóm nhỏ, một người có thể kiêm nhiều vai trò, nhưng vẫn cần trình bày rõ trách nhiệm của từng vai trò.

### 10.2. Product backlog

Các hạng mục backlog chính:

- Tạo giao diện nhập yêu cầu soạn thảo.
- Tạo kho tri thức mẫu.
- Tiền xử lý và chunk tài liệu.
- Tìm kiếm tài liệu liên quan.
- Sinh bản nháp theo loại văn bản.
- Tự động nhận diện loại văn bản.
- Bóc tách thông tin cụ thể từ yêu cầu.
- Hỏi lại thông tin còn thiếu trước khi sinh bản nháp.
- Chuẩn hóa dữ liệu form như ngày tháng, thời lượng và placeholder trước khi render.
- Kiểm tra chất lượng văn bản sinh ra.
- Xuất file DOCX.
- Upload tài liệu người dùng.
- Crawl tài liệu công khai.
- Hybrid retrieval BM25 + vector.
- Quản lý cấu hình LLM.
- Chuẩn bị tài liệu thuyết trình và báo cáo.

### 10.3. Sprint đã thực hiện

| Sprint | Mục tiêu | Kết quả chính | Tiêu chí nghiệm thu |
| --- | --- | --- | --- |
| Sprint 1 | Nền demo RAG mô phỏng | App Streamlit, dữ liệu mẫu, sinh bản nháp cơ bản | Chạy được app, có bản nháp và nguồn tham khảo |
| Sprint 2 | Kho tri thức và tiền xử lý | Upload, parse, clean, chunk tài liệu | Nạp được ít nhất 5 tài liệu mẫu |
| Sprint 3 | Retriever tốt hơn | BM25, tìm kiếm không dấu, test truy xuất | 5/5 test retrieval đạt top 3 |
| Sprint 4 | Generator theo loại văn bản | Template công văn, thông báo, tờ trình, quyết định | Mỗi loại có cấu trúc riêng và citation |
| Sprint 5 | Tích hợp LLM thật | Provider mock/gemini/openai, fallback khi lỗi | App vẫn chạy khi thiếu API key |
| Sprint 6 | Kiểm tra chất lượng | Checklist, risk level, export DOCX | Có điểm chất lượng và cảnh báo |
| Sprint 7 | Hoàn thiện demo | Notebook-style UI, upload riêng, script demo | Demo hoàn chỉnh 3-5 phút |
| Sprint 8 | Schema lab, crawler và báo cáo | Catalog JSON, auto route, crawl nguồn công khai, đồng bộ tài liệu | Tài liệu phản ánh đúng code, branch lab không ảnh hưởng main |
| Sprint 9 | Hybrid retrieval | Vector index SQLite, embedding config, gộp điểm BM25 + vector | App vẫn chạy offline, test hiện có đạt, mặc định dùng hybrid |
| Sprint 10 | Clarification flow | Hỏi lại tối đa 3 trường thiếu, merge vào slot trước khi sinh | Giảm placeholder, vẫn có nút tạo nhanh với placeholder |
| Sprint 11 | Chuẩn hóa form | Chuẩn hóa ngày dd/mm/yyyy, tự suy ngày kết thúc nghỉ phép, test form | Không lặp `từ từ ngày`, form test đạt |
| Sprint 12 | Phủ catalog 30 loại | Thêm spec/template còn thiếu, seed docs đúng loại, test retrieval/form toàn danh mục | Retrieval 35/35, form 30/30, catalog load đủ 30 loại |

### 10.4. Definition of Done

Một chức năng được xem là hoàn thành khi:

- Chạy được trong app Streamlit.
- Có dữ liệu demo hoặc test case minh họa.
- Không làm hỏng luồng demo chính.
- Có xử lý lỗi cơ bản.
- Không commit `.env` hoặc dữ liệu nhạy cảm.
- Có thể trình bày được giá trị của chức năng.

### 10.5. Rủi ro dự án và cách giảm thiểu

| Rủi ro | Ảnh hưởng | Cách giảm thiểu |
| --- | --- | --- |
| LLM sinh sai nội dung | Văn bản không đáng tin | Dùng RAG, citation, checklist, human review |
| Thiếu dữ liệu mẫu | Truy xuất yếu | Cho upload, crawl nguồn công khai, thêm catalog |
| PDF scan không trích xuất được | Kho tri thức thiếu nội dung | Cảnh báo chất lượng crawl, dùng nguồn text/PDF rõ hơn |
| API key lỗi hoặc hết quota | Demo gián đoạn | Mock mode và fallback |
| Giao diện khó dùng | Demo kém thuyết phục | Tối giản nút, bố cục notebook, tập trung luồng chính |
| Thêm loại văn bản mới tốn công | Khó mở rộng | Dùng `data/doc_types/*.json` làm schema |
| Dữ liệu upload nhạy cảm | Rủi ro bảo mật | Lưu local, ignore git, cảnh báo người dùng |

---

## 11. Điểm mới của nhánh schema lab

Nhánh lab bổ sung các ý tưởng quan trọng:

- Tách cấu trúc loại văn bản ra file JSON.
- Cho phép tự động chọn loại văn bản dựa trên alias, examples và intent.
- Cho phép khai báo trường bắt buộc theo từng loại văn bản.
- Template sinh văn bản nằm trong catalog, giúp siết chặt thể thức.
- Quality checker đọc section bắt buộc từ catalog.
- Crawler tải và xử lý tài liệu công khai thành dữ liệu RAG.

Điểm này phù hợp với câu hỏi: "Nếu có hàng chục loại văn bản thì làm sao mở rộng?"

Câu trả lời: không viết cứng từng loại vào code chính, mà thêm file JSON đặc tả loại văn bản. Code chỉ đóng vai trò engine đọc catalog và xử lý theo schema.

---

## 12. Nội dung slide đề xuất

### Slide 1: Tên đề tài

Nội dung:

- Xây dựng AI hỗ trợ soạn thảo văn bản hành chính sử dụng RAG.
- Nhóm/sinh viên thực hiện.
- Môn Quản lý dự án.

Lời nói:

> Đề tài của em tập trung xây dựng một hệ thống AI hỗ trợ tạo bản nháp văn bản hành chính. Hệ thống không thay thế người soạn thảo mà hỗ trợ tra cứu mẫu, tạo bản nháp và kiểm tra chất lượng.

### Slide 2: Bài toán

Nội dung:

- Văn bản hành chính có nhiều loại và thể thức khác nhau.
- Người dùng dễ nhập thiếu thông tin.
- Chatbot thông thường dễ sinh nội dung không có nguồn.

Lời nói:

> Vì vậy nhóm chọn hướng RAG, nghĩa là trước khi sinh văn bản, hệ thống truy xuất tài liệu liên quan trong kho tri thức đã kiểm soát.

### Slide 3: Mục tiêu

Nội dung:

- Tự nhận diện loại văn bản.
- Trích xuất thông tin.
- Truy xuất nguồn.
- Sinh bản nháp.
- Kiểm tra chất lượng.
- Xuất DOCX.

### Slide 4: Kiến trúc hệ thống

Nội dung:

```text
Input → Extractor → Retriever → Generator → Quality Check → Export
```

Lời nói:

> Điểm quan trọng là hệ thống tách thành nhiều module, mỗi module phụ trách một nhiệm vụ rõ ràng, giúp dễ kiểm thử và mở rộng.

### Slide 5: Kho tri thức

Nội dung:

- Dữ liệu mẫu JSON.
- Template TXT.
- Tài liệu crawl.
- Upload riêng.
- Chunk tài liệu.

### Slide 6: Truy xuất RAG

Nội dung:

- BM25.
- Vector index SQLite.
- Hybrid ranking.
- Chuẩn hóa tiếng Việt.
- Lọc theo loại văn bản.
- Top K nguồn liên quan.
- Kết quả trả về có điểm tổng hợp, điểm BM25, điểm vector, từ khóa khớp và đoạn nguồn.

### Slide 7: Phân tích yêu cầu

Nội dung:

Ví dụ:

```text
Xuân Tịnh xin nghỉ 4 ngày vì bị ốm
```

Kết quả:

- Loại: Giấy nghỉ phép.
- Chủ thể: Xuân Tịnh.
- Số ngày: 4.
- Lý do: bị ốm.
- Thiếu: ngày bắt đầu.

### Slide 8: Catalog loại văn bản

Nội dung:

- Toàn bộ 30 loại văn bản trong danh mục app có JSON spec/template.
- Có alias, required slots, template, required sections và nguồn seed truy xuất.
- Test form hiện phủ 30/30 loại; test retrieval phủ toàn danh mục.
- Thêm loại mới không cần sửa nhiều code.

### Slide 9: Sinh bản nháp và kiểm soát chất lượng

Nội dung:

- Template hoặc LLM.
- Citation `[S1]`.
- Checklist.
- Điểm chất lượng, mức rủi ro, số mục cần rà soát.
- Kiểm tra lỗi form như ngày tháng, placeholder, citation, nguồn.
- Human-in-the-loop.

### Slide 10: Scrum/Sprint

Nội dung:

- 12 sprint/nhánh lab.
- Mỗi sprint có demo chạy được.
- Có backlog, DoD, test case.

### Slide 11: Demo

Nội dung:

- Chạy app.
- Nhập yêu cầu công văn.
- Nhập yêu cầu nghỉ phép.
- Tải DOCX.

### Slide 12: Kết luận và hướng phát triển

Nội dung:

- Đã có prototype RAG hoàn chỉnh.
- Đã phủ catalog 30 loại văn bản bằng JSON spec/template.
- Đã có hybrid BM25 + vector local, clarification flow và kiểm thử form 30/30; hướng tới OCR, phân quyền người dùng, tăng độ sâu pháp lý từng template và vector backend mạnh hơn khi cần scale.

---

## 13. Câu hỏi lý thuyết có thể bị hỏi

### Câu 1: RAG là gì?

RAG là kỹ thuật kết hợp truy xuất tài liệu với sinh nội dung. Thay vì để mô hình tự trả lời hoàn toàn, hệ thống tìm các tài liệu liên quan trước, rồi dùng chúng làm ngữ cảnh để sinh câu trả lời hoặc văn bản.

### Câu 2: Vì sao không dùng LLM trực tiếp?

Vì LLM trực tiếp có thể sinh nội dung nghe hợp lý nhưng không có căn cứ. Với văn bản hành chính, sai thể thức hoặc sai căn cứ là rủi ro lớn. RAG giúp kiểm soát nguồn, giảm ảo giác và cho người dùng kiểm chứng.

### Câu 3: BM25 là gì?

BM25 là thuật toán xếp hạng tài liệu theo mức độ liên quan giữa truy vấn và tài liệu. Nó xét tần suất từ khóa, độ hiếm của từ và độ dài tài liệu. Trong project này, BM25 vẫn rất quan trọng vì bắt tốt từ khóa hành chính, số hiệu văn bản và tên loại văn bản; sau Sprint 9 nó được kết hợp với vector search theo hướng hybrid.

### Câu 4: Chunking là gì?

Chunking là chia tài liệu dài thành các đoạn nhỏ. Khi truy xuất, hệ thống tìm đoạn liên quan nhất thay vì đưa toàn bộ tài liệu vào generator. Điều này giúp giảm nhiễu và tiết kiệm token.

### Câu 5: Vì sao cần human-in-the-loop?

Văn bản hành chính có yếu tố pháp lý, thẩm quyền và trách nhiệm ban hành. AI chỉ hỗ trợ tạo bản nháp. Người dùng vẫn phải kiểm tra lại căn cứ, số liệu, chức danh, nơi nhận và thể thức trước khi sử dụng.

### Câu 6: Làm sao hệ thống giảm ảo giác?

Hệ thống giảm ảo giác bằng các cách:

- Chỉ sinh dựa trên nguồn truy xuất.
- Hiển thị citation.
- Cảnh báo khi thiếu nguồn.
- Dùng template cố định cho loại văn bản đã biết.
- Có checklist chất lượng.
- Giữ placeholder thay vì tự bịa thông tin thiếu.

### Câu 7: Vì sao cần tự động nhận diện loại văn bản?

Nếu bắt người dùng chọn thủ công, trải nghiệm kém và dễ chọn sai. Tự động nhận diện giúp người dùng nhập tự nhiên hơn, ví dụ "xin nghỉ 4 ngày" thì hệ thống biết đó là giấy nghỉ phép.

### Câu 8: Nếu người dùng nhập thiếu thông tin thì sao?

Hiện tại hệ thống phát hiện `missing_fields` và hỏi lại tối đa 3 thông tin quan trọng trước khi sinh bản nháp. Nếu người dùng muốn demo nhanh hoặc chưa có đủ dữ liệu, vẫn có thể chọn tạo với placeholder.

### Câu 9: Vì sao dùng JSON để mô tả loại văn bản?

JSON giúp tách dữ liệu cấu hình khỏi code. Khi muốn thêm loại văn bản mới, chỉ cần thêm file JSON mô tả alias, trường bắt buộc và template, thay vì sửa nhiều hàm Python.

### Câu 10: RAG khác gì fine-tuning?

Fine-tuning là huấn luyện thêm mô hình để thay đổi hành vi mô hình. RAG là bổ sung tri thức bằng truy xuất tài liệu ngoài. Với bài toán văn bản hành chính, RAG phù hợp hơn vì tài liệu có thể thay đổi và cần cập nhật thường xuyên.

---

## 14. Câu hỏi về code có thể bị hỏi

### Câu 1: File `app.py` làm gì?

`app.py` là entry point của ứng dụng Streamlit. File này dựng giao diện, quản lý session state, gọi các module phân tích, truy xuất, sinh văn bản, kiểm tra chất lượng và xuất file.

### Câu 2: `src/extractor.py` làm gì?

File này phân tích yêu cầu người dùng:

- Chuẩn hóa câu nhập.
- Nhận diện loại văn bản.
- Bóc tách slot.
- Tạo retrieval query.
- Trả về danh sách thông tin còn thiếu.

### Câu 3: `src/doc_type_catalog.py` làm gì?

File này đọc các JSON spec trong `data/doc_types/` (mỗi file có thể chứa một hoặc nhiều spec), chọn loại văn bản phù hợp, kiểm tra trường bắt buộc, trả về section cần có và render template theo placeholder.

### Câu 4: `src/retriever.py` làm gì?

File này triển khai các retriever:

- Tokenize truy vấn và tài liệu.
- Tính điểm BM25.
- Gọi vector store SQLite để lấy điểm gần nghĩa.
- Gộp điểm BM25 + vector trong `HybridRetriever`.
- Lọc theo loại văn bản nếu cần.
- Trả về danh sách `SearchResult`.

### Câu 5: `src/generator.py` làm gì?

File này sinh bản nháp rule-based/template. Nó xây citation từ kết quả truy xuất, chọn form theo loại văn bản và tạo bản nháp có nguồn tham khảo.

### Câu 6: `src/llm.py` làm gì?

File này quản lý provider LLM:

- Đọc `.env`.
- Chọn mock/gemini/openai.
- Gọi API nếu có key.
- Fallback về mock khi thiếu key hoặc lỗi.
- Với loại văn bản có catalog template, ưu tiên template để giữ cấu trúc ổn định.

### Câu 7: `src/quality.py` làm gì?

File này chấm chất lượng bản nháp:

- Kiểm tra thể thức.
- Kiểm tra citation.
- Kiểm tra nguồn tham khảo.
- Cảnh báo rủi ro.
- Tính score.

### Câu 8: `src/docx_exporter.py` làm gì?

File này chuyển bản nháp text sang DOCX với profile định dạng văn bản hành chính: A4, Times New Roman, cỡ chữ, lề, header và số trang.

### Câu 9: `scripts/crawl_public_sources.py` làm gì?

Script này đọc manifest nguồn công khai, tải file PDF/DOCX/TXT, trích xuất nội dung, chuẩn hóa thành document JSON để đưa vào kho tri thức.

### Câu 10: Làm sao thêm một loại văn bản mới?

Các bước:

1. Tạo file mới trong `data/doc_types/`, ví dụ `giay_moi.json`.
2. Khai báo `name`, `aliases`, `examples`.
3. Khai báo `required_slots` và `optional_slots`.
4. Khai báo `required_sections`.
5. Viết `template_lines` có placeholder.
6. Thêm tài liệu mẫu hoặc nguồn liên quan vào kho tri thức.
7. Chạy test bằng vài câu nhập mẫu.

---

## 15. Câu hỏi quản lý dự án có thể bị hỏi

### Câu 1: Vì sao chọn Scrum?

Vì yêu cầu dự án thay đổi liên tục trong quá trình làm demo. Scrum cho phép chia nhỏ công việc thành sprint, sau mỗi sprint có sản phẩm chạy được để nhận phản hồi và điều chỉnh.

### Câu 2: Sprint nào quan trọng nhất?

Sprint 3 và Sprint 4 rất quan trọng vì tạo lõi RAG: truy xuất đúng nguồn và sinh văn bản theo cấu trúc. Sprint 6 cũng quan trọng vì thêm kiểm soát chất lượng, giúp sản phẩm đáng tin hơn.

### Câu 3: Tiêu chí nghiệm thu tổng thể là gì?

Hệ thống được nghiệm thu khi:

- Chạy được local.
- Có thể soạn ít nhất vài loại văn bản.
- Có truy xuất nguồn.
- Có kiểm tra chất lượng.
- Có xuất file.
- Có demo ổn định.
- Có tài liệu kỹ thuật và kế hoạch sprint.

### Câu 4: Làm sao quản lý rủi ro API?

Hệ thống có mock mode. Nếu không có API key, hết quota hoặc API lỗi, app vẫn chạy và sinh bản nháp mô phỏng. Điều này giúp demo không phụ thuộc hoàn toàn vào dịch vụ bên ngoài.

### Câu 5: Làm sao chứng minh tiến độ?

Tiến độ được thể hiện qua:

- File `SPRINTS.md`.
- Các test case JSON.
- Commit Git.
- Demo script.
- Các chức năng chạy được sau từng sprint.

### Câu 6: Product backlog được ưu tiên thế nào?

Ưu tiên theo giá trị demo:

1. Chạy được app.
2. Có dữ liệu và truy xuất.
3. Sinh bản nháp.
4. Kiểm soát chất lượng.
5. Xuất file.
6. Mở rộng tự động nhận diện và crawler.

### Câu 7: Nếu thiếu thời gian thì cắt gì?

Không cắt luồng chính RAG. Có thể cắt các phần mở rộng như crawler, LLM thật hoặc giao diện nâng cao. Luồng tối thiểu phải giữ: nhập yêu cầu, retrieve, sinh nháp, nguồn tham khảo, checklist.

---

## 16. Câu hỏi phản biện khó và cách trả lời

### Câu 1: Văn bản sinh ra có đúng pháp luật không?

Trả lời:

> Hệ thống hiện là công cụ hỗ trợ soạn thảo bản nháp, không phải hệ thống ban hành văn bản tự động. Vì vậy sản phẩm có citation, checklist và cảnh báo human-in-the-loop. Người có thẩm quyền vẫn phải kiểm tra pháp lý, thể thức và nội dung trước khi sử dụng.

### Câu 2: Nếu nguồn trong kho tri thức sai thì sao?

Trả lời:

> RAG phụ thuộc vào chất lượng kho tri thức. Vì vậy dự án có bước kiểm tra dữ liệu sau crawl, có metadata nguồn và cho phép người dùng kiểm soát nguồn. Hướng phát triển là thêm quy trình duyệt dữ liệu trước khi đưa vào kho chính thức.

### Câu 3: Dự án đã dùng vector database chưa?

Trả lời:

> Dự án đã bổ sung vector index local trong SQLite và chạy theo chế độ hybrid BM25 + vector. BM25 vẫn giữ vai trò quan trọng cho từ khóa hành chính, số hiệu, tên loại văn bản; vector search hỗ trợ rerank và truy vấn gần nghĩa. Mặc định demo dùng `local_hash` embedding để chạy offline và không tự nhận vector-only trong hybrid nhằm tránh nguồn yếu; khi cần tìm kiếm ngữ nghĩa thật hơn có thể đổi sang OpenAI embedding hoặc backend như Chroma/Qdrant.

### Câu 4: Nếu câu nhập rất mơ hồ thì hệ thống làm gì?

Trả lời:

> Hệ thống phát hiện thiếu trường và chuyển sang clarification flow. Ví dụ thiếu ngày bắt đầu nghỉ hoặc nơi nhận, app sẽ hỏi lại tối đa 3 trường. Nếu người dùng chưa có thông tin, vẫn có thể tạo bản nháp với placeholder để rà soát sau.

### Câu 4b: Làm sao tránh lỗi form như ngày tháng không thống nhất?

Trả lời:

> Dự án có lớp chuẩn hóa slot trước khi render template. Ví dụ `1/6/2026` được đổi thành `01/06/2026`, cụm nhập `từ ngày 1/6/2026` được rút còn ngày chuẩn để tránh lỗi `từ từ ngày`, và giấy nghỉ phép tự suy ngày kết thúc nếu có ngày bắt đầu cùng số ngày nghỉ. Ngoài ra có bộ `form_test_cases.json` để kiểm thử tự động các lỗi form thường gặp.

### Câu 5: Có thể dùng trong cơ quan thật chưa?

Trả lời:

> Hiện tại đây là prototype/demo. Để dùng thật cần bổ sung phân quyền, nhật ký thao tác, kiểm duyệt nguồn, bảo mật dữ liệu, ký số, quy trình phê duyệt và kiểm thử pháp lý sâu hơn.

### Câu 6: Điểm khác biệt so với ChatGPT hoặc NotebookLM là gì?

Trả lời:

> Ý tưởng giao diện và luồng hỏi đáp có tham khảo NotebookLM/ChatGPT, nhưng project tập trung vào miền văn bản hành chính Việt Nam. Hệ thống có catalog loại văn bản, slot bắt buộc, template thể thức, checklist chất lượng và xuất DOCX theo profile hành chính.

### Câu 7: Nếu thêm 30 loại văn bản thì có phải sửa code nhiều không?

Trả lời:

> Không nên sửa code chính cho từng loại. Cách thiết kế hiện tại là thêm JSON spec cho từng loại văn bản trong `data/doc_types/`. Engine đọc catalog và xử lý theo schema chung.
>
> Hiện nhóm đã phủ đủ 30 loại văn bản đang có trong danh mục app. Mỗi loại có JSON spec/template, nguồn seed trong `data/doc_type_seed_docs.json`, test truy xuất đúng loại trong `data/retrieval_test_cases.json` và test form trong `data/form_test_cases.json`. Điểm cần nói rõ khi bảo vệ là đây là prototype: form đã đúng khung loại văn bản, nhưng các căn cứ pháp lý, thẩm quyền, số liệu và nội dung chi tiết vẫn phải được người dùng rà soát.

---

## 17. Hướng phát triển tiếp theo

Các hướng phát triển sau demo:

- Nâng cấp embedding/vector backend: OpenAI embedding, sentence-transformers tiếng Việt, Chroma hoặc Qdrant khi kho dữ liệu lớn hơn.
- Thêm OCR cho PDF scan.
- Chuẩn hóa pipeline crawl, duyệt nguồn và đánh dấu độ tin cậy.
- Nâng độ sâu nghiệp vụ cho từng template: căn cứ pháp lý theo lĩnh vực, thẩm quyền ban hành, điều khoản chuyên ngành và mẫu phụ lục đi kèm.
- Thêm phân quyền người dùng.
- Thêm lịch sử phiên soạn thảo.
- Thêm cơ chế so sánh bản nháp với mẫu chuẩn.
- Tạo dashboard quản lý sprint/backlog/test case.
- Triển khai nội bộ bằng Docker hoặc server riêng.

---

## 18. Kết luận

AdminDoc-RAG chứng minh được một hướng triển khai khả thi cho bài toán hỗ trợ soạn thảo văn bản hành chính:

- Có quy trình RAG rõ ràng.
- Có kho tri thức và truy xuất nguồn.
- Có phân tích yêu cầu tự nhiên.
- Có sinh bản nháp theo thể thức.
- Có kiểm tra chất lượng và xuất file.
- Có quản lý dự án theo sprint.
- Có hướng mở rộng bằng catalog JSON và crawler dữ liệu.

Thông điệp kết thúc khi thuyết trình:

> Sản phẩm không cố gắng thay thế người soạn thảo, mà đóng vai trò trợ lý giúp tạo bản nháp nhanh hơn, có nguồn kiểm chứng hơn và giảm lỗi thể thức trong quá trình chuẩn bị văn bản hành chính.
