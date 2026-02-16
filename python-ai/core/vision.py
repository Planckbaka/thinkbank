"""
ThinkBank AI Service - Vision Captioning
SmolVLM for image understanding - runs on CPU/Offload
"""

from typing import Optional
from PIL import Image
from loguru import logger
import torch

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
        device = "cpu"
        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        self.model = AutoModelForVision2Seq.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype=torch.float32,
            device_map=device,
        )
        self.model.to(device)
        self._loaded = True
        logger.info("Vision model loaded successfully on CPU")

    def caption(
        self,
        image: Image.Image,
        prompt: str = "Describe this image with key objects and actions.",
        max_tokens: int = 256,
    ) -> str:
        """Generate caption for an image."""
        if not self._loaded:
            self.load()

        # SmolVLM-like processors expose chat templates; BLIP-style processors do not.
        if hasattr(self.processor, "apply_chat_template"):
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            try:
                inputs = self.processor(
                    images=[image],
                    text=self.processor.apply_chat_template(messages, add_generation_prompt=True),
                    return_tensors="pt",
                )
            except Exception as exc:
                logger.warning(f"Chat template unavailable for {self.model_name}, fallback to plain prompt: {exc}")
                inputs = self.processor(
                    images=image,
                    text=prompt,
                    return_tensors="pt",
                )
        else:
            inputs = self.processor(
                images=image,
                text=prompt,
                return_tensors="pt",
            )
        inputs = {k: v.to("cpu") if hasattr(v, "to") else v for k, v in inputs.items()}

        # Generate
        input_len = inputs["input_ids"].shape[-1]
        output_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
        )

        # Decode only the generated tokens (strip prompt tokens)
        generated_ids = output_ids[0][input_len:]
        caption = self.processor.decode(generated_ids, skip_special_tokens=True).strip()
        return caption

    def caption_path(self, image_path: str, prompt: str = "Describe this image with key objects and actions.") -> str:
        """Generate caption for an image from file path."""
        image = Image.open(image_path).convert("RGB")
        return self.caption(image, prompt)

    def classify(self, image: Image.Image) -> str:
        """
        Classify image into fixed categories:
        Landscape, Portrait, Document, Screenshot, Food, Animal, Other
        """
        if not self._loaded:
            self.load()

        categories = ["Landscape", "Portrait", "Document", "Screenshot", "Food", "Animal", "Graphic Design", "Other"]
        prompt = f"Classify this image into one of these categories: {', '.join(categories)}. Return only the category name."

        try:
            # Re-use caption logic but with classification prompt
            category = self.caption(image, prompt=prompt, max_tokens=16)
            
            # Simple cleanup
            for cat in categories:
                if cat.lower() in category.lower():
                    return cat
            return "Other"
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return "Other"


# Global instance
_vision_model: Optional[VisionCaptioningModel] = None


def get_vision_model() -> VisionCaptioningModel:
    """Get or create the global vision model."""
    global _vision_model
    if _vision_model is None:
        _vision_model = VisionCaptioningModel()
        _vision_model.load()
    return _vision_model
