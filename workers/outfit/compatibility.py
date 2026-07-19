import colorsys
from shared.logger import get_logger
from core.config.settings import settings

logger = get_logger(__name__)

def hex_to_hsv(hex_color: str) -> tuple[float, float, float] | None:
    """Convert hex color to HSV. Returns None if invalid."""
    try:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return (h * 360, s, v)  # hue in degrees
    except Exception:
        return None


def color_pair_score(hex_a: str | None, hex_b: str | None) -> float:
    """
    Score how well two colors work together using HSV hue distance.
    Returns 0.0 - 1.0.
    """
    if not hex_a or not hex_b:
        return 0.7  # neutral score when data missing — don't punish

    hsv_a = hex_to_hsv(hex_a)
    hsv_b = hex_to_hsv(hex_b)

    if not hsv_a or not hsv_b:
        return 0.7

    h_a, s_a, v_a = hsv_a
    h_b, s_b, v_b = hsv_b

    # Low saturation = neutral (black/white/gray/beige) — always pairs well
    if s_a < 0.15 or s_b < 0.15:
        return 0.95

    hue_diff = abs(h_a - h_b)
    hue_diff = min(hue_diff, 360 - hue_diff)  # wrap around color wheel

    # Monochromatic / analogous (close hues) — harmonious
    if hue_diff <= 30:
        return 0.9
    # Complementary-ish (opposite hues) — bold but works
    if 150 <= hue_diff <= 210:
        return 0.8
    # Everything else — moderate
    if hue_diff <= 90:
        return 0.75
    return 0.6


def calculate_color_score(items: list[dict]) -> float:
    """Average pairwise color compatibility across all items."""
    hexes = [item.get("dominant_hex") for item in items if item.get("dominant_hex")]

    if len(hexes) < 2:
        return 0.85  # single item or missing data — assume fine

    scores = []
    for i in range(len(hexes)):
        for j in range(i + 1, len(hexes)):
            scores.append(color_pair_score(hexes[i], hexes[j]))

    return sum(scores) / len(scores) if scores else 0.85


def calculate_style_score(items: list[dict]) -> float:
    """How consistent are the styles across items?"""
    styles = [item.get("style") for item in items if item.get("style")]
    if not styles:
        return 0.7

    unique_styles = set(styles)
    if len(unique_styles) == 1:
        return 1.0
    if len(unique_styles) == 2:
        return 0.75
    return 0.5


def calculate_occasion_score(items: list[dict]) -> float:
    """Do items share at least one common occasion?"""
    occasion_sets = [set(item.get("occasions", [])) for item in items]
    occasion_sets = [s for s in occasion_sets if s]

    if not occasion_sets:
        return 0.7

    common = set.intersection(*occasion_sets)
    return 1.0 if common else 0.4


def calculate_season_score(items: list[dict]) -> float:
    """Do items share at least one common season?"""
    season_sets = [set(item.get("seasons", [])) for item in items]
    season_sets = [s for s in season_sets if s]

    if not season_sets:
        return 0.7

    common = set.intersection(*season_sets)
    return 1.0 if common else 0.4


def calculate_compatibility(items: list[dict]) -> dict:
    """
    Main entry point — instant, rule-based, no AI call.
    Takes list of closet_item dicts, returns weighted scores + reasons.
    """
    logger.info(f"Calculating compatibility for {len(items)} items")

    color_score = calculate_color_score(items)
    style_score = calculate_style_score(items)
    occasion_score = calculate_occasion_score(items)
    season_score = calculate_season_score(items)

    overall = (
        color_score * settings.COLOR_WEIGHT +
        style_score * settings.STYLE_WEIGHT +
        occasion_score * settings.OCCASION_WEIGHT +
        season_score * settings.SEASON_WEIGHT
    )

    strengths, warnings = _build_explanations(
        color_score, style_score, occasion_score, season_score
    )

    result = {
        "overall_score": round(overall * 100),
        "overall_grade": score_to_grade(round(overall * 100)),
        "color_score": round(color_score * 100),
        "style_score": round(style_score * 100),
        "occasion_score": round(occasion_score * 100),
        "season_score": round(season_score * 100),
        "strengths": strengths,
        "warnings": warnings,
    }

    logger.info(f"Compatibility result — overall={result['overall_score']}%")
    return result


def _build_explanations(
    color_score: float, style_score: float,
    occasion_score: float, season_score: float
) -> tuple[list[str], list[str]]:
    strengths = []
    warnings = []

    if color_score >= 0.85:
        strengths.append("Colors work well together.")
    elif color_score < 0.65:
        warnings.append("Some colors may not pair naturally.")

    if style_score >= 0.9:
        strengths.append("All items share a consistent style.")
    elif style_score < 0.6:
        warnings.append("Styles are quite mixed.")

    if occasion_score >= 0.9:
        strengths.append("All items suit the same occasions.")
    elif occasion_score < 0.5:
        warnings.append("Items may not suit the same occasion.")

    if season_score >= 0.9:
        strengths.append("All items suit the same season.")
    elif season_score < 0.5:
        warnings.append("Items may suit different seasons.")

    return strengths, warnings

def score_to_grade(score: int) -> str:
    """Convert a 0-100 score into a letter grade."""
    if score >= 95: return "A+"
    if score >= 90: return "A"
    if score >= 85: return "B+"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "Needs Work"