"""Tests for the GST calculation engine."""
import pytest
from decimal import Decimal
from services.gst_service import calculate_gst, calculate_gst_api, get_gst_rate_for_hsn
from models.models import GSTType
from models.schemas import GSTCalculationRequest


class TestCalculateGST:
    def test_cgst_18_percent(self):
        result = calculate_gst(Decimal("100000"), Decimal("18"), GSTType.CGST)
        assert result["taxable_amount"] == Decimal("100000.00")
        assert result["cgst_amount"] == Decimal("9000.00")
        assert result["sgst_amount"] == Decimal("9000.00")
        assert result["igst_amount"] == Decimal("0.00")
        assert result["total_gst"] == Decimal("18000.00")
        assert result["total_amount"] == Decimal("118000.00")

    def test_igst_18_percent(self):
        result = calculate_gst(Decimal("50000"), Decimal("18"), GSTType.IGST)
        assert result["igst_amount"] == Decimal("9000.00")
        assert result["cgst_amount"] == Decimal("0.00")
        assert result["sgst_amount"] == Decimal("0.00")
        assert result["total_gst"] == Decimal("9000.00")

    def test_exempt_gst(self):
        result = calculate_gst(Decimal("80000"), Decimal("0"), GSTType.exempt)
        assert result["total_gst"] == Decimal("0.00")
        assert result["total_amount"] == Decimal("80000.00")

    def test_zero_rate(self):
        result = calculate_gst(Decimal("10000"), Decimal("0"), GSTType.CGST)
        assert result["total_gst"] == Decimal("0.00")

    def test_5_percent(self):
        result = calculate_gst(Decimal("100000"), Decimal("5"), GSTType.CGST)
        assert result["cgst_amount"] == Decimal("2500.00")
        assert result["sgst_amount"] == Decimal("2500.00")
        assert result["total_gst"] == Decimal("5000.00")

    def test_gst_inclusive_pricing(self):
        """When price includes GST, taxable amount should be lower."""
        result = calculate_gst(Decimal("118000"), Decimal("18"), GSTType.CGST, is_inclusive=True)
        assert result["taxable_amount"] == pytest.approx(Decimal("100000.00"), rel=Decimal("0.01"))
        assert result["total_gst"] == pytest.approx(Decimal("18000.00"), rel=Decimal("0.01"))

    def test_0_25_percent(self):
        result = calculate_gst(Decimal("100000"), Decimal("0.25"), GSTType.CGST)
        assert result["total_gst"] == Decimal("250.00")

    def test_28_percent_luxury(self):
        result = calculate_gst(Decimal("200000"), Decimal("28"), GSTType.IGST)
        assert result["igst_amount"] == Decimal("56000.00")
        assert result["total_amount"] == Decimal("256000.00")

    def test_rounding(self):
        """Test that rounding works correctly for fractional amounts."""
        result = calculate_gst(Decimal("33333"), Decimal("18"), GSTType.CGST)
        # Should be rounded to 2 decimal places
        assert result["total_gst"] == round(Decimal("33333") * Decimal("0.18"), 2)

    def test_invalid_amount_raises(self):
        with pytest.raises((ValueError, Exception)):
            calculate_gst(Decimal("-1000"), Decimal("18"), GSTType.CGST)


class TestGSTApi:
    def test_api_cgst_calculation(self, client, auth_headers):
        res = client.post("/api/v1/gst/calculate", json={
            "amount": 100000,
            "gst_rate": 18,
            "gst_type": "CGST",
            "is_inclusive": False,
        }, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert float(data["cgst_amount"]) == 9000.0
        assert float(data["sgst_amount"]) == 9000.0
        assert float(data["total_gst"]) == 18000.0
        assert float(data["total_amount"]) == 118000.0
        assert float(data["cgst_rate"]) == 9.0
        assert float(data["sgst_rate"]) == 9.0

    def test_api_igst_calculation(self, client, auth_headers):
        res = client.post("/api/v1/gst/calculate", json={
            "amount": 50000,
            "gst_rate": 12,
            "gst_type": "IGST",
            "is_inclusive": False,
        }, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert float(data["igst_amount"]) == 6000.0
        assert float(data["igst_rate"]) == 12.0

    def test_api_rates_list(self, client, auth_headers):
        res = client.get("/api/v1/gst/rates", headers=auth_headers)
        assert res.status_code == 200
        assert 18 in res.json()["rates"]
        assert 28 in res.json()["rates"]


class TestHSNLookup:
    def test_known_hsn(self):
        rate = get_gst_rate_for_hsn("8471")
        assert rate == Decimal("18")

    def test_unknown_hsn(self):
        rate = get_gst_rate_for_hsn("9999")  # services default
        assert rate is not None

    def test_nonexistent_hsn(self):
        rate = get_gst_rate_for_hsn("0000")
        assert rate is None
