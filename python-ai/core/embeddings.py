"""
ThinkBank AI Service - Core Embedding Loaders
Optimized for RTX 4070 8GB VRAM - Embeddings run on CPU
"""

import torch
from sentence_transformers import SentenceTransformer
from typing import List, Optional, Union
from loguru import logger

from .config import settings


class TextEmbeddingModel:
    """
    BGE-M3 text embedding model.
    Runs on CPU to save GPU memory for LLM.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.text_embedding_model
        self.model = None
        self._loaded = False

    def load(self) -> None:
        """Load the model on CPU."""
        if self._loaded:
            return

        logger.info(f"Loading text embedding model: {self.model_name}")
        self.model = SentenceTransformer(
            self.model_name,
            device="cpu",
            trust_remote_code=True
        )
        self._loaded = True
        logger.info("Text embedding model loaded successfully")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not self._loaded:
            self.load()

        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.embed([text])[0]


class ImageEmbeddingModel:
    """
    SigLIP image embedding model.
    Runs on CPU to save GPU memory for LLM.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.image_embedding_model
        self.model = None
        self._loaded = False

    def load(self) -> None:
        """Load the model on CPU."""
        if self._loaded:
            return

        logger.info(f"Loading image embedding model: {self.model_name}")
        self.model = SentenceTransformer(
            self.model_name,
            device="cpu",
            trust_remote_code=True
        )
        self._loaded = True
        logger.info("Image embedding model loaded successfully")

    def embed(self, image_paths: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of images."""
        if not self._loaded:
            self.load()

        from PIL import Image
        images = [Image.open(path).convert("RGB") for path in image_paths]
        embeddings = self.model.encode(images, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_single(self, image_path: str) -> List[float]:
        """Generate embedding for a single image."""
        return self.embed([image_path])[0]

    def embed_pil(self, image: "Image.Image") -> List[float]:
        """Generate embedding for a PIL Image."""
        if not self._loaded:
            self.load()

        embeddings = self.model.encode([image.convert("RGB")], normalize_embeddings=True)
        return embeddings.tolist()[0]


# Global instances
_text_embedder: Optional[TextEmbeddingModel] = None
_image_embedder: Optional[ImageEmbeddingModel] = None


def get_text_embedder() -> TextEmbeddingModel:
    """Get or create the global text embedder."""
    global _text_embedder
    if _text_embedder is None:
        _text_embedder = TextEmbeddingModel()
        _text_embedder.load()
    return _text_embedder


def get_image_embedder() -> ImageEmbeddingModel:
    """Get or create the global image embedder."""
    global _image_embedder
    if _image_embedder is None:
        _image_embedder = ImageEmbeddingModel()
        _image_embedder.load()
    return _image_embedder
