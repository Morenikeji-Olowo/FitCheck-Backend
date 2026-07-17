from core.ai.vision_client import vision_client
from shared.logger import get_logger
from shared.exceptions import AIAnalysisError
from shared.models.clothing import ClothingClassification
from shared.models.enums import (
    Category, Pattern, Style, Season, Occasion
)

logger = get_logger(__name__)

MIN_CONFIDENCE = 0.5
PROMPT_VERSION = "wardrobe-v1"

DEFAULT_SEASONS = [Season.ALL]
DEFAULT_OCCASIONS = [Occasion.EVERYDAY]


def classify_clothing(
    image_bytes: bytes,
    content_type: str = "image/png"
) -> ClothingClassification:
    """
    Sends clean clothing image to GPT-4o Vision.
    Returns validated ClothingClassification model.
    Never returns raw dicts — worker gets a proper object.
    """
    try:
        logger.info(f"Starting clothing classification — prompt: {PROMPT_VERSION}")

        raw = vision_client.classify_clothing(image_bytes, content_type)

        # Validate required fields
        required = ["category", "colors", "style"]
        missing = [f for f in required if not raw.get(f)]
        if missing:
            logger.error(f"GPT-4o missing fields: {missing}")
            raise AIAnalysisError(
                "AI classification returned incomplete data. Please try again."
            )

        # Validate colors list is not empty
        colors = raw.get("colors", [])
        if not colors:
            logger.warning("GPT returned empty colors — using fallback")
            colors = ["unknown"]

        # Validate confidence
        confidence = float(raw.get("confidence", 0))
        if confidence < MIN_CONFIDENCE:
            logger.warning(f"Low confidence classification: {confidence}")
            raise AIAnalysisError(
                "The image couldn't be classified confidently. "
                "Please try a clearer photo."
            )

        classification = ClothingClassification(
            category=_parse_enum(Category, raw.get("category"), Category.TOP),
            item_type=raw.get("item_type", raw.get("type", "unknown")),
            colors=colors,
            dominant_color=colors[0],
            secondary_color=colors[1] if len(colors) > 1 else None,
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
            f"{classification.style} / confidence: {confidence}"
        )
        return classification

    except AIAnalysisError:
        raise
    except Exception as e:
        logger.error(f"Clothing classification failed: {e}")
        raise AIAnalysisError()


def _parse_enum(enum_class, value, default):
    """Parse external value into enum — return default if unknown."""
    try:
        return enum_class(str(value).lower())
    except (ValueError, KeyError):
        logger.warning(
            f"Unknown {enum_class.__name__} value: '{value}' — defaulting to {default}"
        )
        return default


def _parse_enum_list(enum_class, values: list, default: list) -> list:
    """Parse list of strings into enum values — skip unknowns."""
    result = []
    for v in values:
        try:
            result.append(enum_class(str(v).lower()))
        except (ValueError, KeyError):
            logger.warning(f"Skipping unknown {enum_class.__name__} value: '{v}'")
    return result if result else default