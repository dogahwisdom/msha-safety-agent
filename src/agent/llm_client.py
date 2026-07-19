"""LLM client configuration: OpenAI API or local Ollama (OpenAI-compatible)."""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"


def _ollama_reachable(base_url: str) -> bool:
    root = base_url.rstrip("/").removesuffix("/v1")
    try:
        with urllib.request.urlopen(f"{root}/api/tags", timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def llm_provider() -> str | None:
    """Return active provider name: openai, ollama, or None."""
    explicit = os.environ.get("LLM_PROVIDER", "auto").strip().lower()
    if explicit == "openai":
        return "openai" if os.environ.get("OPENAI_API_KEY") else None
    if explicit == "ollama":
        return "ollama" if _ollama_reachable(_ollama_base_url()) else None
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("OLLAMA_MODEL") or _ollama_reachable(_ollama_base_url()):
        return "ollama"
    return None


def _ollama_base_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).rstrip("/")


def get_llm_client() -> Any:
    """Return an OpenAI SDK client for the configured provider."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError("Install openai package: pip install openai") from exc

    provider = llm_provider()
    if provider == "openai":
        return OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    if provider == "ollama":
        return OpenAI(base_url=_ollama_base_url(), api_key=os.environ.get("OLLAMA_API_KEY", "ollama"))
    raise RuntimeError(
        "No LLM configured. Set OPENAI_API_KEY, or run Ollama locally and set "
        "OLLAMA_MODEL (e.g. qwen2.5:7b). See .env.example."
    )


def get_llm_model() -> str:
    provider = llm_provider()
    if provider == "openai":
        return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    if provider == "ollama":
        return os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    raise RuntimeError("No LLM provider configured.")


def get_llm_client_and_model() -> tuple[Any, str]:
    return get_llm_client(), get_llm_model()


# Backward-compatible alias used by RAG baseline.
_get_openai_client = get_llm_client
