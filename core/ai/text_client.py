from core.ai.openai_client import BaseOpenAIClient
from shared.logger import get_logger

logger = get_logger(__name__)


class TextClient(BaseOpenAIClient):
    """Handles all text-only prompts — outfit critique, planning, future chat."""

    def analyze_text(self, prompt: str) -> dict:
        messages = [{"role": "user", "content": prompt}]
        return self._call(messages, label="GPT-4o Text")


text_client = TextClient()