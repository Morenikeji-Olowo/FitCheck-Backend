import io
from PIL import Image, ImageEnhance
from core.config.settings import settings
from shared.logger import get_logger

logger = get_logger(__name__)

def enhance_image(image_bytes: bytes) -> bytes:
    """
    Enhances clothing or avatar image after background removal.
    Makes it look clean and editorial — like Pinterest clothing cards.

    Pipeline:
    Resize → Sharpen → Contrast → Brightness → Color → Compress
    """
    try:
        logger.info("Starting image enhancement")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        # 1. Resize oversized images — keeps S3 lean and processing fast
        image.thumbnail(
            (settings.MAX_IMAGE_SIZE, settings.MAX_IMAGE_SIZE),
            Image.Resampling.LANCZOS
        )
        logger.debug(f"Resized to {image.size}")

        # 2. Convert to RGB for enhancement operations
        rgb = image.convert("RGB")

        # 3. Sharpness — smoother than ImageFilter.SHARPEN
        rgb = ImageEnhance.Sharpness(rgb).enhance(settings.SHARPNESS_FACTOR)

        # 4. Contrast boost — makes colors pop
        rgb = ImageEnhance.Contrast(rgb).enhance(settings.CONTRAST_FACTOR)

        # 5. Brightness correction
        rgb = ImageEnhance.Brightness(rgb).enhance(settings.BRIGHTNESS_FACTOR)

        # 6. Color saturation — vibrant not washed out
        rgb = ImageEnhance.Color(rgb).enhance(settings.COLOR_FACTOR)

        # 7. Restore original alpha channel (background transparency)
        result = rgb.convert("RGBA")
        r, g, b, _ = result.split()
        _, _, _, original_alpha = image.split()
        result = Image.merge("RGBA", (r, g, b, original_alpha))

        # 8. Save — strip metadata for privacy + smaller file
        output = io.BytesIO()
        result.save(
            output,
            format="PNG",
            optimize=True,
            compress_level=6
        )
        output.seek(0)

        logger.info("Image enhancement complete")
        return output.read()

    except Exception as e:
        logger.error(f"Image enhancement failed: {e}")
        logger.warning("Returning original image — enhancement skipped")
        return image_bytes