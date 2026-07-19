from core.ai.vision_client import vision_client
from shared.logger import get_logger
from shared.exceptions import AIAnalysisError
from shared.models.clothing import ClothingClassification
from shared.models.enums import (
    Category, Pattern, Style, Season, Occasion
)

logger = get_logger(__name__)

MIN_CONFIDENCE = 0.5
PROMPT_VERSION = "wardrobe-v2"

DEFAULT_SEASONS = [Season.ALL]
DEFAULT_OCCASIONS = [Occasion.EVERYDAY]

HEX_PATTERN_LEN = 7  # e.g. "#1F3B73"


def classify_clothing(
    image_bytes: bytes,
    content_type: str = "image/png"
) -> ClothingClassification:
    """
    Sends clean clothing image to GPT-4o Vision.
    Returns validated ClothingClassification model.
    """
    try:
        logger.info(f"Starting clothing classification — prompt: {PROMPT_VERSION}")

        raw = vision_client.classify_clothing(image_bytes, content_type)

        required = ["category", "item_type", "dominant_color", "style"]
        missing = [f for f in required if not raw.get(f)]
        if missing:
            logger.error(f"GPT-4o missing fields: {missing}")
            raise AIAnalysisError(
                "AI classification returned incomplete data. Please try again."
            )

        confidence = float(raw.get("confidence", 0))
        if confidence < MIN_CONFIDENCE:
            logger.warning(f"Low confidence classification: {confidence}")
            raise AIAnalysisError(
                "The image couldn't be classified confidently. "
                "Please try a clearer photo."
            )

        dominant_color = raw.get("dominant_color", "unknown")
        dominant_hex = _validate_hex(raw.get("dominant_hex"))
        secondary_color = raw.get("secondary_color")
        secondary_hex = _validate_hex(raw.get("secondary_hex"))
        accent_color = raw.get("accent_color")
        accent_hex = _validate_hex(raw.get("accent_hex"))

        colors = list(dict.fromkeys(
            c for c in [dominant_color, secondary_color, accent_color] if c
        ))

        classification = ClothingClassification(
            category=_parse_enum(Category, raw.get("category"), Category.TOP),
            item_type=raw.get("item_type", raw.get("type", "unknown")),
            colors=colors,
            dominant_color=dominant_color,
            dominant_hex=dominant_hex,
            secondary_color=secondary_color,
            secondary_hex=secondary_hex,
            accent_color=accent_color,
            accent_hex=accent_hex,
            pattern=_parse_enum(Pattern, raw.get("pattern"), Pattern.SOLID),
            style=_parse_enum(Style, raw.get("style"), Style.CASUAL),
            seasons=_parse_enum_list(Season, raw.get("season", []), DEFAULT_SEASONS),
            occasions=_parse_enum_list(Occasion, raw.get("occasion", []), DEFAULT_OCCASIONS),
            brand=raw.get("brand") if raw.get("brand") != "unknown" else None,
            pairs_well_with=raw.get("pairs_well_with", []),
            material=raw.get("material"),
            classification_confidence=confidence
        )

        logger.info(
            f"Classification complete — {classification.category} / "
            f"{classification.style} / hex={dominant_hex} / confidence: {confidence}"
        )
        return classification

    except AIAnalysisError:
        raise
    except Exception as e:
        logger.error(f"Clothing classification failed: {e}")
        raise AIAnalysisError()


def _validate_hex(value) -> str | None:
    """Validate GPT returned a real hex code, otherwise return None."""
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if not value.startswith("#") or len(value) != HEX_PATTERN_LEN:
        logger.warning(f"Invalid hex value from GPT: '{value}' — discarding")
        return None
    try:
        int(value[1:], 16)
        return value.upper()
    except ValueError:
        logger.warning(f"Invalid hex value from GPT: '{value}' — discarding")
        return None


def _parse_enum(enum_class, value, default):
    try:
        return enum_class(str(value).lower())
    except (ValueError, KeyError):
        logger.warning(
            f"Unknown {enum_class.__name__} value: '{value}' — defaulting to {default}"
        )
        return default


def _parse_enum_list(enum_class, values: list, default: list) -> list:
    if not values:
        return default
    result = []
    for v in values:
        try:
            result.append(enum_class(str(v).lower()))
        except (ValueError, KeyError):
            logger.warning(f"Skipping unknown {enum_class.__name__} value: '{v}'")
    return result if result else default