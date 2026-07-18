from pydantic import BaseModel, Field
from shared.models.enums import (
    BodyShape,
    SkinTone,
    HeightCategory,
    Build,
    ShoulderWidth,
    WaistDefinition,
)


class BodyProfile(BaseModel):
    body_shape: BodyShape
    height_category: HeightCategory
    skin_tone: SkinTone
    shoulder_width: ShoulderWidth
    waist_definition: WaistDefinition
    build: Build
    analysis_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="AI confidence score"
    )