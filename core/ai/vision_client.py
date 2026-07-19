import base64
from core.ai.openai_client import BaseOpenAIClient
from shared.logger import get_logger

logger = get_logger(__name__)


class VisionClient(BaseOpenAIClient):
    """Handles all image + vision prompts."""

    def _call_vision(
        self,
        image_bytes: bytes,
        prompt: str,
        content_type: str = "image/png"
    ) -> dict:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{content_type};base64,{base64_image}"}
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        return self._call(messages, label="GPT-4o Vision")

    def analyze_avatar(self, image_bytes: bytes, content_type: str = "image/png") -> dict:
        from core.prompts.avatar_prompts import AVATAR_ANALYSIS_PROMPT
        logger.info("Starting avatar analysis")
        return self._call_vision(image_bytes, AVATAR_ANALYSIS_PROMPT, content_type)

    def classify_clothing(self, image_bytes: bytes, content_type: str = "image/png") -> dict:
        from core.prompts.wardrobe_prompts import WARDROBE_CLASSIFICATION_PROMPT
        logger.info("Starting clothing classification")
        return self._call_vision(image_bytes, WARDROBE_CLASSIFICATION_PROMPT, content_type)


vision_client = VisionClient()