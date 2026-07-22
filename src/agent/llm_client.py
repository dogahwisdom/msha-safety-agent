"""LLM client configuration: OpenAI, Groq (free tier), or local Ollama."""

from __future__ import annotations

import os
import time
import urllib.error
import urllib.request
from typing import Any

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"
DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GROQ_BENCHMARK_DELAY_S = 2.5


def _ollama_reachable(base_url: str) -> bool:
    root = base_url.rstrip("/").removesuffix("/v1")
    try:
        with urllib.request.urlopen(f"{root}/api/tags", timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def llm_provider() -> str | None:
    """Return active provider: openai, groq, ollama, or None (offline tools)."""
    explicit = os.environ.get("LLM_PROVIDER", "auto").strip().lower()
    if explicit in {"offline", "none"}:
        return None
    if explicit == "openai":
        return "openai" if os.environ.get("OPENAI_API_KEY") else None
    if explicit == "groq":
        if not os.environ.get("GROQ_API_KEY"):
            raise RuntimeError(
                "LLM_PROVIDER=groq but GROQ_API_KEY is not set. "
                "Add it to .env (see .env.example) or use LLM_PROVIDER=offline."
            )
        return "groq"
    if explicit == "ollama":
        return "ollama" if _ollama_reachable(_ollama_base_url()) else None
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    if os.environ.get("OLLAMA_MODEL") or _ollama_reachable(_ollama_base_url()):
        return "ollama"
    return None


def _ollama_base_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).rstrip("/")


def _groq_base_url() -> str:
    return os.environ.get("GROQ_BASE_URL", DEFAULT_GROQ_BASE_URL).rstrip("/")


def get_llm_client() -> Any:
    """Return an OpenAI SDK client for the configured provider."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError("Install openai package: pip install openai") from exc

    provider = llm_provider()
    if provider == "openai":
        return OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    if provider == "groq":
        return OpenAI(api_key=os.environ["GROQ_API_KEY"], base_url=_groq_base_url())
    if provider == "ollama":
        return OpenAI(base_url=_ollama_base_url(), api_key=os.environ.get("OLLAMA_API_KEY", "ollama"))
    raise RuntimeError(
        "No LLM configured. Options: GROQ_API_KEY (free at console.groq.com), "
        "OPENAI_API_KEY, or local Ollama (OLLAMA_MODEL=qwen2.5:7b). "
        "Set LLM_PROVIDER=offline to force offline benchmark runs. See .env.example."
    )


def get_llm_model() -> str:
    provider = llm_provider()
    if provider == "openai":
        return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    if provider == "groq":
        return os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)
    if provider == "ollama":
        return os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    raise RuntimeError("No LLM provider configured.")


def get_llm_client_and_model() -> tuple[Any, str]:
    return get_llm_client(), get_llm_model()


def groq_benchmark_delay_s() -> float:
    return float(os.environ.get("GROQ_BENCHMARK_DELAY_S", DEFAULT_GROQ_BENCHMARK_DELAY_S))


def chat_completion_with_retry(client: Any, **kwargs: Any) -> Any:
    """Call chat.completions.create with backoff on rate limits (Groq free tier)."""
    try:
        from openai import APIStatusError, RateLimitError
    except ImportError as exc:
        raise ImportError("Install openai package: pip install openai") from exc

    max_retries = int(os.environ.get("LLM_MAX_RETRIES", "12"))
    delay_s = float(os.environ.get("LLM_RETRY_DELAY_S", "5"))
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**kwargs)
            if llm_provider() == "groq":
                time.sleep(groq_benchmark_delay_s())
            return response
        except RateLimitError as exc:
            last_exc = exc
        except APIStatusError as exc:
            if exc.status_code == 429:
                last_exc = exc
            else:
                raise
        if attempt + 1 >= max_retries:
            break
        time.sleep(delay_s)
        delay_s = min(delay_s * 1.5, 120.0)
    assert last_exc is not None
    raise last_exc


# Backward-compatible alias used by RAG baseline.
_get_openai_client = get_llm_client
