from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from typing import Dict
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.upload_service import process_and_save_image

router = APIRouter()

@router.post("/image", response_model=Dict[str, str])
async def upload_image(
    file: UploadFile = File(...),
    img_type: str = Query("project", enum=["avatar", "project", "thumbnail"]),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and process an image.
    Automatically resizes based on img_type and converts to optimized JPEG.
    """
    url = await process_and_save_image(file, image_type=img_type)
    return {"url": url}
