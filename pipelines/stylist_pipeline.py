from shared.logger import get_logger
from shared.exceptions import FitCheckException
from core.storage.supabase_client import supabase
from core.weather.client import weather_client
from workers.stylist.generator import generate_outfits
from workers.stylist.wardrobe_validator import analyze_wardrobe

logger = get_logger(__name__)


async def run_stylist_pipeline(
    user_id: str,
    occasion: str = "everyday",
    mood: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    excluded_item_ids: list[str] | None = None,
    max_results: int = 3
) -> list[dict]:
    """
    Orchestrates the full recommendation flow:
    Weather → Wardrobe fetch → Wardrobe validation → 
    Generator → Compatibility scoring → Top results.

    Business logic only — returns data on success, raises
    FitCheckException on failure. API layer decides HTTP response.
    """
    logger.info(
        "Stylist pipeline started — user=%s occasion=%s mood=%s",
        user_id, occasion, mood
    )

    weather = await weather_client.get_weather(latitude, longitude)

    wardrobe_result = supabase.table("closet_items")\
        .select("item_id, category, item_type, dominant_color, dominant_hex, "
                "clean_image_url, pattern, style, occasions, seasons, "
                "favorite, times_worn")\
        .eq("user_id", user_id)\
        .eq("is_archived", False)\
        .execute()

    wardrobe_items = wardrobe_result.data or []

    analysis = analyze_wardrobe(wardrobe_items)
    if not analysis["is_viable"]:
        missing = analysis["missing_categories"]
        message = (
            f"Add {' and '.join(missing)} to your wardrobe to unlock "
            f"outfit suggestions." if missing
            else "Add a few more items to unlock outfit suggestions."
        )
        logger.warning("Wardrobe not viable — missing=%s", missing)
        raise FitCheckException(
            message,
            code="INSUFFICIENT_WARDROBE",
            status_code=400
        )

    results = generate_outfits(
        wardrobe_items=wardrobe_items,
        occasion=occasion,
        mood=mood,
        weather=weather,
        excluded_item_ids=excluded_item_ids,
        max_results=max_results
    )

    logger.info(
        "Stylist pipeline complete — user=%s outfits=%d weather_used=%s",
        user_id, len(results), weather is not None
    )

    return results