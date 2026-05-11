from __future__ import annotations

import hashlib
import json
import re
import io
import docx
from pypdf import PdfReader
from pathlib import Path
from typing import Any

from src.documents import Document

# --- CẤU HÌNH MẶC ĐỊNH ---
DEFAULT_CHUNK_SIZE_WORDS = 120
DEFAULT_CHUNK_OVERLAP_WORDS = 20

# 29 LOẠI VĂN BẢN CHUẨN NGHỊ ĐỊNH 30/2020/NĐ-CP
ND30_VALID_DOC_TYPES = {
    "Nghị quyết", "Quyết định", "Chỉ thị", "Quy chế", "Quy định", "Hướng dẫn",
    "Thông cáo", "Thông báo", "Báo cáo", "Biên bản", "Tờ trình",
    "Chương trình", "Kế hoạch", "Phương án", "Đề án", "Dự án",
    "Công văn", "Công điện", "Bản ghi nhớ", "Bản thỏa thuận", "Hợp đồng",
    "Giấy ủy quyền", "Giấy mời", "Giấy giới thiệu", "Giấy nghỉ phép",
    "Phiếu gửi", "Phiếu chuyển", "Phiếu báo", "Thư công"
}

def clean_text(text: str) -> str:
    """Làm sạch văn bản, chuẩn hóa khoảng trắng và dòng trống."""
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)

    cleaned_lines: list[str] = []
    previous_blank = False
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
            continue

        cleaned_lines.append(line)
        previous_blank = False

    return "\n".join(cleaned_lines).strip()

def normalize_doc_type(raw_type: str) -> str:
    """Nắn các doc_type tự do về đúng 29 loại chuẩn của Nghị định 30."""
    clean_type = str(raw_type).strip()
    
    # 1. Nếu đã khớp hoàn toàn với danh sách chuẩn
    if clean_type in ND30_VALID_DOC_TYPES:
        return clean_type
        
    # 2. Tìm kiếm thông minh theo từ khóa (Auto-mapping)
    lower_type = clean_type.lower()
    for valid_type in ND30_VALID_DOC_TYPES:
        if valid_type.lower() in lower_type:
            return valid_type
    
    # 3. Mặc định nếu không thuộc danh mục nào
    return "Công văn"

def extract_text_from_binary(file_bytes: bytes, filename: str) -> str:
    """Trích xuất nội dung văn bản từ định dạng nhị phân (Word, PDF)."""
    extension = filename.split('.')[-1].lower()
    
    try:
        if extension == 'docx':
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([para.text for para in doc.paragraphs])
        
        elif extension == 'pdf':
            reader = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text
        
        else:
            return file_bytes.decode("utf-8", errors="replace")
            
    except Exception as e:
        raise ValueError(f"Không thể đọc file {filename}: {str(e)}")

def parse_documents_from_text(
    *,
    filename: str,
    text: str,
    default_doc_type: str,
    source_kind: str = "system",
) -> list[Document]:
    """Chuyển đổi văn bản thô thành danh sách đối tượng Document."""
    
    # TRƯỜNG HỢP 1: File JSON (Chứa danh sách nhiều tài liệu)
    suffix = Path(filename).suffix.lower()
    if suffix == ".json":
        try:
            return _parse_json_documents(
                text=text,
                filename=filename,
                default_doc_type=default_doc_type,
                source_kind=source_kind,
            )
        except Exception:
            # Nếu JSON lỗi, coi như text thuần để xử lý ở bước dưới
            pass

    # TRƯỜNG HỢP 2: File đơn lẻ (Word, PDF, Txt)
    cleaned = clean_text(text)
    if not cleaned:
        return []

    title = _guess_title(filename, cleaned)
    
    # Khắc phục lỗi: Sử dụng default_doc_type trực tiếp cho file đơn lẻ
    doc_type = normalize_doc_type(default_doc_type)

    return [
        Document(
            id=_stable_id("DOC", filename, title, cleaned),
            title=title,
            doc_type=doc_type,
            source=filename,
            content=cleaned,
            source_kind=source_kind,
        )
    ]

def build_chunks(
    documents: list[Document],
    *,
    chunk_size_words: int = DEFAULT_CHUNK_SIZE_WORDS,
    overlap_words: int = DEFAULT_CHUNK_OVERLAP_WORDS,
) -> list[Document]:
    """Chia nhỏ tài liệu thành các đoạn (chunks) để AI truy xuất hiệu quả."""
    chunks: list[Document] = []
    for document in documents:
        cleaned_content = clean_text(document.content)
        words = cleaned_content.split()
        if not words:
            continue

        c_size = max(40, chunk_size_words)
        o_words = max(0, min(overlap_words, c_size // 2))

        start = 0
        doc_chunks_text: list[str] = []
        while start < len(words):
            end = min(start + c_size, len(words))
            doc_chunks_text.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start = end - o_words

        total = len(doc_chunks_text)
        for index, chunk_text in enumerate(doc_chunks_text, start=1):
            chunks.append(
                Document(
                    id=f"{document.id}-CH{index:03d}",
                    title=document.title,
                    doc_type=document.doc_type,
                    source=document.source,
                    content=chunk_text,
                    source_kind=document.source_kind,
                    parent_id=document.id,
                    chunk_index=index,
                    total_chunks=total,
                )
            )

    return chunks

def _parse_json_documents(
    *,
    text: str,
    filename: str,
    default_doc_type: str,
    source_kind: str,
) -> list[Document]:
    """Logic riêng để bóc tách cấu trúc file JSON."""
    raw_data = json.loads(text)
    raw_documents = raw_data.get("documents", []) if isinstance(raw_data, dict) else raw_data

    documents: list[Document] = []
    for index, raw_item in enumerate(raw_documents, start=1):
        if not isinstance(raw_item, dict):
            continue

        content = clean_text(str(raw_item.get("content") or raw_item.get("text") or ""))
        if not content:
            continue

        title = str(raw_item.get("title") or _guess_title(filename, content)).strip()
        source = str(raw_item.get("source") or filename).strip()
        
        # Ở đây dùng raw_item.get vì trong JSON có thể định nghĩa doc_type riêng cho từng mục
        doc_type = normalize_doc_type(raw_item.get("doc_type") or default_doc_type)
        
        document_id = str(raw_item.get("id") or "").strip()
        if not document_id:
            document_id = _stable_id("DOC", filename, title, str(index), content)

        documents.append(
            Document(
                id=document_id,
                title=title,
                doc_type=doc_type,
                source=source,
                content=content,
                source_kind=source_kind,
            )
        )

    return documents

def _guess_title(filename: str, content: str) -> str:
    """Đoán tiêu đề tài liệu từ dòng đầu tiên hoặc tên file."""
    for line in content.splitlines():
        line = line.strip(" #\t")
        if line:
            return line[:90]
    return Path(filename).stem.replace("_", " ").strip() or "Tài liệu chưa đặt tên"

def _stable_id(prefix: str, *parts: Any) -> str:
    """Tạo ID duy nhất dựa trên nội dung (Hashing)."""
    raw_value = "|".join(str(part) for part in parts)
    digest = hashlib.sha1(raw_value.encode("utf-8")).hexdigest()[:10].upper()
    return f"{prefix}-{digest}"