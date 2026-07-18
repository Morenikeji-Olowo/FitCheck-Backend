from shared.logger import get_logger
from shared.models.avatar import AvatarProfile
from shared.models.body import BodyProfile
from shared.exceptions import FitCheckException

logger = get_logger(__name__)


def build_avatar_profile(
    user_id: str,
    body_profile: BodyProfile,
    original_photo_url: str,
    processed_photo_url: str,
    *,
    avatar_version: int = 1,
    is_setup: bool = True,
) -> AvatarProfile:
    """
    Assembles AvatarProfile from analyzed body data + image URLs.
    Pipeline decides the version — builder just constructs the object.
    """
    # Validate URLs — builder should reject invalid objects
    if not original_photo_url:
        raise FitCheckException("Original photo URL is required.")
    if not processed_photo_url:
        raise FitCheckException("Processed photo URL is required.")

    # Clamp version — never allow negative or zero
    safe_version = max(1, avatar_version)

    try:
        profile = AvatarProfile(
            user_id=user_id,
            original_photo_url=original_photo_url,
            processed_photo_url=processed_photo_url,
            body=body_profile,
            avatar_version=safe_version,
            is_setup=is_setup
        )

        logger.info(
            "Avatar built user=%s version=%d shape=%s build=%s confidence=%.2f",
            user_id,
            profile.avatar_version,
            body_profile.body_shape.value,
            body_profile.build.value,
            body_profile.analysis_confidence
        )

        return profile

    except Exception as e:
        logger.exception("Failed to build avatar profile")
        raise