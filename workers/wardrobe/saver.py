import hashlib
from datetime import datetime, UTC
from core.storage.supabase_client import supabase
from shared.logger import get_logger
from shared.exceptions import FitCheckException
from shared.models.clothing import ClothingItem

logger = get_logger(__name__)

PROMPT_VERSION = "wardrobe-v1"
AI_MODEL = "gpt-4o"

def save_clothing_item(item: ClothingItem, image_bytes: bytes) -> ClothingItem:
    """
    Saves ClothingItem to Supabase closet_items table.
    Returns the same item — confirms save was successful.
    """
    try:
        logger.info(f"Saving clothing item — user: {item.user_id}")

        # Generate image hash to detect duplicates later
        image_hash = hashlib.md5(image_bytes).hexdigest()

        # Build search text for full-text search later
        search_text = " ".join(filter(None, [
            item.dominant_color,
            item.item_type,
            item.style,
            item.brand,
            item.material,
            " ".join(item.colors),
            " ".join([s.value for s in item.seasons]),
            item.category.value
        ]))

        data = {
            "item_id": str(item.item_id),
            "user_id": str(item.user_id),
            "original_image_url": item.original_image_url,
            "clean_image_url": item.clean_image_url,
            "image_hash": image_hash,
            "category": item.category.value,
            "item_type": item.item_type,
            "colors": item.colors,
            "dominant_color": item.dominant_color,
            "dominant_hex": item.dominant_hex,
            "secondary_color": item.secondary_color,
            "secondary_hex": item.secondary_hex,
            "accent_color": item.accent_color,
            "accent_hex": item.accent_hex,
            "pattern": item.pattern.value if item.pattern else None,
            "style": item.style.value if item.style else None,
            "seasons": [s.value for s in item.seasons],
            "occasions": [o.value for o in item.occasions],
            "brand": item.brand,
            "material": item.material,
            "pairs_well_with": item.pairs_well_with,
            "image_width": item.image_width,
            "image_height": item.image_height,
            "classification_confidence": item.classification_confidence,
            "ai_model": AI_MODEL,
            "prompt_version": PROMPT_VERSION,
            "processed_at": datetime.now(UTC).isoformat(),
            "processing_status": "completed",
            "search_text": search_text,
            "favorite": False,
            "times_worn": 0,
            "is_archived": False
        }
        result = supabase.table("closet_items").insert(data).execute()

        if not result.data:
            raise FitCheckException("Failed to save clothing item to database.")

        logger.info(f"Clothing item saved — {item.category} / {item.item_type}")
        return item

    except FitCheckException:
        raise
    except Exception as e:
        logger.error(f"Failed to save clothing item: {e}")
        raise FitCheckException(
            "Something went wrong saving your item. Please try again.",
            code="DATABASE_ERROR",
            status_code=500
        )