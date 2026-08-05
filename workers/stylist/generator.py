import random
import hashlib
from datetime import datetime, UTC
from shared.logger import get_logger
from workers.outfit.compatibility import calculate_compatibility
from workers.outfit.validator import validate_outfit_composition
from shared.exceptions import FitCheckException
from core.config.settings import settings

logger = get_logger(__name__)

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
    max_results: int = 3,
    user_id: str | None = None
) -> list[dict]:
    excluded = set(excluded_item_ids or [])
    logger.info(
        "Generating outfits — occasion=%s mood=%s items_available=%d",
        occasion, mood, len(wardrobe_items)
    )

    # Create ONE seeded RNG at the start, shared across the whole pipeline
    seed_key = f"{user_id or 'anon'}-{datetime.now(UTC).date().isoformat()}"
    seed = int(hashlib.sha256(seed_key.encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)

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
    by_category = _prune_categories(by_category, rng)   # ← pass rng in
    candidates = _build_candidates(by_category)

    scored = []
    for candidate_items in candidates:
        try:
            validate_outfit_composition(candidate_items)
        except FitCheckException:
            continue

        scores = calculate_compatibility(candidate_items)
        compatibility_score = scores["overall_score"]
        rotation_score = _calculate_rotation_score(candidate_items)
        final_rank_score = compatibility_score + rotation_score

        scored.append({
            "item_ids": [item["item_id"] for item in candidate_items],
            "items": candidate_items,
            "score": compatibility_score,
            "grade": scores["overall_grade"],
            "strengths": scores["strengths"],
            "warnings": scores["warnings"],
            "reason": _build_reason(scores, mood),
            "_compatibility_score": compatibility_score,
            "_rotation_score": rotation_score,
            "_final_rank_score": final_rank_score,
        })

    if not scored:
        logger.warning("No valid outfit candidates survived scoring")
        raise FitCheckException(
            "We couldn't put together an outfit for this occasion right now. "
            "Try a different occasion or mood.",
            code="NO_VALID_COMBINATION", status_code=400
        )

    top_results = _select_from_elite_cluster(scored, max_results, rng)   # ← pass rng, not user_id

    for r in top_results:
        r.pop("_compatibility_score", None)
        r.pop("_rotation_score", None)
        r.pop("_final_rank_score", None)

    logger.info(
        "Generated %d candidates, returning top %d — best score=%s",
        len(scored), len(top_results), top_results[0]["score"]
    )

    return top_results


def _prune_categories(by_category: dict[str, list[dict]], rng: random.Random) -> dict[str, list[dict]]:
    pruned = {}
    for cat, items in by_category.items():
        shuffled = items[:]
        rng.shuffle(shuffled)   # ← seeded rng, not global random
        sorted_items = sorted(
            shuffled,
            key=lambda i: (
                not i.get("favorite", False),
                i.get("times_worn", 0)
            )
        )
        pruned[cat] = sorted_items[:MAX_ITEMS_PER_CATEGORY]
    return pruned


def _select_from_elite_cluster(
    scored: list[dict],
    max_results: int,
    rng: random.Random
) -> list[dict]:
    scored.sort(key=lambda x: x["_final_rank_score"], reverse=True)

    if not scored:
        return []

    top_score = scored[0]["_final_rank_score"]
    band = settings.ROTATION_SCORE_BAND

    elite_cluster = [c for c in scored if top_score - c["_final_rank_score"] <= band]
    remainder = [c for c in scored if c not in elite_cluster]

    rng.shuffle(elite_cluster)   # ← same rng instance as _prune_categories used

    ordered = elite_cluster + remainder
    return ordered[:max_results]

def _calculate_rotation_score(items: list[dict]) -> float:
    """
    A SEPARATE signal from compatibility — never mixed into the
    score shown to the user. Uses only confirmed-real fields
    (favorite, times_worn, last_worn), no new backend data required.
    """
    adjustment = 0.0

    for item in items:
        if item.get("favorite"):
            adjustment += settings.FAVORITE_BONUS

        times_worn = item.get("times_worn") or 0
        adjustment -= min(times_worn * settings.TIMES_WORN_WEIGHT, 10)

        last_worn = item.get("last_worn")
        if last_worn:
            try:
                worn_dt = datetime.fromisoformat(last_worn.replace("Z", "+00:00"))
                days_since = (datetime.now(UTC) - worn_dt).days
                if days_since < settings.RECENTLY_WORN_DAYS:
                    adjustment -= settings.ROTATION_PENALTY
            except (ValueError, TypeError):
                pass

    return adjustment


# def _select_from_elite_cluster(
#     scored: list[dict],
#     max_results: int,
#     user_id: str | None
# ) -> list[dict]:
#     """
#     Ranks by final_rank_score (compatibility + rotation combined),
#     then clusters every candidate within ROTATION_SCORE_BAND points
#     of the top result — randomizing ONLY within that elite cluster,
#     never selecting a meaningfully worse outfit. Randomness is seeded
#     per-user-per-day so repeated calls today return the same result.
#     """
#     scored.sort(key=lambda x: x["_final_rank_score"], reverse=True)

#     if not scored:
#         return []

#     top_score = scored[0]["_final_rank_score"]
#     band = settings.ROTATION_SCORE_BAND

#     elite_cluster = [c for c in scored if top_score - c["_final_rank_score"] <= band]
#     remainder = [c for c in scored if c not in elite_cluster]

#     seed_key = f"{user_id or 'anon'}-{datetime.now(UTC).date().isoformat()}"
#     seed = int(hashlib.sha256(seed_key.encode()).hexdigest(), 16) % (2**32)
#     rng = random.Random(seed)

#     rng.shuffle(elite_cluster)

#     ordered = elite_cluster + remainder
#     return ordered[:max_results]


def _group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in items:
        cat = item.get("category")
        grouped.setdefault(cat, []).append(item)
    return grouped


# def _prune_categories(by_category: dict[str, list[dict]]) -> dict[str, list[dict]]:
#     pruned = {}
#     for cat, items in by_category.items():
#         shuffled = items[:]
#         random.shuffle(shuffled)
#         sorted_items = sorted(
#             shuffled,
#             key=lambda i: (
#                 not i.get("favorite", False),
#                 i.get("times_worn", 0)
#             )
#         )
#         pruned[cat] = sorted_items[:MAX_ITEMS_PER_CATEGORY]
#     return pruned


def _build_candidates(by_category: dict[str, list[dict]]) -> list[list[dict]]:
    from itertools import product
    candidates = []
    shoes = by_category.get("shoes") or [None]

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
    preferred_styles = MOOD_STYLE_PRIORITY.get(mood.lower())
    if not preferred_styles:
        return items
    preferred = [item for item in items if item.get("style") in preferred_styles]
    others = [item for item in items if item.get("style") not in preferred_styles]
    return preferred + others


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