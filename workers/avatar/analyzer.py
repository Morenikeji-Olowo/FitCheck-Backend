from core.ai.vision_client import vision_client
from core.config.settings import settings
from shared.logger import get_logger
from shared.exceptions import AIAnalysisError
from shared.models.body import BodyProfile
from shared.models.enums import BodyOrientation, Pose
from shared.models.enums import (
    BodyShape, SkinTone, HeightCategory,
    Build, ShoulderWidth, WaistDefinition
)

logger = get_logger(__name__)

REQUIRED_FIELDS = [
    "body_shape", "height_category", "skin_tone",
    "shoulder_width", "waist_definition", "build", "confidence"
]

VALID_VISIBILITY = {"full", "partial"}


def analyze_body(
    image_bytes: bytes,
    content_type: str = "image/png"
) -> tuple[BodyProfile, dict, str, str]:
    """
    Sends user photo to GPT-4o Vision.
    Returns validated BodyProfile + raw AI result.
    Raw result stored as body_profile_ai — never overwritten.
    """
    try:
        logger.info("Starting body analysis")

        raw = vision_client.analyze_avatar(image_bytes, content_type)

        # 1. Check required fields first
        missing = [f for f in REQUIRED_FIELDS if f not in raw]
        if missing:
            logger.error("GPT-4o missing fields: %s", missing)
            raise AIAnalysisError(
                "AI analysis returned incomplete data. Please try again."
            )

        # 2. Validate confidence
        try:
            confidence = float(raw["confidence"])
        except (ValueError, TypeError):
            raise AIAnalysisError("AI returned an invalid confidence score.")

        if not 0 <= confidence <= 1:
            raise AIAnalysisError("AI returned an invalid confidence score.")

        if confidence < settings.MIN_BODY_CONFIDENCE:
            logger.warning("Low confidence body analysis: %.2f", confidence)
            raise AIAnalysisError(
                "Could not analyze body accurately. "
                "Please upload a clear full-body standing photo."
            )

        # 3. Validate body visibility
        visibility = raw.get("body_visibility", "partial")
        if visibility not in VALID_VISIBILITY:
            logger.warning(
                "Invalid body_visibility value '%s' — defaulting to partial",
                visibility
            )
            visibility = "partial"

        if visibility == "partial":
            logger.warning(
                "Partial body detected — avatar accuracy may be reduced"
            )


        # Validate orientation
        raw_orientation = raw.get("body_orientation", "front")
        orientation = _parse_enum(BodyOrientation, raw_orientation, BodyOrientation.FRONT)

        raw_pose = raw.get("pose", "standing")
        pose = _parse_enum(Pose, raw_pose, Pose.STANDING)

        # Reject back-facing or bad poses
        if orientation == BodyOrientation.BACK or pose in (Pose.SITTING, Pose.OTHER):
            logger.warning(f"Rejected photo — orientation={orientation.value} pose={pose.value}")
            raise AIAnalysisError(
                "Please upload a standing photo facing the camera for best results."
            )

        accuracy_map = {
            BodyOrientation.FRONT: "excellent",
            BodyOrientation.FRONT_LEFT: "good",
            BodyOrientation.FRONT_RIGHT: "good",
            BodyOrientation.SIDE_LEFT: "fair",
            BodyOrientation.SIDE_RIGHT: "fair",
        }
        accuracy = accuracy_map.get(orientation, "fair")
        logger.info(f"Photo orientation: {orientation.value} ({accuracy})")
        # 4. Build BodyProfile
        profile = BodyProfile(
            body_shape=_parse_enum(
                BodyShape, raw.get("body_shape"), BodyShape.RECTANGLE
            ),
            height_category=_parse_enum(
                HeightCategory, raw.get("height_category"), HeightCategory.AVERAGE
            ),
            skin_tone=_parse_enum(
                SkinTone, raw.get("skin_tone"), SkinTone.MEDIUM
            ),
            shoulder_width=_parse_enum(
                ShoulderWidth, raw.get("shoulder_width"), ShoulderWidth.AVERAGE
            ),
            waist_definition=_parse_enum(
                WaistDefinition, raw.get("waist_definition"), WaistDefinition.AVERAGE
            ),
            build=_parse_enum(
                Build, raw.get("build"), Build.AVERAGE
            ),
            analysis_confidence=confidence
        )

        logger.info(
            "Body analysis complete shape=%s build=%s skin=%s confidence=%.2f",
            profile.body_shape.value,
            profile.build.value,
            profile.skin_tone.value,
            confidence
        )

        return profile, raw, orientation.value, accuracy

    except AIAnalysisError:
        raise
    except Exception:
        logger.exception("Body analysis failed")
        raise AIAnalysisError()


def _parse_enum(enum_class, value, default):
    """Parse GPT value into enum — return default if unknown."""
    try:
        return enum_class(str(value).lower())
    except (ValueError, KeyError):
        logger.warning(
            "GPT returned invalid %s value '%s'. Expected one of %s. Defaulting to %s.",
            enum_class.__name__,
            value,
            [e.value for e in enum_class],
            default.value
        )
        return default