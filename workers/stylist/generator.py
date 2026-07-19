from shared.logger import get_logger
from workers.outfit.compatibility import calculate_compatibility
from workers.outfit.validator import validate_outfit_composition
from shared.exceptions import FitCheckException

logger = get_logger(__name__)

MAX_TOPS_PER_CATEGORY = 6   # pruning cap per category, not random sampling

MOOD_STYLE_PRIORITY = {
    "confident": ["streetwear", "formal"],
    "minimal": ["casual", "business"],
    "relaxed": ["casual"],
    "professional": ["business", "formal"],
}


def generate_outfits(
    wardrobe_items: list[dict],
    occasion: str = "everyday",
    mood: str | None = None,
    weather: dict | None = None,
    excluded_item_ids: list[str] | None = None,
    max_results: int = 3
) -> list[dict]:
    """
    Generates and ranks candidate outfits from a user's wardrobe.
    Pure logic — no AI call. Returns full item objects, not just IDs,
    so Flutter can render results without a follow-up fetch.
    """
    excluded = set(excluded_item_ids or [])
    logger.info(
        "Generating outfits — occasion=%s mood=%s items_available=%d",
        occasion, mood, len(wardrobe_items)
    )

    # 1. Filter by occasion + exclusions
    pool = [
        item for item in wardrobe_items
        if item["item_id"] not in excluded
        and (occasion in (item.get("occasions") or []) or occasion == "everyday")
    ]

    # 2. Filter by weather
    if weather:
        pool = _filter_by_weather(pool, weather)

    # 3. Filter/prioritize by mood — actually shapes the candidate pool now
    if mood:
        pool = _prioritize_by_mood(pool, mood)

    by_category = _group_by_category(pool)

    if not _has_viable_outfit(by_category):
        logger.warning("Not enough items across categories to generate an outfit")
        raise FitCheckException(
            "Not enough wardrobe items to generate an outfit for this occasion. "
            "Try adding more items or choosing a different occasion.",
            code="INSUFFICIENT_WARDROBE", status_code=400
        )

    # 4. Prune each category BEFORE combining — deterministic, not random
    by_category = _prune_categories(by_category)

    candidates = _build_candidates(by_category)

    if not candidates:
        raise FitCheckException(
            "Could not generate a valid outfit from your wardrobe for this occasion.",
            code="INSUFFICIENT_WARDROBE", status_code=400
        )

    scored = []
    for candidate_items in candidates:
        try:
            validate_outfit_composition(candidate_items)
        except FitCheckException:
            continue

        scores = calculate_compatibility(candidate_items)
        scored.append({
            "item_ids": [item["item_id"] for item in candidate_items],
            "items": candidate_items,  # full objects — Flutter renders directly
            "score": scores["overall_score"],
            "grade": scores["overall_grade"],
            "strengths": scores["strengths"],
            "warnings": scores["warnings"],
            "reason": _build_reason(scores, mood)
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top_results = scored[:max_results]

    logger.info(
        "Generated %d candidates, returning top %d — best score=%s",
        len(scored), len(top_results),
        top_results[0]["score"] if top_results else "none"
    )

    return top_results


def _group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in items:
        cat = item.get("category")
        grouped.setdefault(cat, []).append(item)
    return grouped


def _has_viable_outfit(by_category: dict[str, list[dict]]) -> bool:
    has_dress = bool(by_category.get("dress"))
    has_top_bottom = bool(by_category.get("top")) and bool(by_category.get("bottom"))
    return has_dress or has_top_bottom


def _prune_categories(by_category: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """
    Cap items per category deterministically — most recently added / 
    most favorited first, not random. Keeps candidate count sane 
    without discarding the "best" items by chance.
    """
    pruned = {}
    for cat, items in by_category.items():
        sorted_items = sorted(
            items,
            key=lambda i: (i.get("favorite", False), i.get("times_worn", 0)),
            reverse=True
        )
        pruned[cat] = sorted_items[:MAX_TOPS_PER_CATEGORY]
    return pruned


def _build_candidates(by_category: dict[str, list[dict]]) -> list[list[dict]]:
    from itertools import product
    candidates = []
    shoes = by_category.get("shoes", [None])

    if by_category.get("dress"):
        for dress, shoe in product(by_category["dress"], shoes):
            combo = [dress] + ([shoe] if shoe else [])
            candidates.append(combo)

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
    """
    Mood shapes the candidate pool itself, not just the explanation text.
    Prefer items matching mood-associated styles when enough exist;
    never filter down to nothing.
    """
    preferred_styles = MOOD_STYLE_PRIORITY.get(mood.lower())
    if not preferred_styles:
        return items

    matched = [item for item in items if item.get("style") in preferred_styles]
    return matched if len(matched) >= 4 else items  # fall back if too restrictive


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