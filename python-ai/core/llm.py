"""
ThinkBank AI Service - Remote LLM Client
Uses an OpenAI-compatible HTTP endpoint served by vLLM.
"""

import os
from typing import Iterator, List, Optional

from loguru import logger
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

try:
    from langchain_openai import ChatOpenAI
    LANGCHAIN_OPENAI_AVAILABLE = True
except ImportError:
    ChatOpenAI = None
    LANGCHAIN_OPENAI_AVAILABLE = False
    logger.warning("langchain-openai not available. Install with: pip install langchain-openai")


class LLMService:
    """
    LLM service backed by an OpenAI-compatible API endpoint.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.model_name = (
            model_name
            or os.getenv("LLM_MODEL")
            or os.getenv("VLLM_MODEL")
            or "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4"
        )
        # Default to localhost for host-run mode; docker-compose overrides this to llm-engine.
        self.api_url = api_url or os.getenv("LLM_API_URL", "http://127.0.0.1:8000/v1")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "sk-local")
        self.client = None
        self._loaded = False

    def load(self) -> None:
        """Initialize the remote LLM client."""
        if self._loaded:
            return

        if not LANGCHAIN_OPENAI_AVAILABLE:
            raise RuntimeError("langchain-openai is not available. Please install it first.")

        logger.info(f"Initializing remote LLM client: model={self.model_name}, url={self.api_url}")
        self.client = ChatOpenAI(
            model=self.model_name,
            base_url=self.api_url,
            api_key=self.api_key,
            temperature=0.7,
        )
        self._loaded = True
        logger.info("Remote LLM client initialized")

    @staticmethod
    def _to_text(content) -> str:
        """Normalize model output content into plain text."""
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            chunks: List[str] = []
            for item in content:
                if isinstance(item, str):
                    chunks.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        chunks.append(text)
            return "".join(chunks)

        return "" if content is None else str(content)

    def _bound_client(self, max_tokens: int, temperature: float, top_p: float):
        if not self._loaded:
            self.load()
        return self.client.bind(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """Generate text from a prompt."""
        client = self._bound_client(max_tokens=max_tokens, temperature=temperature, top_p=top_p)
        response = client.invoke([HumanMessage(content=prompt)])
        return self._to_text(response.content)

    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> Iterator[str]:
        """Stream generated text from a prompt."""
        client = self._bound_client(max_tokens=max_tokens, temperature=temperature, top_p=top_p)
        has_output = False

        for chunk in client.stream([HumanMessage(content=prompt)]):
            text = self._to_text(getattr(chunk, "content", ""))
            if text:
                has_output = True
                yield text

        if not has_output:
            text = self.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            if text:
                yield text

    def chat(
        self,
        query: str,
        history: List[dict],
        context: str = "",
        max_tokens: int = 512,
    ) -> str:
        """Generate a chat response with optional context."""
        messages = []

        if context:
            messages.append(
                SystemMessage(
                    content=(
                        "You are a helpful assistant with access to the following context:\n\n"
                        f"{context}"
                    )
                )
            )
        else:
            messages.append(SystemMessage(content="You are a helpful assistant."))

        for msg in history:
            role = str(msg.get("role", "user")).lower()
            content = self._to_text(msg.get("content", ""))
            if not content:
                continue

            if role in {"assistant", "ai"}:
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))

        messages.append(HumanMessage(content=query))
        client = self._bound_client(max_tokens=max_tokens, temperature=0.7, top_p=0.9)
        response = client.invoke(messages)
        return self._to_text(response.content)


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
    """Check if the remote LLM client dependencies are available."""
    return LANGCHAIN_OPENAI_AVAILABLE
