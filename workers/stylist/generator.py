from shared.logger import get_logger
from workers.outfit.compatibility import calculate_compatibility
from workers.outfit.validator import validate_outfit_composition
from shared.exceptions import FitCheckException

logger = get_logger(__name__)

SINGLE_ITEM_CATEGORIES = {"top", "bottom", "shoes", "dress", "outerwear"}
REQUIRED_FOR_OUTFIT = ["bottom", "shoes"]  # what a top-based outfit needs beyond a top

MOOD_STYLE_PRIORITY = {
    "confident": ["streetwear", "formal"],
    "minimal": ["casual", "business"],
    "relaxed": ["casual"],
    "professional": ["business", "formal"],
}

MAX_ITEMS_PER_CATEGORY = 6


def generate_outfits(
    wardrobe_items: list[dict],
    occasion: str = "everyday",
    mood: str | None = None,
    weather: dict | None = None,
    excluded_item_ids: list[str] | None = None,
    max_results: int = 3
) -> dict:
    """
    Generates and ranks candidate outfits from a user's wardrobe.
    Pure logic — no AI call. Never raises for "not enough items" —
    that's a normal state, not an error. Returns a structured result
    the caller can turn into whatever HTTP/UX response makes sense.

    Returns:
    {
        "success": bool,
        "outfits": [...],           # empty if insufficient wardrobe
        "reason": str | None,       # "insufficient_wardrobe" if applicable
        "missing_categories": [...] # what's needed to unlock generation
    }
    """
    excluded = set(excluded_item_ids or [])
    logger.info(
        "Generating outfits — occasion=%s mood=%s items_available=%d",
        occasion, mood, len(wardrobe_items)
    )

    pool = [
        item for item in wardrobe_items
        if item["item_id"] not in excluded
        and (occasion in (item.get("occasions") or []) or occasion == "everyday")
    ]

    if weather:
        pool = _filter_by_weather(pool, weather)

    if mood:
        pool = _prioritize_by_mood(pool, mood)

    by_category = _group_by_category(pool)

    missing = _find_missing_categories(by_category)
    if missing:
        logger.warning(
            "Insufficient wardrobe for generation — missing=%s", missing
        )
        return {
            "success": False,
            "outfits": [],
            "reason": "insufficient_wardrobe",
            "missing_categories": missing
        }

    by_category = _prune_categories(by_category)
    candidates = _build_candidates(by_category)

    scored = []
    for candidate_items in candidates:
        try:
            validate_outfit_composition(candidate_items)
        except FitCheckException:
            continue  # skip invalid combos, validator stays strict

        scores = calculate_compatibility(candidate_items)
        scored.append({
            "item_ids": [item["item_id"] for item in candidate_items],
            "items": candidate_items,
            "score": scores["overall_score"],
            "grade": scores["overall_grade"],
            "strengths": scores["strengths"],
            "warnings": scores["warnings"],
            "reason": _build_reason(scores, mood)
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top_results = scored[:max_results]

    if not top_results:
        # Composition possible in theory, but nothing survived validation
        # (e.g. bad data). Same clean non-error response.
        logger.warning("No valid outfit candidates survived scoring")
        return {
            "success": False,
            "outfits": [],
            "reason": "no_valid_combination",
            "missing_categories": []
        }

    logger.info(
        "Generated %d candidates, returning top %d — best score=%s",
        len(scored), len(top_results), top_results[0]["score"]
    )

    return {
        "success": True,
        "outfits": top_results,
        "reason": None,
        "missing_categories": []
    }


def _find_missing_categories(by_category: dict[str, list[dict]]) -> list[str]:
    """
    Determines what's missing to build ANY valid outfit.
    Validator requires MIN_ITEMS=2 unconditionally, so a dress alone
    is NOT enough — it needs a second item (shoes) to meet that bar.
    """
    has_dress = bool(by_category.get("dress"))
    has_top = bool(by_category.get("top"))
    has_bottom = bool(by_category.get("bottom"))
    has_shoes = bool(by_category.get("shoes"))

    if has_dress:
        return [] if has_shoes else ["shoes"]

    missing = []
    if not has_top:
        missing.append("top")
    if not has_bottom:
        missing.append("bottom")

    if not missing and not has_shoes:
        missing.append("shoes")

    return missing

def _group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in items:
        cat = item.get("category")
        grouped.setdefault(cat, []).append(item)
    return grouped


def _prune_categories(by_category: dict[str, list[dict]]) -> dict[str, list[dict]]:
    pruned = {}
    for cat, items in by_category.items():
        sorted_items = sorted(
            items,
            key=lambda i: (i.get("favorite", False), i.get("times_worn", 0)),
            reverse=True
        )
        pruned[cat] = sorted_items[:MAX_ITEMS_PER_CATEGORY]
    return pruned


def _build_candidates(by_category: dict[str, list[dict]]) -> list[list[dict]]:
    from itertools import product
    candidates = []
    shoes = by_category.get("shoes") or [None]

    if by_category.get("dress"):
        for dress, shoe in product(by_category["dress"], shoes):
            combo = [dress] + ([shoe] if shoe else [])
            candidates.append(combo)  # no length filter — validator handles it

    if by_category.get("top") and by_category.get("bottom"):
        for top, bottom, shoe in product(
            by_category["top"], by_category["bottom"], shoes
        ):
            combo = [top, bottom] + ([shoe] if shoe else [])
            candidates.append(combo)

    return candidates

def _filter_by_weather(items: list[dict], weather: dict) -> list[dict]:
    temp = weather.get("temp_celsius")
    if temp is None:
        return items
    if temp >= 25:
        target_seasons = {"summer", "spring"}
    elif temp <= 12:
        target_seasons = {"winter", "fall"}
    else:
        target_seasons = {"spring", "fall", "summer", "winter"}
    filtered = [
        item for item in items
        if not item.get("seasons") or set(item["seasons"]) & target_seasons
    ]
    return filtered if filtered else items


def _prioritize_by_mood(items: list[dict], mood: str) -> list[dict]:
    preferred_styles = MOOD_STYLE_PRIORITY.get(mood.lower())
    if not preferred_styles:
        return items
    matched = [item for item in items if item.get("style") in preferred_styles]
    return matched if len(matched) >= 4 else items


def _build_reason(scores: dict, mood: str | None) -> str:
    parts = []
    if scores["color_score"] >= 85:
        parts.append("strong color harmony")
    if scores["style_score"] >= 85:
        parts.append("consistent style")
    if scores["occasion_score"] >= 85:
        parts.append("great fit for the occasion")
    if mood:
        parts.append(f"suits a {mood} mood")
    if not parts:
        return "A balanced option from your wardrobe."
    return "Matches your wardrobe with " + ", ".join(parts) + "."