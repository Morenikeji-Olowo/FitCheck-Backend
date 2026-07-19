from pydantic import BaseModel, Field
from shared.models.enums import OutfitOccasion, OutfitMood


class ExtractedIntent(BaseModel):
    occasion: OutfitOccasion
    mood: OutfitMood | None = None
    confidence: float = Field(ge=0, le=1)