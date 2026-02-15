"""
ThinkBank AI Service - Vision Captioning
SmolVLM for image understanding - runs on CPU/Offload
"""

from typing import Optional, List
from PIL import Image
from loguru import logger

from .config import settings

try:
    from transformers import AutoModelForVision2Seq, AutoProcessor
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Install with: pip install transformers")


class VisionCaptioningModel:
    """
    SmolVLM for image captioning and understanding.
    Runs on CPU with optional GPU offload for memory efficiency.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.vision_model
        self.model = None
        self.processor = None
        self._loaded = False

    def load(self) -> None:
        """Load the vision model on CPU."""
        if self._loaded:
            return

        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers library is not available")

        logger.info(f"Loading vision model: {self.model_name}")

        # Load on CPU to save GPU memory for LLM
        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        self.model = AutoModelForVision2Seq.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype="auto",  # Will use float32 on CPU
            device_map="cpu",
        )
        self._loaded = True
        logger.info("Vision model loaded successfully on CPU")

    def caption(
        self,
        image: Image.Image,
        prompt: str = "Describe this image in detail.",
        max_tokens: int = 256,
    ) -> str:
        """Generate caption for an image."""
        if not self._loaded:
            self.load()

        # Prepare inputs
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        inputs = self.processor(
            images=[image],
            text=self.processor.apply_chat_template(messages, add_generation_prompt=True),
            return_tensors="pt",
        )

        # Generate
        output_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
        )

        # Decode
        caption = self.processor.decode(output_ids[0], skip_special_tokens=True)
        return caption

    def caption_path(self, image_path: str, prompt: str = "Describe this image in detail.") -> str:
        """Generate caption for an image from file path."""
        image = Image.open(image_path).convert("RGB")
        return self.caption(image, prompt)


# Global instance
_vision_model: Optional[VisionCaptioningModel] = None


def get_vision_model() -> VisionCaptioningModel:
    """Get or create the global vision model."""
    global _vision_model
    if _vision_model is None:
        _vision_model = VisionCaptioningModel()
        _vision_model.load()
    return _vision_model
