import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from models.models import User
from models.schemas import TaxCalculationRequest, TaxCalculationResponse, SuccessResponse
from services.auth_service import get_current_user
from services.tax_service import calculate_income_tax, save_tax_calculation

logger = logging.getLogger("autogst.routes.tax")
router = APIRouter(prefix="/tax", tags=["Tax Calculator"])


@router.post("/calculate", response_model=TaxCalculationResponse)
def calculate_tax(
    request: TaxCalculationRequest,
    save: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate income tax liability under old or new regime."""
    logger.info(
        "Tax calc: user=%d regime=%s income=%.2f",
        current_user.id, request.regime, float(request.gross_income)
    )
    result = calculate_income_tax(request)
    if save:
        save_tax_calculation(db, current_user.id, request, result)
    return result


@router.get("/history")
def tax_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get previous tax calculations for the current user."""
    from models.models import TaxCalculation
    calcs = (
        db.query(TaxCalculation)
        .filter(TaxCalculation.user_id == current_user.id)
        .order_by(TaxCalculation.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "id": c.id,
            "assessment_year": c.assessment_year,
            "regime": c.regime,
            "gross_income": float(c.gross_income),
            "taxable_income": float(c.taxable_income),
            "total_tax_liability": float(c.total_tax_liability),
            "effective_tax_rate": c.effective_tax_rate,
            "created_at": str(c.created_at),
        }
        for c in calcs
    ]


@router.get("/slabs")
def get_tax_slabs(
    regime: str = "new",
    current_user: User = Depends(get_current_user),
):
    """Return income tax slabs for the given regime."""
    if regime == "new":
        return {
            "regime": "new",
            "assessment_year": "2024-25",
            "standard_deduction": 75000,
            "slabs": [
                {"from": 0, "to": 300000, "rate": 0},
                {"from": 300001, "to": 600000, "rate": 5},
                {"from": 600001, "to": 900000, "rate": 10},
                {"from": 900001, "to": 1200000, "rate": 15},
                {"from": 1200001, "to": 1500000, "rate": 20},
                {"from": 1500001, "to": None, "rate": 30},
            ],
            "rebate_87a": {"limit": 700000, "max_rebate": 25000},
        }
    else:
        return {
            "regime": "old",
            "assessment_year": "2024-25",
            "standard_deduction": 50000,
            "slabs": [
                {"from": 0, "to": 250000, "rate": 0},
                {"from": 250001, "to": 500000, "rate": 5},
                {"from": 500001, "to": 1000000, "rate": 20},
                {"from": 1000001, "to": None, "rate": 30},
            ],
            "rebate_87a": {"limit": 500000, "max_rebate": 12500},
            "deductions": {
                "80C": "Up to ₹1,50,000",
                "80D": "Health insurance premium",
                "80G": "Charitable donations",
                "HRA": "House rent allowance exemption",
            },
        }
