from core.ai.text_client import text_client
from core.prompts.outfit_prompts import OUTFIT_ANALYSIS_PROMPT_TEMPLATE
from shared.logger import get_logger
from shared.exceptions import AIAnalysisError

logger = get_logger(__name__)

REQUIRED_FIELDS = ["summary", "highlights", "suggestions", "personalization_note"]


def analyze_outfit(
    items: list[dict],
    style_profile: dict,
    body_profile: dict,
    rule_scores: dict,
    occasion: str = "everyday"
) -> dict:
    """
    Sends outfit context to GPT-4o for personalized critique.
    Text-only reasoning — no image compositing needed since
    GPT reasons from item metadata + rule scores, not pixels.
    """
    try:
        logger.info("Starting outfit AI analysis")

        items_description = "\n".join(
            f"- {item.get('category', 'item')}: "
            f"{item.get('item_type', 'unknown type')}, "
            f"{item.get('dominant_color', 'unknown color')}, "
            f"{item.get('pattern', 'solid')} pattern, "
            f"{item.get('style', 'unknown')} style, "
            f"material: {item.get('material') or 'unknown'}"
            for item in items
        )

        prompt = OUTFIT_ANALYSIS_PROMPT_TEMPLATE.format(
            styles=", ".join(style_profile.get("styles", [])) or "not specified",
            preferred_colors=", ".join(style_profile.get("preferred_colors", [])) or "not specified",
            disliked_colors=", ".join(style_profile.get("disliked_colors", [])) or "none specified",
            body_shape=body_profile.get("body_shape", "not specified"),
            build=body_profile.get("build", "not specified"),
            height_category=body_profile.get("height_category", "not specified"),
            occasion=occasion,
            items_description=items_description,
            color_score=rule_scores.get("color_score", 0),
            style_score=rule_scores.get("style_score", 0),
            occasion_score=rule_scores.get("occasion_score", 0),
            season_score=rule_scores.get("season_score", 0),
        )

        raw = text_client.analyze_text(prompt)

        missing = [f for f in REQUIRED_FIELDS if f not in raw]
        if missing:
            logger.error(f"GPT-4o missing fields: {missing}")
            raise AIAnalysisError("AI analysis returned incomplete data.")

        confidence = raw.get("confidence")
        low_confidence = isinstance(confidence, (int, float)) and confidence < 0.6

        logger.info("Outfit AI analysis complete")
        return {
            "summary": raw.get("summary", ""),
            "highlights": raw.get("highlights", [])[:3],
            "suggestions": raw.get("suggestions", [])[:3],
            "personalization_note": raw.get("personalization_note", ""),
            "confidence": confidence,
            "low_confidence": low_confidence
        }

    except AIAnalysisError:
        raise
    except Exception:
        logger.exception("Outfit AI analysis failed")
        raise AIAnalysisError()