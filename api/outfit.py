import time
from fastapi import APIRouter, Query
from pydantic import BaseModel
from uuid import UUID
from shared.logger import get_logger
from shared.models.responses import SuccessResponse
from shared.exceptions import ClothingItemNotFoundError, FitCheckException
from core.storage.supabase_client import supabase
from workers.outfit.compatibility import calculate_compatibility

logger = get_logger(__name__)

router = APIRouter(prefix="/outfit", tags=["Outfit"])

MAX_OUTFIT_ITEMS = 10


class CompatibilityRequest(BaseModel):
    item_ids: list[UUID]


@router.get("/health")
async def health():
    return { "service": "outfit", "version": "1.0.0", "status": "healthy" }


@router.post("/compatibility", response_model=SuccessResponse)
async def check_compatibility(
    body: CompatibilityRequest,
    user_id: UUID = Query(...)
):
    """
    Instant rule-based compatibility check.
    No AI call — called on every swipe/selection change.
    """
    if len(body.item_ids) > MAX_OUTFIT_ITEMS:
        raise FitCheckException(
            f"An outfit can contain at most {MAX_OUTFIT_ITEMS} items.",
            code="TOO_MANY_ITEMS",
            status_code=400
        )

    if len(body.item_ids) < 2:
        return SuccessResponse(data={
            "overall_score": 100,
            "overall_grade": "A+",
            "color_score": 100,
            "style_score": 100,
            "occasion_score": 100,
            "season_score": 100,
            "strengths": [],
            "warnings": [],
            "message": "Add more items to see compatibility",
            "engine": "rule-based",
            "engine_version": "1.0"
        })

    logger.info(f"Compatibility check — user={user_id} items={len(body.item_ids)}")

    ids = [str(i) for i in body.item_ids]

    result = supabase.table("closet_items")\
        .select("item_id, category, dominant_hex, style, occasions, seasons")\
        .eq("user_id", str(user_id))\
        .in_("item_id", ids)\
        .execute()

    if not result.data or len(result.data) != len(ids):
        raise ClothingItemNotFoundError()

    start = time.perf_counter()
    compatibility = calculate_compatibility(result.data)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("Compatibility calculated in %.2f ms", elapsed_ms)

    compatibility["message"] = None
    compatibility["engine"] = "rule-based"
    compatibility["engine_version"] = "1.0"

    return SuccessResponse(data=compatibility)