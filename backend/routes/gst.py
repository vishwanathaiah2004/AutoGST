import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from models.models import User
from models.schemas import GSTCalculationRequest, GSTCalculationResponse, SuccessResponse
from services.auth_service import get_current_user
from services.gst_service import calculate_gst_api, get_gst_rate_for_hsn

logger = logging.getLogger("autogst.routes.gst")
router = APIRouter(prefix="/gst", tags=["GST Engine"])


@router.post("/calculate", response_model=GSTCalculationResponse)
def calculate(
    request: GSTCalculationRequest,
    current_user: User = Depends(get_current_user),
):
    """Calculate GST breakdown for a given amount and rate."""
    logger.info("GST calc: user=%d amount=%.2f rate=%.2f", current_user.id, float(request.amount), float(request.gst_rate))
    return calculate_gst_api(request)


@router.get("/hsn-rate/{hsn_code}")
def get_hsn_rate(
    hsn_code: str,
    current_user: User = Depends(get_current_user),
):
    """Look up GST rate by HSN/SAC code."""
    rate = get_gst_rate_for_hsn(hsn_code)
    return {
        "hsn_code": hsn_code,
        "gst_rate": float(rate) if rate is not None else None,
        "found": rate is not None,
    }


@router.get("/rates")
def list_gst_rates(current_user: User = Depends(get_current_user)):
    """Return all valid GST rates in India."""
    return {
        "rates": [0, 0.25, 3, 5, 12, 18, 28],
        "slabs": {
            "0%": "Essential goods (food grains, milk, eggs, fresh vegetables)",
            "0.25%": "Cut & semi-polished stones",
            "3%": "Gold, silver, precious metals",
            "5%": "Edible oils, sugar, spices, coal, fertilizers",
            "12%": "Computers, processed food, business class air tickets",
            "18%": "Most goods and services (AC, electronics, telecom, IT services)",
            "28%": "Luxury goods (cars, tobacco, AC, cement)",
        },
    }
