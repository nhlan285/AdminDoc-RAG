from __future__ import annotations
import os
import json
from dataclasses import dataclass
from pathlib import Path
from pydantic import BaseModel, Field

from src.generator import build_draft
from src.retriever import SearchResult

DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"

# === CẤU TRÚC ÉP BUỘC LLM PHẢI TRẢ VỀ ===
class StructuredDraft(BaseModel):
    du_lieu_boc_tach: dict[str, str] = Field(
        description="Từ điển bóc tách các thông tin từ yêu cầu người dùng để lấp vào chỗ trống."
    )
    van_ban_nhap_hoan_chinh: str = Field(
        description="Toàn bộ nội dung bản nháp hành chính đã được thay thế biến số vào các khoảng trống [...]."
    )

@dataclass(frozen=True)
class LLMConfig:
    provider: str
    gemini_api_key: str
    gemini_model: str
    gemini_timeout_seconds: float
    gemini_max_output_tokens: int
    openai_api_key: str
    openai_model: str
    openai_timeout_seconds: float
    openai_max_output_tokens: int

@dataclass(frozen=True)
class DraftResult:
    text: str
    provider: str
    model: str | None
    used_llm: bool
    fallback_used: bool
    error: str | None = None

def load_llm_config(project_root: Path) -> LLMConfig:
    dotenv_values = _read_dotenv(project_root / ".env")
    def get_value(name: str, default: str = "") -> str:
        return os.environ.get(name) or dotenv_values.get(name) or default
    return LLMConfig(
        provider=get_value("LLM_PROVIDER", "mock").strip().lower(),
        gemini_api_key=get_value("GEMINI_API_KEY").strip(),
        gemini_model=get_value("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip(),
        gemini_timeout_seconds=_as_float(get_value("GEMINI_TIMEOUT_SECONDS", "30"), default=30.0),
        gemini_max_output_tokens=_as_int(get_value("GEMINI_MAX_OUTPUT_TOKENS", "1800"), default=1800),
        openai_api_key=get_value("OPENAI_API_KEY").strip(),
        openai_model=get_value("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip(),
        openai_timeout_seconds=_as_float(get_value("OPENAI_TIMEOUT_SECONDS", "30"), default=30.0),
        openai_max_output_tokens=_as_int(get_value("OPENAI_MAX_OUTPUT_TOKENS", "1800"), default=1800),
    )

def generate_draft(*, request: str, doc_type: str, search_results: list[SearchResult], config: LLMConfig) -> DraftResult:
    if config.provider == "mock":
        return _mock_result(request, doc_type, search_results)
    if config.provider == "gemini":
        return _generate_with_provider(provider="gemini", request=request, doc_type=doc_type, search_results=search_results, config=config)
    if config.provider == "openai":
        return _generate_with_provider(provider="openai", request=request, doc_type=doc_type, search_results=search_results, config=config)
    
    fallback = build_draft(request, doc_type, search_results)
    return DraftResult(text=fallback, provider=config.provider or "unknown", model=None, used_llm=False, fallback_used=True, error=f"Provider không hỗ trợ: {config.provider}")

def _generate_with_provider(*, provider: str, request: str, doc_type: str, search_results: list[SearchResult], config: LLMConfig) -> DraftResult:
    if provider == "gemini":
        api_key = config.gemini_api_key
        model = config.gemini_model
        key_name = "GEMINI_API_KEY"
        generate = _generate_with_gemini
    elif provider == "openai":
        api_key = config.openai_api_key
        model = config.openai_model
        key_name = "OPENAI_API_KEY"
        generate = _generate_with_openai
    else:
        fallback = build_draft(request, doc_type, search_results)
        return DraftResult(text=fallback, provider=provider, model=None, used_llm=False, fallback_used=True, error="Lỗi provider")

    if not search_results:
        fallback = build_draft(request, doc_type, search_results)
        return DraftResult(text=fallback, provider=provider, model=model, used_llm=False, fallback_used=True, error="Không gọi LLM vì chưa có nguồn truy xuất.")

    if not api_key:
        fallback = build_draft(request, doc_type, search_results)
        return DraftResult(text=fallback, provider=provider, model=model, used_llm=False, fallback_used=True, error=f"Thiếu {key_name}.")

    try:
        text = generate(request=request, doc_type=doc_type, search_results=search_results, config=config)
    except Exception as error:
        fallback = build_draft(request, doc_type, search_results)
        return DraftResult(text=fallback, provider=provider, model=model, used_llm=False, fallback_used=True, error=f"Lỗi API: {error}")

    return DraftResult(text=text, provider=provider, model=model, used_llm=True, fallback_used=False)

def describe_llm_status(config: LLMConfig) -> str:
    if config.provider == "mock": return "Mock mode"
    if config.provider == "gemini" and config.gemini_api_key: return f"Gemini ready ({config.gemini_model})"
    if config.provider == "gemini": return "Gemini thiếu API key"
    if config.provider == "openai" and config.openai_api_key: return f"OpenAI ready ({config.openai_model})"
    if config.provider == "openai": return "OpenAI thiếu API key"
    return f"Provider không hỗ trợ: {config.provider}"

def _generate_with_openai(*, request: str, doc_type: str, search_results: list[SearchResult], config: LLMConfig) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=config.openai_api_key, timeout=config.openai_timeout_seconds)
    response = client.chat.completions.create(
        model=config.openai_model,
        messages=[
            {"role": "system", "content": _build_instructions()},
            {"role": "user", "content": _build_input(request, doc_type, search_results)}
        ],
        max_tokens=config.openai_max_output_tokens,
    )
    return response.choices[0].message.content.strip()

def _generate_with_gemini(*, request: str, doc_type: str, search_results: list[SearchResult], config: LLMConfig) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=config.gemini_api_key)
    
    response = client.models.generate_content(
        model=config.gemini_model,
        contents=_build_input(request, doc_type, search_results),
        config=types.GenerateContentConfig(
            system_instruction=_build_instructions(),
            max_output_tokens=config.gemini_max_output_tokens,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=StructuredDraft,
        ),
    )
    
    try:
        raw_text = response.text or "{}"
        parsed_json = json.loads(raw_text)
        final_draft = parsed_json.get("van_ban_nhap_hoan_chinh", "")
        return final_draft.strip()
    except Exception as e:
        return f"Lỗi trích xuất cấu trúc văn bản: {str(e)}\n\n{response.text}"

