import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

from models.models import GSTType
from models.schemas import GSTCalculationRequest, GSTCalculationResponse

logger = logging.getLogger("autogst.gst_engine")

# GST rate mapping
VALID_GST_RATES = [Decimal("0"), Decimal("0.25"), Decimal("3"), Decimal("5"),
                   Decimal("12"), Decimal("18"), Decimal("28")]

# HSN code GST rate reference (sample)
HSN_GST_MAP = {
    "0101": Decimal("0"),    # Live animals
    "1001": Decimal("0"),    # Wheat
    "2204": Decimal("28"),   # Wine
    "8471": Decimal("18"),   # Computers
    "9403": Decimal("18"),   # Furniture
    "3004": Decimal("12"),   # Medicines
    "6101": Decimal("5"),    # Clothing < 1000
    "9999": Decimal("18"),   # Services (default)
}


def round_gst(value: Decimal) -> Decimal:
    """Round to 2 decimal places using ROUND_HALF_UP."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_gst(
    amount: Decimal,
    gst_rate: Decimal,
    gst_type: GSTType,
    is_inclusive: bool = False,
) -> Dict[str, Decimal]:
    """
    Core GST calculation engine.
    Returns breakdown of CGST, SGST, IGST, total_gst, taxable_amount, total_amount.
    """
    try:
        half_rate = gst_rate / Decimal("2")

        if is_inclusive:
            # GST is included in the amount — extract it
            taxable_amount = round_gst(amount * Decimal("100") / (Decimal("100") + gst_rate))
            total_gst = round_gst(amount - taxable_amount)
        else:
            taxable_amount = round_gst(amount)
            total_gst = round_gst(taxable_amount * gst_rate / Decimal("100"))

        cgst_amount = Decimal("0")
        sgst_amount = Decimal("0")
        igst_amount = Decimal("0")

        if gst_type == GSTType.IGST:
            igst_amount = total_gst
        elif gst_type == GSTType.CGST:
            cgst_amount = round_gst(taxable_amount * half_rate / Decimal("100"))
            sgst_amount = round_gst(taxable_amount * half_rate / Decimal("100"))
            total_gst = cgst_amount + sgst_amount
        elif gst_type == GSTType.SGST:
            cgst_amount = round_gst(taxable_amount * half_rate / Decimal("100"))
            sgst_amount = round_gst(taxable_amount * half_rate / Decimal("100"))
            total_gst = cgst_amount + sgst_amount
        elif gst_type == GSTType.UTGST:
            cgst_amount = round_gst(taxable_amount * half_rate / Decimal("100"))
            sgst_amount = round_gst(taxable_amount * half_rate / Decimal("100"))
            total_gst = cgst_amount + sgst_amount
        elif gst_type == GSTType.exempt:
            total_gst = Decimal("0")

        total_amount = taxable_amount + total_gst

        result = {
            "taxable_amount": taxable_amount,
            "cgst_amount": cgst_amount,
            "sgst_amount": sgst_amount,
            "igst_amount": igst_amount,
            "total_gst": total_gst,
            "total_amount": total_amount,
        }
        logger.debug(
            "GST calculated: amount=%.2f rate=%.2f type=%s → gst=%.2f total=%.2f",
            amount, gst_rate, gst_type, total_gst, total_amount
        )
        return result
    except Exception as e:
        logger.error("GST calculation error: %s", str(e))
        raise ValueError(f"GST calculation failed: {str(e)}")


def calculate_gst_api(request: GSTCalculationRequest) -> GSTCalculationResponse:
    """API-level GST calculator."""
    result = calculate_gst(
        request.amount, request.gst_rate, request.gst_type, request.is_inclusive
    )
    half_rate = request.gst_rate / Decimal("2")

    return GSTCalculationResponse(
        taxable_amount=result["taxable_amount"],
        gst_rate=request.gst_rate,
        cgst_rate=half_rate if request.gst_type != GSTType.IGST else None,
        sgst_rate=half_rate if request.gst_type != GSTType.IGST else None,
        igst_rate=request.gst_rate if request.gst_type == GSTType.IGST else None,
        cgst_amount=result["cgst_amount"],
        sgst_amount=result["sgst_amount"],
        igst_amount=result["igst_amount"],
        total_gst=result["total_gst"],
        total_amount=result["total_amount"],
        gst_type=request.gst_type,
    )


def get_gst_rate_for_hsn(hsn_code: str) -> Optional[Decimal]:
    """Look up GST rate by HSN/SAC code."""
    return HSN_GST_MAP.get(hsn_code[:4])


def compute_gstr1_summary(transactions: list) -> Dict[str, Any]:
    """Aggregate transactions into GSTR-1 format."""
    b2b = []  # Business to business
    b2c = []  # Business to consumer

    total_taxable = Decimal("0")
    total_cgst = Decimal("0")
    total_sgst = Decimal("0")
    total_igst = Decimal("0")

    for txn in transactions:
        if txn.transaction_type.value != "income":
            continue
        entry = {
            "invoice_number": txn.invoice_number or f"INV-{txn.id}",
            "invoice_date": str(txn.transaction_date),
            "party_name": txn.party_name or "Unknown",
            "party_gstin": txn.party_gstin,
            "taxable_value": float(txn.taxable_amount),
            "cgst": float(txn.cgst_amount),
            "sgst": float(txn.sgst_amount),
            "igst": float(txn.igst_amount),
            "total_tax": float(txn.total_gst),
            "total_invoice_value": float(txn.total_amount),
        }
        if txn.party_gstin:
            b2b.append(entry)
        else:
            b2c.append(entry)

        total_taxable += txn.taxable_amount or Decimal("0")
        total_cgst += txn.cgst_amount or Decimal("0")
        total_sgst += txn.sgst_amount or Decimal("0")
        total_igst += txn.igst_amount or Decimal("0")

    return {
        "b2b_invoices": b2b,
        "b2c_invoices": b2c,
        "summary": {
            "total_taxable_value": float(total_taxable),
            "total_cgst": float(total_cgst),
            "total_sgst": float(total_sgst),
            "total_igst": float(total_igst),
            "total_tax": float(total_cgst + total_sgst + total_igst),
        },
    }


def compute_gstr3b_summary(transactions: list) -> Dict[str, Any]:
    """Aggregate into GSTR-3B format — output tax and input tax credit."""
    output_cgst = Decimal("0")
    output_sgst = Decimal("0")
    output_igst = Decimal("0")
    input_cgst = Decimal("0")
    input_sgst = Decimal("0")
    input_igst = Decimal("0")
    output_taxable = Decimal("0")
    input_taxable = Decimal("0")

    for txn in transactions:
        if txn.transaction_type.value == "income":
            output_cgst += txn.cgst_amount or Decimal("0")
            output_sgst += txn.sgst_amount or Decimal("0")
            output_igst += txn.igst_amount or Decimal("0")
            output_taxable += txn.taxable_amount or Decimal("0")
        else:
            input_cgst += txn.cgst_amount or Decimal("0")
            input_sgst += txn.sgst_amount or Decimal("0")
            input_igst += txn.igst_amount or Decimal("0")
            input_taxable += txn.taxable_amount or Decimal("0")

    total_output = output_cgst + output_sgst + output_igst
    total_input_credit = input_cgst + input_sgst + input_igst
    net_liability = max(Decimal("0"), total_output - total_input_credit)

    return {
        "3_1_outward_supplies": {
            "taxable_value": float(output_taxable),
            "integrated_tax": float(output_igst),
            "central_tax": float(output_cgst),
            "state_ut_tax": float(output_sgst),
        },
        "4_input_tax_credit": {
            "integrated_tax": float(input_igst),
            "central_tax": float(input_cgst),
            "state_ut_tax": float(input_sgst),
        },
        "6_payment_of_tax": {
            "total_output_tax": float(total_output),
            "total_itc": float(total_input_credit),
            "net_payable": float(net_liability),
        },
    }
