from __future__ import annotations

import hashlib
import math
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


DEFAULT_EMBEDDING_PROVIDER = "local_hash"
DEFAULT_HASH_DIMENSIONS = 384
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_SENTENCE_TRANSFORMERS_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


@dataclass(frozen=True)
class EmbeddingConfig:
    provider: str
    dimensions: int
    openai_api_key: str
    openai_model: str
    sentence_transformers_model: str

    @property
    def signature(self) -> str:
        if self.provider == "openai":
            model = self.openai_model
        elif self.provider == "sentence_transformers":
            model = self.sentence_transformers_model
        else:
            model = "local-hash-v1"
        return f"{self.provider}:{model}:{self.dimensions}"


class EmbeddingProvider(Protocol):
    config: EmbeddingConfig

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class LocalHashEmbeddingProvider:
    def __init__(self, config: EmbeddingConfig) -> None:
        self.config = config

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_hash_embedding(text, self.config.dimensions) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class OpenAIEmbeddingProvider:
    def __init__(self, config: EmbeddingConfig) -> None:
        if not config.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings.")
        self.config = config

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        from openai import OpenAI

        client = OpenAI(api_key=self.config.openai_api_key)
        response = client.embeddings.create(
            model=self.config.openai_model,
            input=texts,
        )
        return [_normalize_vector(item.embedding) for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class SentenceTransformersEmbeddingProvider:
    def __init__(self, config: EmbeddingConfig) -> None:
        self.config = config
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(config.sentence_transformers_model)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [list(map(float, vector)) for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


def load_embedding_config(project_root: Path | None = None) -> EmbeddingConfig:
    root = project_root or Path.cwd()
    dotenv_values = _read_dotenv(root / ".env")

    def get_value(name: str, default: str = "") -> str:
        return os.environ.get(name) or dotenv_values.get(name) or default

    return EmbeddingConfig(
        provider=get_value("EMBEDDING_PROVIDER", DEFAULT_EMBEDDING_PROVIDER)
        .strip()
        .lower(),
        dimensions=_as_int(
            get_value("EMBEDDING_DIMENSIONS", str(DEFAULT_HASH_DIMENSIONS)),
            default=DEFAULT_HASH_DIMENSIONS,
        ),
        openai_api_key=get_value("OPENAI_API_KEY").strip(),
        openai_model=get_value(
            "OPENAI_EMBEDDING_MODEL",
            DEFAULT_OPENAI_EMBEDDING_MODEL,
        ).strip(),
        sentence_transformers_model=get_value(
            "SENTENCE_TRANSFORMERS_MODEL",
            DEFAULT_SENTENCE_TRANSFORMERS_MODEL,
        ).strip(),
    )


def build_embedding_provider(config: EmbeddingConfig) -> EmbeddingProvider:
    if config.provider in {"local", "local_hash", "hash"}:
        return LocalHashEmbeddingProvider(config)
    if config.provider == "openai":
        return OpenAIEmbeddingProvider(config)
    if config.provider in {"sentence_transformers", "sentence-transformers"}:
        return SentenceTransformersEmbeddingProvider(
            EmbeddingConfig(
                provider="sentence_transformers",
                dimensions=config.dimensions,
                openai_api_key=config.openai_api_key,
                openai_model=config.openai_model,
                sentence_transformers_model=config.sentence_transformers_model,
            )
        )
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {config.provider}")


def describe_embedding_config(config: EmbeddingConfig) -> str:
    if config.provider in {"local", "local_hash", "hash"}:
        return f"local hash ({config.dimensions}d)"
    if config.provider == "openai":
        return f"OpenAI {config.openai_model}"
    if config.provider in {"sentence_transformers", "sentence-transformers"}:
        return f"SentenceTransformers {config.sentence_transformers_model}"
    return config.provider


def _hash_embedding(text: str, dimensions: int) -> list[float]:
    dimensions = max(16, dimensions)
    vector = [0.0] * dimensions
    for feature, weight in _semantic_features(text):
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        raw = int.from_bytes(digest, "little", signed=False)
        index = raw % dimensions
        sign = 1.0 if (raw >> 63) == 0 else -1.0
        vector[index] += sign * weight
    return _normalize_vector(vector)


def _semantic_features(text: str) -> list[tuple[str, float]]:
    normalized = _normalize_text(text)
    tokens = re.findall(r"\w+", normalized, flags=re.UNICODE)
    tokens = [token for token in tokens if len(token) > 1 and not token.isnumeric()]

    features: list[tuple[str, float]] = []
    features.extend((f"w:{token}", 1.0) for token in tokens)
    features.extend(
        (f"b:{tokens[index]}_{tokens[index + 1]}", 1.35)
        for index in range(len(tokens) - 1)
    )

    compact = " ".join(tokens)
    for phrase, concepts in _CONCEPT_HINTS.items():
        if phrase in compact:
            features.extend((f"concept:{concept}", 2.0) for concept in concepts)

    return features or [("empty", 1.0)]


_CONCEPT_HINTS = {
    "xin nghi": ["leave_request", "personnel"],
    "nghi phep": ["leave_request", "personnel"],
    "bi om": ["leave_request", "health"],
    "om dau": ["leave_request", "health"],
    "cong van": ["official_letter"],
    "de nghi": ["request", "official_letter"],
    "cung cap": ["request", "data_collection"],
    "so lieu": ["data_collection", "reporting"],
    "chuyen doi so": ["digital_admin"],
    "ky so": ["digital_admin", "electronic_document"],
    "van ban dien tu": ["digital_admin", "electronic_document"],
    "thong bao": ["announcement"],
    "tap huan": ["training", "announcement"],
    "an toan thong tin": ["security", "training"],
    "to trinh": ["proposal"],
    "phe duyet": ["approval", "proposal"],
    "quyet dinh": ["decision"],
    "thanh lap": ["decision", "organization"],
    "giay moi": ["invitation"],
    "hoi nghi": ["meeting", "invitation"],
    "bien ban": ["minutes", "meeting"],
    "ke hoach": ["planning"],
    "du an": ["project"],
}


def _normalize_text(text: str) -> str:
    text = text.lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return unicodedata.normalize("NFC", text)


def _normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if not norm:
        return vector
    return [float(value) / norm for value in vector]


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
