from pydantic import BaseModel, Field
from datetime import datetime, UTC
from uuid import UUID


class StyleProfile(BaseModel):
    user_id: UUID
    styles: list[str] = []
    preferred_colors: list[str] = []
    disliked_colors: list[str] = []
    favorite_occasions: list[str] = []
    onboarding_completed: bool = False


class UpdateStyleProfileRequest(BaseModel):
    styles: list[str] | None = None
    preferred_colors: list[str] | None = None
    disliked_colors: list[str] | None = None
    favorite_occasions: list[str] | None = None
    onboarding_completed: bool | None = None