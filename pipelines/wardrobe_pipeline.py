from fastapi import UploadFile
from shared.logger import get_logger
from shared.models.clothing import ClothingItem
from core.image.validator import validate_image, check_free_tier_limit
from core.image.enhancer import enhance_image
from core.storage.s3 import storage, S3Folders
from workers.wardrobe.background import remove_background
from workers.wardrobe.classifier import classify_clothing
from workers.wardrobe.metadata import build_clothing_item
from workers.wardrobe.saver import save_clothing_item

logger = get_logger(__name__)

async def run_wardrobe_pipeline(
    file: UploadFile,
    user_id: str
) -> ClothingItem:
    """
    Full wardrobe processing pipeline.

    Upload → Validate → Remove BG → Enhance →
    Classify → Build Item → Save to DB → Return

    Max execution time: 30 seconds
    Retries: handled inside each worker
    Rollback: S3 cleanup on failure
    """

    original_key = None
    clean_key = None

    try:
        logger.info(f"Wardrobe pipeline started — user: {user_id}")
        
        # 0. Free tier check — before any expensive operations
        check_free_tier_limit(user_id)
        logger.info("Step 0/7 — Free tier check passed")

        # 1. Read image bytes
        image_bytes = await file.read()
        content_type = file.content_type

        # 2. Validate
        validate_image(image_bytes, content_type)
        logger.info("Step 1/7 — Validation passed")

        # 3. Upload original to S3
        original_result = storage.upload(
            image_bytes,
            folder=f"{S3Folders.WARDROBE}/{user_id}/original",
            extension="png",
            content_type=content_type
        )
        original_key = original_result["key"]
        logger.info("Step 2/7 — Original uploaded to S3")

        # 4. Remove background
        clean_bytes = remove_background(image_bytes)
        logger.info("Step 3/7 — Background removed")

        # 5. Enhance image
        enhanced_bytes = enhance_image(clean_bytes)
        logger.info("Step 4/7 — Image enhanced")

        # 6. Upload clean image to S3
        clean_result = storage.upload(
            enhanced_bytes,
            folder=f"{S3Folders.WARDROBE}/{user_id}/clean",
            extension="png",
            content_type="image/png"
        )
        clean_key = clean_result["key"]
        logger.info("Step 5/7 — Clean image uploaded to S3")

        # 7. Classify with GPT-4o Vision
        classification = classify_clothing(enhanced_bytes, "image/png")
        logger.info("Step 6/7 — Classification complete")

        # 8. Build final ClothingItem
        item = build_clothing_item(
            user_id=user_id,
            classification=classification,
            original_image_url=original_result["url"],
            clean_image_url=clean_result["url"],
            image_bytes=enhanced_bytes
        )

        # 9. Save to Supabase
        save_clothing_item(item, enhanced_bytes)
        logger.info("Step 7/7 — Saved to database")

        logger.info(
            f"Wardrobe pipeline complete — "
            f"{item.category} / {item.item_type} / "
            f"confidence: {item.classification_confidence}"
        )

        return item

    except Exception as e:
        logger.error(f"Wardrobe pipeline failed: {e}")
        _rollback(original_key, clean_key)
        raise


def _rollback(original_key: str | None, clean_key: str | None) -> None:
    """
    Clean up S3 uploads if pipeline fails.
    Prevents orphaned files in storage.
    """
    if original_key:
        deleted = storage.delete(original_key)
        logger.info(f"Rollback — original deleted: {deleted}")

    if clean_key:
        deleted = storage.delete(clean_key)
        logger.info(f"Rollback — clean image deleted: {deleted}")