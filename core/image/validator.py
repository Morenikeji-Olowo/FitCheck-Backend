from PIL import Image
import io
import cv2
import numpy as np
from core.config.settings import settings
from shared.logger import get_logger
from shared.exceptions import (
    ImageTooLargeError,
    InvalidImageFormatError,
    BlurryImageError
)
from core.storage.supabase_client import supabase
from shared.exceptions import FreeTierLimitError
from core.config.settings import settings

logger = get_logger(__name__)

ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
UNLIMITED_TIERS = {"premium", "pro", "enterprise"}


def validate_image(image_bytes: bytes, content_type: str) -> Image.Image:
    """
    Validates image before any AI processing.
    Returns decoded PIL Image so pipeline doesn't decode again.
    Order matters — cheapest checks first.
    """

    # 1. Empty check first — nothing else matters if no bytes
    if not image_bytes or len(image_bytes) == 0:
        logger.warning("Empty image received")
        raise InvalidImageFormatError("Image appears to be empty. Please try again.")

    # 2. File size check
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        logger.warning(f"Image too large: {len(image_bytes)} bytes")
        raise ImageTooLargeError()

    # 3. Verify actual file content — don't trust content_type header
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
        # Re-open after verify — verify() exhausts the file object
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        logger.warning("Invalid or corrupted image file")
        raise InvalidImageFormatError("Invalid or corrupted image. Please try again.")

    # 4. Check actual MIME type from file content
    mime_map = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    actual_mime = mime_map.get(image.format)
    if actual_mime not in ALLOWED_MIME_TYPES:
        logger.warning(f"Unsupported image format: {image.format}")
        raise InvalidImageFormatError()

    # 5. Dimension checks
    width, height = image.size
    if width < settings.MIN_IMAGE_DIMENSION or height < settings.MIN_IMAGE_DIMENSION:
        logger.warning(f"Image too small: {width}x{height}")
        raise InvalidImageFormatError(
            f"Image too small. Minimum size is "
            f"{settings.MIN_IMAGE_DIMENSION}x{settings.MIN_IMAGE_DIMENSION}px."
        )

    if width > settings.MAX_IMAGE_DIMENSION or height > settings.MAX_IMAGE_DIMENSION:
        logger.warning(f"Image too large dimensions: {width}x{height}")
        raise InvalidImageFormatError(
            f"Image dimensions too large. Maximum is "
            f"{settings.MAX_IMAGE_DIMENSION}x{settings.MAX_IMAGE_DIMENSION}px."
        )

    # 6. Blur detection using Laplacian variance
    _check_blur(image_bytes)

    logger.info(f"Image validation passed — {width}x{height} {image.format}")
    return image


def _check_blur(image_bytes: bytes) -> None:
    """
    Blur detection using Laplacian variance — industry standard approach.
    Much more reliable than edge detection for clothing items.
    """
    try:
        # Convert to numpy array for OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if img is None:
            logger.warning("OpenCV could not decode image — skipping blur check")
            return

        # Laplacian variance — low variance = blurry
        variance = cv2.Laplacian(img, cv2.CV_64F).var()

        logger.debug(f"Blur variance: {variance} (threshold: {settings.BLUR_THRESHOLD})")

        if variance < settings.BLUR_THRESHOLD:
            logger.warning(f"Blurry image detected — variance: {variance}")
            raise BlurryImageError()

    except BlurryImageError:
        raise
    except Exception as e:
        # Never block upload if blur detection fails
        logger.warning(f"Blur detection skipped: {e}")
    
    
def check_free_tier_limit(user_id: str) -> None:
    """
    Checks if free user has hit the item limit.
    Runs before any AI processing — saves credits.
    """
    try:
        profile = supabase.table("profiles")\
            .select("tier")\
            .eq("id", user_id)\
            .single()\
            .execute()

        if not profile.data:
            return

        tier = profile.data.get("tier", "free")

        if tier in UNLIMITED_TIERS:
            return

        result = supabase.table("closet_items")\
            .select("item_id", count="exact")\
            .eq("user_id", user_id)\
            .eq("is_archived", False)\
            .execute()

        count = result.count or 0

        if count >= settings.FREE_TIER_LIMIT:
            raise FreeTierLimitError(
                f"You've reached your free limit of "
                f"{settings.FREE_TIER_LIMIT} wardrobe items. "
                f"Upgrade to Premium for unlimited storage."
            )

    except FreeTierLimitError:
        raise
    except Exception as e:
        logger.error(f"Failed to check free tier limit: {e}")
        raise