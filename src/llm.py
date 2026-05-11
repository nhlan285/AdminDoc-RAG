from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from src.generator import build_draft
from src.retriever import SearchResult


DEFAULT_OPENAI_MODEL = "gpt-5.5"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"


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
        gemini_timeout_seconds=_as_float(
            get_value("GEMINI_TIMEOUT_SECONDS", "30"),
            default=30.0,
        ),
        gemini_max_output_tokens=_as_int(
            get_value("GEMINI_MAX_OUTPUT_TOKENS", "1800"),
            default=1800,
        ),
        openai_api_key=get_value("OPENAI_API_KEY").strip(),
        openai_model=get_value("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip(),
        openai_timeout_seconds=_as_float(
            get_value("OPENAI_TIMEOUT_SECONDS", "30"),
            default=30.0,
        ),
        openai_max_output_tokens=_as_int(
            get_value("OPENAI_MAX_OUTPUT_TOKENS", "1800"),
            default=1800,
        ),
    )


def generate_draft(
    *,
    request: str,
    doc_type: str,
    search_results: list[SearchResult],
    config: LLMConfig,
) -> DraftResult:
    if config.provider == "mock":
        return _mock_result(request, doc_type, search_results)

    if config.provider == "gemini":
        return _generate_with_provider(
            provider="gemini",
            request=request,
            doc_type=doc_type,
            search_results=search_results,
            config=config,
        )

    if config.provider == "openai":
        return _generate_with_provider(
            provider="openai",
            request=request,
            doc_type=doc_type,
            search_results=search_results,
            config=config,
        )

    fallback = build_draft(request, doc_type, search_results)
    return DraftResult(
        text=fallback,
        provider=config.provider or "unknown",
        model=None,
        used_llm=False,
        fallback_used=True,
        error=f"Nhà cung cấp LLM không được hỗ trợ: {config.provider}",
    )


def _generate_with_provider(
    *,
    provider: str,
    request: str,
    doc_type: str,
    search_results: list[SearchResult],
    config: LLMConfig,
) -> DraftResult:
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
        return DraftResult(
            text=fallback,
            provider=provider,
            model=None,
            used_llm=False,
            fallback_used=True,
            error=f"Nhà cung cấp LLM không được hỗ trợ: {provider}",
        )

    if not search_results:
        fallback = build_draft(request, doc_type, search_results)
        return DraftResult(
            text=fallback,
            provider=provider,
            model=model,
            used_llm=False,
            fallback_used=True,
            error="Không gọi LLM vì chưa có nguồn truy xuất phù hợp.",
        )

    if not api_key:
        fallback = build_draft(request, doc_type, search_results)
        return DraftResult(
            text=fallback,
            provider=provider,
            model=model,
            used_llm=False,
            fallback_used=True,
            error=f"{key_name} chưa được cấu hình, đang dùng mock fallback.",
        )

    try:
        text = generate(
            request=request,
            doc_type=doc_type,
            search_results=search_results,
            config=config,
        )
    except Exception as error:  # The UI should keep the user's draftable state.
        fallback = build_draft(request, doc_type, search_results)
        return DraftResult(
            text=fallback,
            provider=provider,
            model=model,
            used_llm=False,
            fallback_used=True,
            error=f"Lỗi khi gọi {provider.upper()} API: {error}",
        )

    if not text:
        fallback = build_draft(request, doc_type, search_results)
        return DraftResult(
            text=fallback,
            provider=provider,
            model=model,
            used_llm=False,
            fallback_used=True,
            error=f"{provider.upper()} API trả về nội dung rỗng, đang dùng mock fallback.",
        )

    return DraftResult(
        text=text,
        provider=provider,
        model=model,
        used_llm=True,
        fallback_used=False,
    )


def describe_llm_status(config: LLMConfig) -> str:
    if config.provider == "mock":
        return "Chế độ mô phỏng"
    if config.provider == "gemini" and config.gemini_api_key:
        return f"Gemini sẵn sàng ({config.gemini_model})"
    if config.provider == "gemini":
        return "Gemini thiếu API key"
    if config.provider == "openai" and config.openai_api_key:
        return f"OpenAI sẵn sàng ({config.openai_model})"
    if config.provider == "openai":
        return "OpenAI thiếu API key"
    return f"Provider không hỗ trợ: {config.provider}"


