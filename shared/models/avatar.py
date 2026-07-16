from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime, UTC
import uuid
from shared.models.body import BodyProfile

class AvatarProfile(BaseModel):
    avatar_id: UUID4 = Field(default_factory=uuid.uuid4)
    user_id: UUID4
    original_photo_url: str
    processed_photo_url: str
    body: BodyProfile
    avatar_version: int = 1

    # User editable overrides
    display_height: str | None = None
    display_body_shape: str | None = None
    display_skin_tone: str | None = None
    hair_style: str | None = None
    hair_color: str | None = None

    is_setup: bool = False
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    class Config:
        json_encoders = { uuid.UUID: str }