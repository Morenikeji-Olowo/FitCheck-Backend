import openai
import json
import time
from core.config.settings import settings
from shared.logger import get_logger
from shared.exceptions import AIAnalysisError, OpenAIConnectionError

logger = get_logger(__name__)


class BaseOpenAIClient:
    """
    Shared low-level OpenAI request logic.
    vision_client and text_client both build on this.
    Handles retries, timing, JSON parsing, error mapping.
    """

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.MODEL_NAME
        self.max_retries = 3
        self.timeout = 60

    def _call(self, messages: list, label: str) -> dict:
        """
        Sends a chat completion request with retries.
        messages: full OpenAI-format message list (vision or text).
        label: used for logging only.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"{label} call — attempt {attempt}/{self.max_retries}")
                start_time = time.time()

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=1000,
                    timeout=self.timeout
                )

                elapsed = round(time.time() - start_time, 2)
                logger.info(f"{label} completed in {elapsed}s")

                result = response.choices[0].message.content.strip()
                result = result.replace("```json", "").replace("```", "").strip()

                return json.loads(result)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse {label} response: {e}")
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