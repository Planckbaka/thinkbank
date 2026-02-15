"""
ThinkBank AI Service - LLM Loader
vLLM-based LLM loading for Qwen3-VL with GPU optimization
"""

import torch
from typing import List, Optional, Iterator, AsyncIterator
from loguru import logger

from .config import settings

# vLLM imports (will be available after pip install)
try:
    from vllm import LLM, SamplingParams
    from vllm.engine.async_llm_engine import AsyncLLMEngine
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False
    logger.warning("vLLM not available. Install with: pip install vllm")


class LLMService:
    """
    LLM Service using vLLM for efficient inference.
    Configured for RTX 4070 8GB VRAM with GPTQ-Int4 quantization.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        gpu_memory_utilization: Optional[float] = None,
    ):
        self.model_name = model_name or settings.vllm_model
        self.gpu_memory_utilization = gpu_memory_utilization or settings.gpu_memory_utilization
        self.max_model_len = settings.max_model_len
        self.engine = None
        self._loaded = False

    def load(self) -> None:
        """Load the LLM model with vLLM."""
        if self._loaded:
            return

        if not VLLM_AVAILABLE:
            raise RuntimeError("vLLM is not available. Please install it first.")

        logger.info(f"Loading LLM: {self.model_name}")
        logger.info(f"GPU Memory Utilization: {self.gpu_memory_utilization}")

        self.engine = LLM(
            model=self.model_name,
            gpu_memory_utilization=self.gpu_memory_utilization,
            max_model_len=self.max_model_len,
            trust_remote_code=True,
            dtype="auto",
            # GPTQ-specific settings
            quantization="gptq",
        )
        self._loaded = True
        logger.info("LLM loaded successfully")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """Generate text from a prompt."""
        if not self._loaded:
            self.load()

        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

        outputs = self.engine.generate([prompt], sampling_params)
        return outputs[0].outputs[0].text

    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> Iterator[str]:
        """Stream generated text from a prompt."""
        if not self._loaded:
            self.load()

        # Note: For true streaming, use AsyncLLMEngine
        # This is a simplified version
        result = self.generate(prompt, max_tokens, temperature, top_p)
        # Simulate streaming by yielding chunks
        chunk_size = 20
        for i in range(0, len(result), chunk_size):
            yield result[i:i + chunk_size]

    def chat(
        self,
        query: str,
        history: List[dict],
        context: str = "",
        max_tokens: int = 512,
    ) -> str:
        """Generate chat response with context."""
        # Build prompt with conversation history
        messages = []

        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(f"<|user|>\n{content}<|end|>")
            else:
                messages.append(f"<|assistant|\n{content}<|end|>")

        # Add context if provided
        if context:
            system_context = f"<|system|>\nYou are a helpful assistant with access to the following context:\n\n{context}<|end|>"
        else:
            system_context = "<|system|>\nYou are a helpful assistant.<|end|>"

        # Add current query
        messages.append(f"<|user|>\n{query}<|end|>")
        messages.append("<|assistant|")

        prompt = system_context + "\n" + "\n".join(messages)

        return self.generate(prompt, max_tokens=max_tokens)


# Global instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
        _llm_service.load()
    return _llm_service


def is_llm_available() -> bool:
    """Check if LLM is available (vLLM installed and GPU available)."""
    return VLLM_AVAILABLE and torch.cuda.is_available()
