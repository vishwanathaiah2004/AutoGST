import logging
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from config.database import get_db
from models.models import User
from models.schemas import ReportRequest
from services.auth_service import get_current_user
from services.report_service import (
    generate_report_data, generate_pdf_report, generate_excel_report
)

logger = logging.getLogger("autogst.routes.reports")
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/gstr")
def get_gstr_report(
    report_type: str = Query(..., description="GSTR-1 or GSTR-3B"),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get GST return data in JSON format."""
    logger.info("Report request: user=%d type=%s period=%d-%02d", current_user.id, report_type, year, month)
    return generate_report_data(db, current_user.id, report_type, month, year)


@router.get("/gstr/pdf")
def download_gstr_pdf(
    report_type: str = Query(...),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download GST return report as PDF."""
    data = generate_report_data(db, current_user.id, report_type, month, year)
    pdf_bytes = generate_pdf_report(data, report_type)
    filename = f"{report_type.replace('-', '')}_{year}_{month:02d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/gstr/excel")
def download_gstr_excel(
    report_type: str = Query(...),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download GST return report as Excel."""
    excel_bytes = generate_excel_report(db, current_user.id, month, year, report_type)
    filename = f"{report_type.replace('-', '')}_{year}_{month:02d}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
