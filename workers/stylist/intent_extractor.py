from core.ai.text_client import text_client
from core.prompts.intent_prompts import INTENT_EXTRACTION_PROMPT_TEMPLATE
from shared.logger import get_logger
from shared.exceptions import AIAnalysisError
from shared.models.enums import OutfitOccasion, OutfitMood
from shared.models.intent import ExtractedIntent

logger = get_logger(__name__)

MIN_CONFIDENCE = 0.4


def extract_intent(user_text: str) -> ExtractedIntent:
    """
    Converts free text ("dinner with my girlfriend tonight") into
    structured occasion/mood the stylist pipeline already understands.
    GPT never sees wardrobe data — this is a pure text-to-intent step,
    isolated from the generator entirely.
    """
    if not user_text or not user_text.strip():
        raise AIAnalysisError("Please describe what you need an outfit for.")

    try:
        logger.info("Extracting intent from text: '%s'", user_text[:100])

        prompt = INTENT_EXTRACTION_PROMPT_TEMPLATE.format(user_text=user_text.strip())
        raw = text_client.analyze_text(prompt)

        if "occasion" not in raw:
            logger.error("GPT-4o missing occasion field")
            raise AIAnalysisError("Couldn't understand that request. Please try again.")

        try:
            confidence = float(raw.get("confidence", 0))
        except (TypeError, ValueError):
            logger.warning("Invalid confidence value from GPT")
            confidence = 0.0

        confidence = max(0.0, min(confidence, 1.0))
        if confidence < MIN_CONFIDENCE:
            logger.warning("Low confidence intent extraction: %.2f", confidence)

        occasion = _parse_occasion(raw.get("occasion"))
        mood = _parse_mood(raw.get("mood"))

        logger.info(
            "Intent extracted — occasion=%s mood=%s confidence=%.2f",
            occasion.value, mood.value if mood else None, confidence
        )

        return ExtractedIntent(
            occasion=occasion,
            mood=mood,
            confidence=confidence
        )

    except AIAnalysisError:
        raise
    except Exception:
        logger.exception("Intent extraction failed")
        raise AIAnalysisError("Couldn't understand that request. Please try again.")


def _parse_occasion(value) -> OutfitOccasion:
    try:
        return OutfitOccasion(str(value).lower())
    except (ValueError, KeyError):
        logger.warning("Unknown occasion '%s' — defaulting to everyday", value)
        return OutfitOccasion.EVERYDAY


def _parse_mood(value) -> OutfitMood | None:
    if not value or str(value).lower() == "null":
        return None
    try:
        return OutfitMood(str(value).lower())
    except (ValueError, KeyError):
        logger.warning("Unknown mood '%s' — ignoring", value)
        return None