from datetime import datetime, UTC
from PIL import Image
import io
import uuid

from shared.logger import get_logger
from shared.models.clothing import ClothingItem, ClothingClassification

logger = get_logger(__name__)

def build_clothing_item(
    user_id: str,
    classification: ClothingClassification,
    original_image_url: str,
    clean_image_url: str,
    image_bytes: bytes
) -> ClothingItem:
    """
    Takes classification result + image URLs
    and builds a complete ClothingItem model.
    This is the final step before saving to database.
    """
    try:
        logger.info("Building clothing item metadata")

        # Get image dimensions
        width, height = _get_dimensions(image_bytes)

        item = ClothingItem(
            item_id=uuid.uuid4(),
            user_id=user_id,
            original_image_url=original_image_url,
            clean_image_url=clean_image_url,
            category=classification.category,
            item_type=classification.item_type,
            colors=classification.colors,
            dominant_color=classification.dominant_color,
            secondary_color=classification.secondary_color,
            pattern=classification.pattern,
            style=classification.style,
            seasons=classification.seasons,
            occasions=classification.occasions,
            brand=classification.brand,
            pairs_well_with=classification.pairs_well_with,
            material=classification.material,
            image_width=width,
            image_height=height,
            classification_confidence=classification.classification_confidence,
            favorite=False,
            times_worn=0,
            last_worn=None,
            is_archived=False
        )

        logger.info(f"ClothingItem built — {item.category} / {item.item_type}")
        return item

    except Exception as e:
        logger.error(f"Failed to build clothing item: {e}")
        raise


def _get_dimensions(image_bytes: bytes) -> tuple[int, int]:
    """Extract width and height from image bytes."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return image.size
    except Exception as e:
        logger.warning(f"Could not extract dimensions: {e} — using defaults")
        return 0, 0