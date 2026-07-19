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
) -> dict:
    logger.info(
        "Stylist pipeline started — user=%s occasion=%s mood=%s",
        user_id, occasion, mood
    )

    wardrobe_result = supabase.table("closet_items")\
        .select("item_id, category, item_type, dominant_color, dominant_hex, "
                "clean_image_url, pattern, style, occasions, seasons, "
                "favorite, times_worn")\
        .eq("user_id", user_id)\
        .eq("is_archived", False)\
        .execute()

    wardrobe_items = wardrobe_result.data or []

    if len(wardrobe_items) < 2:
        return {
            "success": False,
            "outfits": [],
            "reason": "insufficient_wardrobe",
            "missing_categories": ["top", "bottom"]
        }

    result = generate_outfits(
        wardrobe_items=wardrobe_items,
        occasion=occasion,
        mood=mood,
        weather=weather,
        excluded_item_ids=excluded_item_ids,
        max_results=max_results
    )

    logger.info(
        "Stylist pipeline complete — user=%s success=%s outfits=%d",
        user_id, result["success"], len(result["outfits"])
    )

    return result