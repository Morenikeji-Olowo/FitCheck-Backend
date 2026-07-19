from fastapi import APIRouter, Query
from uuid import UUID
from shared.logger import get_logger
from shared.models.responses import SuccessResponse
from shared.exceptions import FitCheckException
from core.storage.supabase_client import supabase

logger = get_logger(__name__)

router = APIRouter(prefix="/social", tags=["Social"])


@router.get("/health")
async def health():
    return { "service": "social", "version": "1.0.0", "status": "healthy" }


@router.post("/follow/{target_user_id}", response_model=SuccessResponse)
async def follow_user(
    target_user_id: UUID,
    user_id: UUID = Query(...)
):
    """Follow another user"""
    if str(target_user_id) == str(user_id):
        raise FitCheckException(
            "You can't follow yourself.",
            code="INVALID_FOLLOW", status_code=400
        )

    logger.info(f"Follow — follower={user_id} following={target_user_id}")

    user_result = supabase.table("profiles")\
        .select("id")\
        .eq("id", str(target_user_id))\
        .single()\
        .execute()

    if not user_result.data:
        raise FitCheckException(
            "User not found.", code="USER_NOT_FOUND", status_code=404
        )

    existing = supabase.table("follows")\
        .select("follower_id")\
        .eq("follower_id", str(user_id))\
        .eq("following_id", str(target_user_id))\
        .execute()

    if existing.data:
        return SuccessResponse(data={
            "message": "Already following",
            "following_id": str(target_user_id)
        })

    result = supabase.table("follows")\
        .insert({
            "follower_id": str(user_id),
            "following_id": str(target_user_id)
        })\
        .execute()

    if not result.data:
        raise FitCheckException(
            "Failed to follow user.", code="DATABASE_ERROR", status_code=500
        )

    counts = _get_follow_counts(str(target_user_id))

    return SuccessResponse(data={
        "message": "Now following",
        "following_id": str(target_user_id),
        **counts
    })


@router.delete("/follow/{target_user_id}", response_model=SuccessResponse)
async def unfollow_user(
    target_user_id: UUID,
    user_id: UUID = Query(...)
):
    """Unfollow a user"""
    logger.info(f"Unfollow — follower={user_id} following={target_user_id}")

    supabase.table("follows")\
        .delete()\
        .eq("follower_id", str(user_id))\
        .eq("following_id", str(target_user_id))\
        .execute()

    counts = _get_follow_counts(str(target_user_id))

    return SuccessResponse(data={
        "message": "Unfollowed",
        "following_id": str(target_user_id),
        **counts
    })


@router.get("/followers", response_model=SuccessResponse)
async def get_followers(
    user_id: UUID = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of users following this user"""
    result = supabase.table("follows")\
        .select("follower_id, created_at, profiles!follows_follower_id_fkey(id, full_name)", count="exact")\
        .eq("following_id", str(user_id))\
        .order("created_at", desc=True)\
        .range(offset, offset + limit - 1)\
        .execute()

    followers = result.data or []
    total = result.count or 0

    return SuccessResponse(data={
        "followers": followers,
        "pagination": {
            "total": total, "limit": limit, "offset": offset,
            "has_more": (offset + limit) < total
        }
    })


@router.get("/following", response_model=SuccessResponse)
async def get_following(
    user_id: UUID = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of users this user follows"""
    result = supabase.table("follows")\
        .select("following_id, created_at, profiles!follows_following_id_fkey(id, full_name)", count="exact")\
        .eq("follower_id", str(user_id))\
        .order("created_at", desc=True)\
        .range(offset, offset + limit - 1)\
        .execute()

    following = result.data or []
    total = result.count or 0

    return SuccessResponse(data={
        "following": following,
        "pagination": {
            "total": total, "limit": limit, "offset": offset,
            "has_more": (offset + limit) < total
        }
    })


def _get_follow_counts(user_id: str) -> dict:
    """Shared helper — returns current followers/following counts for a user."""
    followers = supabase.table("follows")\
        .select("follower_id", count="exact")\
        .eq("following_id", user_id).execute()

    following = supabase.table("follows")\
        .select("following_id", count="exact")\
        .eq("follower_id", user_id).execute()

    return {
        "followers_count": followers.count or 0,
        "following_count": following.count or 0
    }