def _build_instructions() -> str:
    return """Bạn là chuyên viên hành chính chuyên nghiệp. Nhiệm vụ của bạn là soạn thảo văn bản.
Quy tắc:
1. Bóc tách thông tin từ Yêu cầu người dùng (Tên, thời gian, địa điểm, sự việc...) và lấp đầy CHÍNH XÁC vào các khoảng trống [...] trong khung văn bản truy xuất được.
2. Không để lại các cụm lười biếng. Gọt giũa văn phong nghiêm túc (VD: thay vì "Lý do: lý do bị ốm", hãy viết "Lý do: Ốm đau, cần đi bệnh viện điều trị").
3. Chỉ giữ lại ngoặc vuông [...] nếu thông tin đó thực sự KHÔNG có.
4. Giữ nguyên các marker trích dẫn nguồn dạng [S1], [S2].
5. Luôn giữ mục "Nguồn tham khảo" ở cuối."""

def _build_input(request: str, doc_type: str, search_results: list[SearchResult]) -> str:
    context_lines = []
    for index, result in enumerate(search_results[:3], start=1):
        document = result.document
        context_lines.append(
            "\n".join([
                f"[S{index}]",
                f"loại: {document.doc_type}",
                f"tiêu đề: {document.title}",
                f"nội dung (KHUNG VĂN BẢN): {' '.join(document.content.split())}"
            ])
        )
    return f"""LOẠI VĂN BẢN CẦN SOẠN: {doc_type}\n\nYÊU CẦU NGƯỜI DÙNG: {request}\n\nNGỮ CẢNH TRUY XUẤT:\n{chr(10).join(context_lines)}"""

def _mock_result(request: str, doc_type: str, search_results: list[SearchResult]) -> DraftResult:
    return DraftResult(text=build_draft(request, doc_type, search_results), provider="mock", model=None, used_llm=False, fallback_used=False)

def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists(): return {}
    values = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values

def _as_int(value: str, *, default: int) -> int:
    try: return int(value)
    except (TypeError, ValueError): return default

def _as_float(value: str, *, default: float) -> float:
    try: return float(value)
    except (TypeError, ValueError): return default