from fastapi import APIRouter, UploadFile, File, Form
from uuid import UUID
from shared.logger import get_logger
from shared.models.responses import SuccessResponse
from shared.models.clothing import ClothingItem
from pipelines.wardrobe_pipeline import run_wardrobe_pipeline

logger = get_logger(__name__)

router = APIRouter(prefix="/wardrobe", tags=["Wardrobe"])


@router.post("/upload", response_model=SuccessResponse[ClothingItem])
async def upload_clothing_item(
    file: UploadFile = File(...),
    user_id: UUID = Form(...)
):
    """
    Upload a clothing photo.
    Validate → Remove BG → Enhance → Classify → Return ClothingItem
    """
    logger.info(f"Wardrobe upload request — user: {user_id}")
    item = await run_wardrobe_pipeline(file=file, user_id=str(user_id))
    return SuccessResponse[ClothingItem](data=item)


@router.get("/health")
async def health():
    return {
        "service": "wardrobe",
        "version": "1.0.0",
        "status": "healthy"
    }