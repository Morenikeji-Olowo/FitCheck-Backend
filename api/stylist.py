from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, UTC
from shared.logger import get_logger
from shared.models.responses import SuccessResponse
from shared.models.enums import OutfitOccasion, OutfitMood
from pipelines.stylist_pipeline import run_stylist_pipeline

logger = get_logger(__name__)

router = APIRouter(prefix="/stylist", tags=["Stylist"])


class GenerateRequest(BaseModel):
    occasion: OutfitOccasion = OutfitOccasion.EVERYDAY
    mood: OutfitMood | None = None
    excluded_item_ids: list[UUID] = Field(default_factory=list)
    max_results: int = 3


@router.get("/health")
async def health():
    return { "service": "stylist", "version": "1.0.0", "status": "healthy" }


@router.post("/generate", response_model=SuccessResponse)
async def generate_outfit_suggestions(
    body: GenerateRequest,
    user_id: UUID = Query(...)
):
    logger.info(f"Generate request — user={user_id} occasion={body.occasion}")

    result = await run_stylist_pipeline(
        user_id=str(user_id),
        occasion=body.occasion.value,
        mood=body.mood.value if body.mood else None,
        weather=None,
        excluded_item_ids=[str(i) for i in body.excluded_item_ids],
        max_results=body.max_results
    )

    status = "ok" if result["success"] else result["reason"]
    message = None
    if not result["success"]:
        if result["reason"] == "insufficient_wardrobe":
            missing = result["missing_categories"]
            message = (
                f"Add {' and '.join(missing)} to your wardrobe to unlock "
                f"outfit suggestions." if missing
                else "Add a few more items to unlock outfit suggestions."
            )
        else:
            message = "We couldn't put together an outfit right now. Try again."

    return SuccessResponse(data={
        "outfits": result["outfits"],
        "generated_at": datetime.now(UTC).isoformat(),
        "occasion": body.occasion.value,
        "mood": body.mood.value if body.mood else None,
        "count": len(result["outfits"]),
        "status": status,
        "message": message,
        "missing_categories": result["missing_categories"]
    })