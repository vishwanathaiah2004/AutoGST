import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.models import TaxCalculation
from models.schemas import TaxCalculationRequest, TaxCalculationResponse

logger = logging.getLogger("autogst.tax")


def round_tax(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ─── Tax Slabs ───────────────────────────────────────────────────────────────

NEW_REGIME_SLABS_2024 = [
    (Decimal("300000"), Decimal("0")),
    (Decimal("600000"), Decimal("5")),
    (Decimal("900000"), Decimal("10")),
    (Decimal("1200000"), Decimal("15")),
    (Decimal("1500000"), Decimal("20")),
    (Decimal("9999999999"), Decimal("30")),
]

OLD_REGIME_SLABS = [
    (Decimal("250000"), Decimal("0")),
    (Decimal("500000"), Decimal("5")),
    (Decimal("1000000"), Decimal("20")),
    (Decimal("9999999999"), Decimal("30")),
]

STANDARD_DEDUCTION = Decimal("75000")  # FY 2024-25 (new regime), 50000 old
OLD_STANDARD_DEDUCTION = Decimal("50000")


def compute_tax_on_slabs(income: Decimal, slabs: list) -> tuple:
    """Compute income tax using progressive slabs. Returns (tax, breakdown)."""
    tax = Decimal("0")
    breakdown = []
    prev_limit = Decimal("0")

    for limit, rate in slabs:
        if income <= prev_limit:
            break
        slab_income = min(income, limit) - prev_limit
        slab_tax = round_tax(slab_income * rate / Decimal("100"))
        breakdown.append({
            "slab": f"₹{prev_limit:,.0f} – ₹{min(income, limit):,.0f}",
            "rate": float(rate),
            "taxable_in_slab": float(slab_income),
            "tax_in_slab": float(slab_tax),
        })
        tax += slab_tax
        prev_limit = limit

    return tax, breakdown


def compute_surcharge(income: Decimal, tax: Decimal) -> Decimal:
    """Compute surcharge based on income level."""
    if income <= Decimal("5000000"):
        return Decimal("0")
    elif income <= Decimal("10000000"):
        return round_tax(tax * Decimal("10") / Decimal("100"))
    elif income <= Decimal("20000000"):
        return round_tax(tax * Decimal("15") / Decimal("100"))
    elif income <= Decimal("50000000"):
        return round_tax(tax * Decimal("25") / Decimal("100"))
    else:
        return round_tax(tax * Decimal("37") / Decimal("100"))


def calculate_income_tax(request: TaxCalculationRequest) -> TaxCalculationResponse:
    """Calculate Indian income tax under old or new regime."""
    try:
        gross = request.gross_income

        if request.regime == "new":
            # New regime: standard deduction of ₹75,000, no other deductions
            std_deduction = min(STANDARD_DEDUCTION, request.salary_income) if request.salary_income > 0 else Decimal("0")
            total_deductions = std_deduction
            taxable_income = max(Decimal("0"), gross - total_deductions)
            slabs = NEW_REGIME_SLABS_2024

        else:  # old regime
            std_deduction = min(OLD_STANDARD_DEDUCTION, request.salary_income) if request.salary_income > 0 else Decimal("0")
            sec_80c = min(request.section_80c, Decimal("150000"))
            sec_80d = request.section_80d
            sec_80g = request.section_80g
            hra = request.hra_exemption
            total_deductions = std_deduction + sec_80c + sec_80d + sec_80g + hra
            taxable_income = max(Decimal("0"), gross - total_deductions)
            slabs = OLD_REGIME_SLABS

        income_tax, slab_breakdown = compute_tax_on_slabs(taxable_income, slabs)

        # Rebate 87A: if taxable income <= 7 lakh (new regime) or 5 lakh (old)
        rebate_limit = Decimal("700000") if request.regime == "new" else Decimal("500000")
        if taxable_income <= rebate_limit:
            rebate = min(income_tax, Decimal("25000"))
            income_tax = max(Decimal("0"), income_tax - rebate)

        surcharge = compute_surcharge(taxable_income, income_tax)
        cess = round_tax((income_tax + surcharge) * Decimal("4") / Decimal("100"))
        total_liability = income_tax + surcharge + cess

        effective_rate = float(total_liability / gross * 100) if gross > 0 else 0.0

        # Comparison: compute the other regime too
        comparison = None
        try:
            other_regime = "old" if request.regime == "new" else "new"
            other_req = TaxCalculationRequest(
                assessment_year=request.assessment_year,
                regime=other_regime,
                gross_income=request.gross_income,
                salary_income=request.salary_income,
                business_income=request.business_income,
                other_income=request.other_income,
                section_80c=request.section_80c,
                section_80d=request.section_80d,
                section_80g=request.section_80g,
                hra_exemption=request.hra_exemption,
            )
            other_result = calculate_income_tax(other_req)
            comparison = {
                "regime": other_regime,
                "total_tax_liability": float(other_result.total_tax_liability),
                "effective_tax_rate": other_result.effective_tax_rate,
                "savings": float(abs(total_liability - other_result.total_tax_liability)),
                "recommended": "current" if total_liability <= other_result.total_tax_liability else "other",
            }
        except Exception:
            pass

        return TaxCalculationResponse(
            assessment_year=request.assessment_year,
            regime=request.regime,
            gross_income=gross,
            total_deductions=total_deductions,
            taxable_income=taxable_income,
            income_tax=income_tax,
            surcharge=surcharge,
            cess=cess,
            total_tax_liability=total_liability,
            effective_tax_rate=round(effective_rate, 2),
            slab_breakdown=slab_breakdown,
            comparison=comparison,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Tax calculation error: %s", str(e))
        raise HTTPException(500, f"Tax calculation failed: {str(e)}")


def save_tax_calculation(db: Session, user_id: int, request: TaxCalculationRequest, result: TaxCalculationResponse) -> TaxCalculation:
    """Persist tax calculation to database."""
    try:
        calc = TaxCalculation(
            user_id=user_id,
            assessment_year=request.assessment_year,
            regime=request.regime,
            gross_income=request.gross_income,
            salary_income=request.salary_income,
            business_income=request.business_income,
            other_income=request.other_income,
            standard_deduction=result.total_deductions,
            section_80c=request.section_80c,
            section_80d=request.section_80d,
            section_80g=request.section_80g,
            hra_exemption=request.hra_exemption,
            total_deductions=result.total_deductions,
            taxable_income=result.taxable_income,
            income_tax=result.income_tax,
            surcharge=result.surcharge,
            cess=result.cess,
            total_tax_liability=result.total_tax_liability,
            effective_tax_rate=result.effective_tax_rate,
            calculation_details={
                "slab_breakdown": result.slab_breakdown,
                "comparison": result.comparison,
            },
        )
        db.add(calc)
        db.commit()
        db.refresh(calc)
        return calc
    except Exception as e:
        db.rollback()
        logger.error("Failed to save tax calculation: %s", str(e))
        raise
