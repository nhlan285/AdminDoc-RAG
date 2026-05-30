from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.preprocessing import clean_text, extract_text_from_binary


requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tải nguồn công khai, lưu bản gốc và JSON đã xử lý cho kho tri thức."
    )
    parser.add_argument("--manifest", default=str(RAW_DIR / "manifest.json"))
    parser.add_argument(
        "--output",
        default=str(PROCESSED_DIR / "crawled_public_docs.json"),
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    documents: list[dict[str, object]] = []

    for item in manifest.get("documents", []):
        try:
            documents.append(process_manifest_item(item))
            item["status"] = "downloaded"
        except Exception as error:
            item["status"] = "error"
            item["error"] = str(error)
            print(f"ERROR {item.get('id')}: {error}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"documents": documents}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved {len(documents)} documents to {output_path}")


def process_manifest_item(item: dict[str, object]) -> dict[str, object]:
    source_url = str(item["source_url"])
    title = str(item["title"])
    doc_type = str(item.get("doc_type") or "Công văn")
    source_name = str(item.get("source_name") or source_url)
    planned_file = str(item.get("file") or "")
    page_html = fetch_text(source_url)
    soup = BeautifulSoup(page_html, "html.parser")

    attachment = choose_attachment(source_url, soup)
    raw_file = ""
    text = ""

    if attachment and _is_extractable(attachment):
        try:
            raw_file = save_attachment(attachment, planned_file)
            text = clean_text(extract_text_from_binary(Path(raw_file).read_bytes(), raw_file))
        except Exception as error:
            print(f"WARN cannot download/extract attachment for {item.get('id')}: {error}")
            raw_file = ""
            text = ""

    if not text:
        text = extract_main_text(soup, title)
        raw_file = save_text_source(text, planned_file, item)

    if not text:
        raise ValueError("Không trích xuất được nội dung văn bản.")

    item["downloaded_file"] = str(Path(raw_file).relative_to(ROOT))
    item["content_length"] = len(text)
    return {
        "id": str(item["id"]).replace("-RAW", ""),
        "title": title,
        "doc_type": doc_type,
        "source": f"{source_name}: {source_url}",
        "source_url": source_url,
        "raw_file": str(Path(raw_file).relative_to(ROOT)),
        "content": text,
    }


def fetch_text(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=45,
        verify=False,
    )
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text


def choose_attachment(page_url: str, soup: BeautifulSoup) -> str:
    candidates: list[tuple[int, str]] = []
    for link in soup.find_all("a"):
        href = link.get("href") or ""
        text = link.get_text(" ", strip=True)
        url = urljoin(page_url, href)
        lower = unquote((href + " " + text).lower())
        score = 0
        if ".pdf" in lower or "format=pdf" in lower:
            score += 30
        if ".docx" in lower:
            score += 20
        if ".doc" in lower:
            score += 10
        if "download" in lower or "tai-ve" in lower or "tải" in lower:
            score += 5
        if score:
            candidates.append((score, url))
    if not candidates:
        return ""
    candidates.sort(key=lambda value: value[0], reverse=True)
    return candidates[0][1]


def save_attachment(url: str, planned_file: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=90,
        verify=False,
    )
    response.raise_for_status()
    filename = filename_from_url_or_header(url, response.headers.get("content-disposition", ""))
    if planned_file and Path(planned_file).suffix.lower() == Path(filename).suffix.lower():
        filename = planned_file
    validate_download(filename, response.content)
    target = RAW_DIR / sanitize_filename(filename)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(response.content)
    print(f"Downloaded {target.name} ({len(response.content)} bytes)")
    return str(target)


def save_text_source(text: str, planned_file: str, item: dict[str, object]) -> str:
    filename = planned_file if planned_file.endswith(".txt") else f"{item['id']}.txt"
    target = RAW_DIR / sanitize_filename(filename)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"Saved text {target.name} ({len(text)} chars)")
    return str(target)


def extract_main_text(soup: BeautifulSoup, title: str) -> str:
    for node in soup(["script", "style", "noscript", "svg", "form"]):
        node.decompose()

    lines = [
        clean_line(line)
        for line in soup.get_text("\n", strip=True).splitlines()
        if clean_line(line)
    ]
    start = find_start_line(lines, title)
    stop = find_stop_line(lines, start)
    return clean_text("\n".join(lines[start:stop]))


def find_start_line(lines: list[str], title: str) -> int:
    normalized_title = normalize(title)
    for index, line in enumerate(lines):
        normalized_line = normalize(line)
        if normalized_title and normalized_title[:45] in normalized_line:
            return index
        if any(
            marker in normalized_line
            for marker in [
                "cong van so",
                "nghi dinh so",
                "quyet dinh so",
                "van phong chinh phu",
            ]
        ):
            return index
    return 0


def find_stop_line(lines: list[str], start: int) -> int:
    stop_markers = [
        "cac van ban khac",
        "van ban moi",
        "ban quyen thuoc",
        "©",
        "copyright",
    ]
    for index in range(start + 1, len(lines)):
        normalized = normalize(lines[index])
        if any(marker in normalized for marker in stop_markers):
            return index
    return len(lines)


def filename_from_url_or_header(url: str, content_disposition: str) -> str:
    header_match = re.search(r"filename\*?=(?:UTF-8''|\"?)([^\";]+)", content_disposition)
    if header_match:
        return unquote(header_match.group(1).strip('"'))
    parsed = urlparse(url)
    query_name = re.search(r"[?&]file_name=([^&]+)", url)
    if query_name:
        return unquote(query_name.group(1).replace("+", " "))
    return Path(unquote(parsed.path)).name or "downloaded_source.pdf"


def validate_download(filename: str, content: bytes) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf" and not content.startswith(b"%PDF"):
        raise ValueError(f"Tải về không phải PDF hợp lệ: {filename}")
    if suffix == ".docx" and not content.startswith(b"PK"):
        raise ValueError(f"Tải về không phải DOCX hợp lệ: {filename}")


def sanitize_filename(filename: str) -> str:
    filename = filename.replace("/", "_").replace("\\", "_").strip()
    return re.sub(r"\s+", " ", filename)


def clean_line(line: str) -> str:
    return " ".join(line.strip().split())


def normalize(text: str) -> str:
    import unicodedata

    text = text.lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return unicodedata.normalize("NFC", text)


def _is_extractable(url: str) -> bool:
    lower = unquote(url.lower())
    return ".pdf" in lower or ".docx" in lower


if __name__ == "__main__":
    main()
