from pydantic import BaseModel, UUID4, Field
from datetime import datetime, UTC
import uuid

class OutfitPreview(BaseModel):
    outfit_id: UUID4 = Field(default_factory=uuid.uuid4)
    user_id: UUID4
    avatar_id: UUID4
    item_ids: list[UUID4]
    preview_url: str
    confidence_score: float = Field(ge=0, le=10)
    color_harmony: str
    style_consistency: str
    occasion_fit: str
    strengths: list[str]
    improvements: list[str]
    summary: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    class Config:
        json_encoders = { uuid.UUID: str }