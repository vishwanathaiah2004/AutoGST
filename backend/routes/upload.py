import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from config.database import get_db
from models.models import User, UploadedFile
from models.schemas import OCRResponse, SuccessResponse
from services.auth_service import get_current_user
from services.ocr_service import process_uploaded_file

logger = logging.getLogger("autogst.routes.ocr")
router = APIRouter(prefix="/upload", tags=["File Upload & OCR"])


@router.post("", response_model=OCRResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload an invoice image and extract data via OCR."""
    logger.info("File upload: user=%d filename=%s", current_user.id, file.filename)
    db_file = await process_uploaded_file(db, file, current_user)
    return OCRResponse(
        file_id=db_file.id,
        filename=db_file.original_filename,
        ocr_text=db_file.ocr_text,
        ocr_status=db_file.ocr_status,
        parsed_data=db_file.parsed_data,
        parsing_method=db_file.parsing_method,
        confidence=db_file.ocr_confidence,
    )


@router.get("", response_model=list)
def list_uploads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all uploaded files for the current user."""
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.user_id == current_user.id)
        .order_by(UploadedFile.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": f.id,
            "filename": f.original_filename,
            "ocr_status": f.ocr_status,
            "parsing_method": f.parsing_method,
            "file_size": f.file_size,
            "created_at": str(f.created_at),
        }
        for f in files
    ]


@router.get("/{file_id}", response_model=OCRResponse)
def get_upload(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get OCR result for a specific uploaded file."""
    f = db.query(UploadedFile).filter(
        UploadedFile.id == file_id, UploadedFile.user_id == current_user.id
    ).first()
    if not f:
        raise HTTPException(404, "File not found")
    return OCRResponse(
        file_id=f.id,
        filename=f.original_filename,
        ocr_text=f.ocr_text,
        ocr_status=f.ocr_status,
        parsed_data=f.parsed_data,
        parsing_method=f.parsing_method,
        confidence=f.ocr_confidence,
    )
