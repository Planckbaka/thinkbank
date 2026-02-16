#!/usr/bin/env python3
"""
Architecture validation for ThinkBank:
1) Check vLLM OpenAI endpoint connectivity.
2) Check embedding model device is CPU.
"""

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parent


def _ensure_local_hf_cache() -> None:
    """Use project-local HF cache to avoid root-owned global cache issues."""
    hf_home = Path(os.getenv("HF_HOME", PROJECT_ROOT / ".hf-cache"))
    hf_home.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(hf_home)
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(hf_home / "hub"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(hf_home / "transformers"))


def check_llm_models() -> bool:
    """Call the local vLLM OpenAI models endpoint."""
    url = "http://localhost:8000/v1/models"
    print(f"[LLM] GET {url}")

    request = Request(
        url,
        headers={
            "Authorization": "Bearer sk-local",
        },
    )

    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        model_ids = [item.get("id", "<unknown>") for item in payload.get("data", [])]
        print(f"[LLM] OK, discovered models: {model_ids}")
        return True
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        print(f"[LLM] FAILED: {exc}")
        return False


def _detect_embedding_device(embedder) -> str:
    """Best-effort runtime device extraction for multiple embedding wrappers."""
    model = getattr(embedder, "model", None)
    if model is None:
        return "unknown"

    client = getattr(model, "client", None)
    if client is not None:
        target_device = getattr(client, "_target_device", None)
        if target_device is not None:
            return str(target_device)

    target_device = getattr(model, "_target_device", None)
    if target_device is not None:
        return str(target_device)

    device = getattr(model, "device", None)
    if device is not None:
        return str(device)

    return "unknown"


def check_embedding_device() -> bool:
    """Load text embedding model and print target device."""
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root / "python-ai"))

    try:
        from core.embeddings import TextEmbeddingModel

        print("[Embedding] Loading BAAI/bge-m3 ...")
        embedder = TextEmbeddingModel(model_name="BAAI/bge-m3")
        embedder.load()

        if hasattr(embedder, "get_device"):
            device = str(embedder.get_device())
        else:
            device = _detect_embedding_device(embedder)

        print(f"[Embedding] device: {device}")
        return "cpu" in device.lower()
    except Exception as exc:
        print(f"[Embedding] FAILED: {exc}")
        return False


def main() -> int:
    _ensure_local_hf_cache()
    llm_ok = check_llm_models()
    embedding_ok = check_embedding_device()

    print("\nSummary:")
    print(f"- LLM endpoint check: {'PASS' if llm_ok else 'FAIL'}")
    print(f"- Embedding CPU check: {'PASS' if embedding_ok else 'FAIL'}")

    return 0 if (llm_ok and embedding_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
