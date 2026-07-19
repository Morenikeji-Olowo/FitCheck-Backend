from shared.logger import get_logger
from shared.exceptions import FitCheckException

logger = get_logger(__name__)

SINGLE_ITEM_CATEGORIES = {"top", "bottom", "shoes", "dress", "outerwear"}
MIN_ITEMS = 2


def validate_outfit_composition(items: list[dict]) -> None:
    if len(items) < MIN_ITEMS:
        raise FitCheckException(
            "An outfit needs at least 2 items.",
            code="OUTFIT_TOO_SMALL", status_code=400
        )

    category_counts: dict[str, int] = {}
    for item in items:
        cat = item.get("category")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    duplicates = [
        cat for cat in SINGLE_ITEM_CATEGORIES
        if category_counts.get(cat, 0) > 1
    ]

    if duplicates:
        logger.warning(f"Outfit rejected — duplicate categories: {duplicates}")
        raise FitCheckException(
            f"An outfit can only have one item per category: {', '.join(duplicates)}.",
            code="INVALID_OUTFIT_COMPOSITION", status_code=400
        )

    has_dress = category_counts.get("dress", 0) > 0
    has_top = category_counts.get("top", 0) > 0
    has_bottom = category_counts.get("bottom", 0) > 0

    if not has_dress and not (has_top and has_bottom):
        logger.warning("Outfit rejected — missing top/bottom or dress")
        raise FitCheckException(
            "An outfit needs either a dress, or both a top and a bottom.",
            code="INVALID_OUTFIT_COMPOSITION", status_code=400
        )

    logger.info(f"Outfit composition valid — {len(items)} items")