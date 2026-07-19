from shared.logger import get_logger

logger = get_logger(__name__)


def analyze_wardrobe(wardrobe_items: list[dict]) -> dict:
    """
    Determines whether a wardrobe has enough variety to build
    at least one valid outfit, and what's missing if not.
    """
    categories = {item.get("category") for item in wardrobe_items}

    has_dress = "dress" in categories
    has_top = "top" in categories
    has_bottom = "bottom" in categories
    has_shoes = "shoes" in categories

    missing = []

    if has_dress:
        if not has_shoes:
            missing.append("shoes")
    else:
        if not has_top:
            missing.append("top")
        if not has_bottom:
            missing.append("bottom")
        if has_top and has_bottom and not has_shoes:
            missing.append("shoes")

    is_viable = len(missing) == 0

    logger.info(
        "Wardrobe analysis — categories=%s viable=%s missing=%s",
        categories, is_viable, missing
    )

    return {
        "is_viable": is_viable,
        "missing_categories": missing
    }