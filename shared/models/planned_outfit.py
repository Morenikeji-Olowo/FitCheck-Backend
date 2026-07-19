from pydantic import BaseModel
from datetime import date
from uuid import UUID
from enum import Enum


class PlannedOutfitSource(str, Enum):
    MANUAL = "manual"
    GENERATOR = "generator"
    DRESS_ME = "dress_me"
    DAILY_SUGGESTION = "daily_suggestion"


class PlannedOutfitStatus(str, Enum):
    PLANNED = "planned"
    WORN = "worn"
    SKIPPED = "skipped"


class CreatePlannedOutfitRequest(BaseModel):
    scheduled_date: date
    item_ids: list[UUID]
    outfit_id: UUID | None = None
    occasion: str | None = None
    notes: str | None = None
    source: PlannedOutfitSource = PlannedOutfitSource.MANUAL


class UpdatePlannedOutfitRequest(BaseModel):
    item_ids: list[UUID] | None = None
    occasion: str | None = None
    notes: str | None = None
    status: PlannedOutfitStatus | None = None