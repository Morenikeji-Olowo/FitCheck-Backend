from shared.logger import get_logger
from shared.exceptions import FitCheckException
from core.storage.supabase_client import supabase
from workers.stylist.generator import generate_outfits

logger = get_logger(__name__)


async def run_stylist_pipeline(
    user_id: str,
    occasion: str = "everyday",
    mood: str | None = None,
    weather: dict | None = None,
    excluded_item_ids: list[str] | None = None,
    max_results: int = 3
) -> list[dict]:
    """
    Orchestrates the full recommendation flow:
    Fetch wardrobe → Generate + score candidates → Return top 3.

    This is the single entry point every Phase 6 feature calls into
    (Daily Suggestion, Dress Me For This, Weekly Planner) — none of
    them duplicate wardrobe fetching or generation logic.
    """
    logger.info(
        "Stylist pipeline started — user=%s occasion=%s mood=%s",
        user_id, occasion, mood
    )

    # 1. Fetch wardrobe — active items only, same fields the generator needs
    wardrobe_result = supabase.table("closet_items")\
        .select("item_id, category, item_type, dominant_color, dominant_hex, "
                "clean_image_url, pattern, style, occasions, seasons, "
                "favorite, times_worn")\
        .eq("user_id", user_id)\
        .eq("is_archived", False)\
        .execute()

    wardrobe_items = wardrobe_result.data or []

    if len(wardrobe_items) < 2:
        raise FitCheckException(
            "Your wardrobe needs at least a few items before FitCheck "
            "can suggest an outfit. Add some clothes first.",
            code="INSUFFICIENT_WARDROBE", status_code=400
        )

    # 2. Generate — pure logic, no AI, no further DB access
    results = generate_outfits(
        wardrobe_items=wardrobe_items,
        occasion=occasion,
        mood=mood,
        weather=weather,
        excluded_item_ids=excluded_item_ids,
        max_results=max_results
    )

    logger.info(
        "Stylist pipeline complete — user=%s candidates_returned=%d",
        user_id, len(results)
    )

    return results

