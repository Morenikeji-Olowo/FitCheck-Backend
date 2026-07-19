import time
from fastapi import APIRouter, Query
from pydantic import BaseModel
from uuid import UUID
from workers.outfit.explainer import analyze_outfit
from shared.logger import get_logger
from shared.models.responses import SuccessResponse
from shared.exceptions import ClothingItemNotFoundError, FitCheckException
from core.storage.supabase_client import supabase
from workers.outfit.compatibility import calculate_compatibility
from workers.outfit.validator import validate_outfit_composition
from shared.models.enums import OutfitOccasion

logger = get_logger(__name__)

router = APIRouter(prefix="/outfit", tags=["Outfit"])

MAX_OUTFIT_ITEMS = 10


class CompatibilityRequest(BaseModel):
    item_ids: list[UUID]


class AnalyzeRequest(BaseModel):
    item_ids: list[UUID]
    occasion: OutfitOccasion = OutfitOccasion.EVERYDAY


class SaveOutfitRequest(BaseModel):
    item_ids: list[UUID]
    occasion: OutfitOccasion = OutfitOccasion.EVERYDAY
    name: str | None = None

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

@router.post("/analyze", response_model=SuccessResponse)
async def analyze_outfit_endpoint(
    body: AnalyzeRequest,
    user_id: UUID = Query(...)
):
    """
    Deep AI analysis — called after user pauses on an outfit.
    Does NOT save anything. Uses style profile + avatar body profile.
    """
    if len(body.item_ids) > MAX_OUTFIT_ITEMS:
        raise FitCheckException(
            f"An outfit can contain at most {MAX_OUTFIT_ITEMS} items.",
            code="TOO_MANY_ITEMS",
            status_code=400
        )

    if len(body.item_ids) < 2:
        raise FitCheckException(
            "Select at least 2 items to analyze an outfit.",
            code="TOO_FEW_ITEMS",
            status_code=400
        )

    logger.info(f"Outfit analysis — user={user_id} items={len(body.item_ids)}")

    ids = [str(i) for i in body.item_ids]

    # Fetch items — richer field set for AI context
    items_result = supabase.table("closet_items")\
        .select("item_id, category, item_type, dominant_color, dominant_hex, "
                "pattern, style, material, occasions, seasons")\
        .eq("user_id", str(user_id))\
        .in_("item_id", ids)\
        .execute()

    if not items_result.data or len(items_result.data) != len(ids):
        raise ClothingItemNotFoundError()

    items = items_result.data
    validate_outfit_composition(items)
    # Rule-based scores first — feeds into the AI prompt
    rule_scores = calculate_compatibility(items)

    # Fetch style profile — default if not onboarded yet
    style_result = supabase.table("style_profiles")\
        .select("styles, preferred_colors, disliked_colors")\
        .eq("user_id", str(user_id))\
        .single()\
        .execute()
    style_profile = style_result.data or {}

    # Fetch avatar body profile — default if no avatar yet
    avatar_result = supabase.table("avatars")\
        .select("body_profile")\
        .eq("user_id", str(user_id))\
        .single()\
        .execute()
    body_profile = (avatar_result.data or {}).get("body_profile") or {}

    ai_result = analyze_outfit(
        items=items,
        style_profile=style_profile,
        body_profile=body_profile,
        rule_scores=rule_scores,
        occasion=body.occasion.value
    )

    return SuccessResponse(data={
        **rule_scores,
        "ai": ai_result
    })

@router.post("/save", response_model=SuccessResponse)
async def save_outfit(
    body: SaveOutfitRequest,
    user_id: UUID = Query(...)
):
    """
    Save a liked outfit combo.
    Re-runs compatibility + AI analysis and persists the result.
    """
    if len(body.item_ids) > MAX_OUTFIT_ITEMS:
        raise FitCheckException(
            f"An outfit can contain at most {MAX_OUTFIT_ITEMS} items.",
            code="TOO_MANY_ITEMS", status_code=400
        )

    ids = [str(i) for i in body.item_ids]
    logger.info(f"Save outfit — user={user_id} items={len(ids)}")

    items_result = supabase.table("closet_items")\
        .select("item_id, category, item_type, dominant_color, dominant_hex, "
                "pattern, style, material, occasions, seasons")\
        .eq("user_id", str(user_id))\
        .in_("item_id", ids)\
        .execute()

    if not items_result.data or len(items_result.data) != len(ids):
        raise ClothingItemNotFoundError()

    items = items_result.data
    validate_outfit_composition(items)
    rule_scores = calculate_compatibility(items)

    style_result = supabase.table("style_profiles")\
        .select("styles, preferred_colors, disliked_colors")\
        .eq("user_id", str(user_id)).single().execute()
    style_profile = style_result.data or {}

    avatar_result = supabase.table("avatars")\
        .select("body_profile")\
        .eq("user_id", str(user_id)).single().execute()
    body_profile = (avatar_result.data or {}).get("body_profile") or {}

    ai_result = analyze_outfit(
        items=items, style_profile=style_profile,
        body_profile=body_profile, rule_scores=rule_scores,
        occasion=body.occasion.value
    )

    data = {
        "user_id": str(user_id),
        "item_ids": ids,
        "overall_score": rule_scores["overall_score"],
        "overall_grade": rule_scores["overall_grade"],
        "color_score": rule_scores["color_score"],
        "style_score": rule_scores["style_score"],
        "occasion_score": rule_scores["occasion_score"],
        "season_score": rule_scores["season_score"],
        "ai_summary": ai_result["summary"],
        "ai_highlights": ai_result["highlights"],
        "ai_suggestions": ai_result["suggestions"],
        "ai_personalization_note": ai_result["personalization_note"],
        "ai_confidence": ai_result["confidence"],
        "occasion": body.occasion.value,
        "name": body.name,
    }

    result = supabase.table("outfits").insert(data).execute()

    if not result.data:
        raise FitCheckException(
            "Failed to save outfit.", code="DATABASE_ERROR", status_code=500
        )

    logger.info(f"Outfit saved — id={result.data[0]['outfit_id']}")
    return SuccessResponse(data=result.data[0])


@router.get("/", response_model=SuccessResponse)
async def get_outfits(
    user_id: UUID = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List saved outfits for a user"""
    logger.info(f"Get outfits — user={user_id}")

    result = supabase.table("outfits")\
        .select("*", count="exact")\
        .eq("user_id", str(user_id))\
        .order("created_at", desc=True)\
        .range(offset, offset + limit - 1)\
        .execute()

    total = result.count or 0
    return SuccessResponse(data={
        "outfits": result.data,
        "pagination": {
            "total": total, "limit": limit, "offset": offset,
            "has_more": (offset + limit) < total
        }
    })

@router.delete("/{outfit_id}", response_model=SuccessResponse)
async def delete_outfit(outfit_id: UUID, user_id: UUID = Query(...)):
    """Delete a saved outfit"""
    logger.info(f"Delete outfit — id={outfit_id} user={user_id}")

    result = supabase.table("outfits")\
        .delete()\
        .eq("outfit_id", str(outfit_id))\
        .eq("user_id", str(user_id))\
        .execute()

    if not result.data:
        raise FitCheckException(
            "Outfit not found.", code="OUTFIT_NOT_FOUND", status_code=404
        )

    return SuccessResponse(data={"message": "Outfit deleted successfully"})