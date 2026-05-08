# Thư mục dữ liệu thô

Đặt các văn bản hành chính tải từ nguồn công khai vào thư mục này.

Định dạng khuyến nghị cho giai đoạn demo:

- `.txt`
- `.md`
- `.json`

Nếu tải được `.pdf` hoặc `.doc`, hãy giữ bản gốc ở đây, sau đó chuyển nội dung đã làm sạch sang `.txt` hoặc `.json` để app nạp dễ hơn.

## Quy tắc đặt tên

```text
nguon__so-ky-hieu__ten-ngan.ext
```

Ví dụ:

```text
congbao__30-2020-nd-cp__cong-tac-van-thu.pdf
vanban-chinhphu__7017-vpcp-hc__gui-file-dien-tu-ho-so.txt
moha__qd-bnv-demo__quyet-dinh-mau.txt
```

## Metadata cần ghi lại

Khi thêm tài liệu mới, cập nhật `data/raw/manifest.json` với:

- `id`
- `title`
- `doc_type`
- `source_url`
- `source_name`
- `file`
- `status`
- `notes`

Không đưa văn bản mật, dữ liệu nội bộ hoặc dữ liệu cá nhân nhạy cảm vào thư mục này.
