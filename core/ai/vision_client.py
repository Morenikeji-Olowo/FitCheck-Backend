import openai
import base64
import json
import time
from core.config.settings import settings
from shared.logger import get_logger
from shared.exceptions import AIAnalysisError, OpenAIConnectionError

logger = get_logger(__name__)

class VisionClient:
    """
    Single wrapper around GPT-4o Vision.
    All workers use this — never import openai directly.
    """

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.MODEL_NAME
        self.max_retries = 3
        self.timeout = 60

    def _call_vision(
        self,
        image_bytes: bytes,
        prompt: str,
        content_type: str = "image/png"
    ) -> dict:
        """
        Internal method — calls GPT-4o Vision with retries.
        Workers call the higher level methods below, not this.
        """
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"GPT-4o Vision call — attempt {attempt}/{self.max_retries}")
                start_time = time.time()

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{content_type};base64,{base64_image}"
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    max_tokens=1000,
                    timeout=self.timeout
                )

                elapsed = round(time.time() - start_time, 2)
                logger.info(f"GPT-4o Vision completed in {elapsed}s")

                result = response.choices[0].message.content.strip()
                result = result.replace("```json", "").replace("```", "").strip()

                return json.loads(result)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT-4o response: {e}")
                raise AIAnalysisError()

            except openai.RateLimitError:
                wait = 2 ** attempt
                logger.warning(f"Rate limit hit — waiting {wait}s before retry")
                time.sleep(wait)

            except openai.APIConnectionError as e:
                logger.error(f"OpenAI connection failed on attempt {attempt}: {e}")
                if attempt == self.max_retries:
                    raise OpenAIConnectionError()
                time.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                if attempt == self.max_retries:
                    raise AIAnalysisError()
                time.sleep(1)

        raise AIAnalysisError("All retry attempts failed.")

    def analyze_avatar(
        self,
        image_bytes: bytes,
        content_type: str = "image/png"
    ) -> dict:
        """Analyze user photo — returns body profile data"""
        from core.prompts.avatar import AVATAR_ANALYSIS_PROMPT
        logger.info("Starting avatar analysis")
        return self._call_vision(image_bytes, AVATAR_ANALYSIS_PROMPT, content_type)

    def classify_clothing(
        self,
        image_bytes: bytes,
        content_type: str = "image/png"
    ) -> dict:
        """Classify clothing item — returns metadata"""
        from core.prompts.wardrobe import WARDROBE_CLASSIFICATION_PROMPT
        logger.info("Starting clothing classification")
        return self._call_vision(image_bytes, WARDROBE_CLASSIFICATION_PROMPT, content_type)

    def score_outfit(
        self,
        image_bytes: bytes,
        content_type: str = "image/png"
    ) -> dict:
        """Score outfit combination — returns confidence and explanation"""
        from core.prompts.outfit import OUTFIT_SCORING_PROMPT
        logger.info("Starting outfit scoring")
        return self._call_vision(image_bytes, OUTFIT_SCORING_PROMPT, content_type)

vision_client = VisionClient()