def _generate_with_openai(
    *,
    request: str,
    doc_type: str,
    search_results: list[SearchResult],
    config: LLMConfig,
) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=config.openai_api_key,
        timeout=config.openai_timeout_seconds,
    )
    response = client.responses.create(
        model=config.openai_model,
        instructions=_build_instructions(),
        input=_build_input(request, doc_type, search_results),
        max_output_tokens=config.openai_max_output_tokens,
        store=False,
    )
    return response.output_text.strip()


def _generate_with_gemini(
    *,
    request: str,
    doc_type: str,
    search_results: list[SearchResult],
    config: LLMConfig,
) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.gemini_api_key)
    response = client.models.generate_content(
        model=config.gemini_model,
        contents=_build_input(request, doc_type, search_results),
        config=types.GenerateContentConfig(
            system_instruction=_build_instructions(),
            max_output_tokens=config.gemini_max_output_tokens,
            temperature=0.2, # Giữ Temperature thấp để AI không bị "ảo giác" văn phong
        ),
    )
    return (response.text or "").strip()


def _build_instructions() -> str:
    # SYSTEM PROMPT ĐƯỢC NÂNG CẤP ĐỂ ÉP AI VÀO KHUÔN KHỔ
    return """Bạn là một Chuyên viên Văn thư lưu trữ bậc cao có nhiệm vụ hoàn thiện VĂN BẢN HÀNH CHÍNH.
Tôi sẽ cung cấp cho bạn một KHUNG VĂN BẢN (TEMPLATE) chuẩn Nghị định 30.

NHIỆM VỤ CỦA BẠN:
1. Giữ nguyên 100% cấu trúc template, không được xóa Quốc hiệu, Tiêu ngữ hay các đề mục có sẵn.
2. Chỉ tập trung viết nội dung chi tiết để thay thế các phần dấu chấm "...." hoặc các phần nằm trong ngoặc vuông [...].
3. Sử dụng thông tin từ NGỮ CẢNH TRUY XUẤT để điền vào. Nếu thông tin nào không có trong nguồn, hãy để nguyên hoặc để trống dạng [...] để người dùng tự điền.
4. Tuyệt đối không thêm lời dẫn như "Dưới đây là bản nháp...". Trả về trực tiếp nội dung văn bản.
5. Giữ citation dạng [S1], [S2] ở các câu có dùng nguồn."""


def _build_input(
    request: str,
    doc_type: str,
    search_results: list[SearchResult],
) -> str:
    # Lấy Template chuẩn từ module generator
    skeleton = build_draft(request, doc_type, search_results)

    context_lines = []
    for index, result in enumerate(search_results[:3], start=1):
        document = result.document
        context_lines.append(
            "\n".join(
                [
                    f"[S{index}]",
                    f"id: {document.parent_id or document.id}",
                    f"loại: {document.doc_type}",
                    f"tiêu đề: {document.title}",
                    f"nguồn: {document.source}",
                    f"nội dung: {' '.join(document.content.split())}",
                ]
            )
        )

    # Đưa Template vào Prompt để AI có khung tham chiếu
    return f"""LOẠI VĂN BẢN CẦN SOẠN:
{doc_type}

YÊU CẦU NGƯỜI DÙNG:
{request}

NGỮ CẢNH TRUY XUẤT:
{chr(10).join(context_lines)}

KHUNG VĂN BẢN (TEMPLATE) CẦN HOÀN THIỆN:
{skeleton}

YÊU CẦU ĐẦU RA:
- Hãy điền thông tin vào các vị trí [...] hoặc .... trong KHUNG VĂN BẢN dựa trên Ngữ cảnh truy xuất và Yêu cầu người dùng.
- Trả về toàn bộ văn bản sau khi điền, tuyệt đối KHÔNG viết thêm lời chào hỏi, giải thích hay phân tích bên ngoài văn bản."""


def _mock_result(
    request: str,
    doc_type: str,
    search_results: list[SearchResult],
) -> DraftResult:
    # Ở chế độ Mock, nó sẽ trả thẳng Skeleton về giao diện
    return DraftResult(
        text=build_draft(request, doc_type, search_results),
        provider="mock",
        model=None,
        used_llm=False,
        fallback_used=False,
    )


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def _as_int(value: str, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: str, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default