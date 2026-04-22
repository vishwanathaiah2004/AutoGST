"""Tests for the Indian income tax calculator."""
import pytest
from decimal import Decimal
from services.tax_service import calculate_income_tax
from models.schemas import TaxCalculationRequest


def make_req(**kwargs) -> TaxCalculationRequest:
    defaults = {
        "assessment_year": "2024-25",
        "regime": "new",
        "gross_income": Decimal("0"),
        "salary_income": Decimal("0"),
        "business_income": Decimal("0"),
        "other_income": Decimal("0"),
        "section_80c": Decimal("0"),
        "section_80d": Decimal("0"),
        "section_80g": Decimal("0"),
        "hra_exemption": Decimal("0"),
    }
    defaults.update(kwargs)
    return TaxCalculationRequest(**defaults)


class TestNewRegime:
    def test_zero_income(self):
        result = calculate_income_tax(make_req(gross_income=Decimal("0"), regime="new"))
        assert result.total_tax_liability == Decimal("0.00")

    def test_below_3_lakh_no_tax(self):
        """Income below ₹3L has 0% tax in new regime."""
        result = calculate_income_tax(make_req(gross_income=Decimal("250000"), regime="new"))
        assert result.total_tax_liability == Decimal("0.00")

    def test_rebate_87a_new_regime(self):
        """Income up to ₹7L gets full rebate in new regime."""
        result = calculate_income_tax(make_req(
            gross_income=Decimal("700000"),
            salary_income=Decimal("700000"),
            regime="new"
        ))
        assert result.total_tax_liability == Decimal("0.00")

    def test_above_rebate_limit(self):
        """Income above ₹7L should have tax liability."""
        result = calculate_income_tax(make_req(
            gross_income=Decimal("800000"),
            salary_income=Decimal("800000"),
            regime="new"
        ))
        assert result.total_tax_liability > Decimal("0")

    def test_standard_deduction_applied(self):
        """New regime should apply ₹75,000 standard deduction for salaried."""
        result = calculate_income_tax(make_req(
            gross_income=Decimal("1000000"),
            salary_income=Decimal("1000000"),
            regime="new"
        ))
        assert result.total_deductions == Decimal("75000")
        assert result.taxable_income == Decimal("925000")

    def test_30_percent_slab_applies(self):
        """Income above ₹15L should hit 30% slab."""
        result = calculate_income_tax(make_req(
            gross_income=Decimal("2000000"),
            salary_income=Decimal("2000000"),
            regime="new"
        ))
        assert result.income_tax > Decimal("100000")

    def test_cess_is_4_percent(self):
        result = calculate_income_tax(make_req(
            gross_income=Decimal("1500000"),
            salary_income=Decimal("1500000"),
            regime="new"
        ))
        expected_cess = round((result.income_tax + result.surcharge) * Decimal("0.04"), 2)
        assert abs(result.cess - expected_cess) < Decimal("1")

    def test_effective_rate_is_percentage(self):
        result = calculate_income_tax(make_req(
            gross_income=Decimal("1200000"),
            salary_income=Decimal("1200000"),
            regime="new"
        ))
        assert 0 <= result.effective_tax_rate <= 100


class TestOldRegime:
    def test_section_80c_deduction(self):
        result = calculate_income_tax(make_req(
            gross_income=Decimal("1000000"),
            salary_income=Decimal("1000000"),
            regime="old",
            section_80c=Decimal("150000"),
        ))
        # Deductions should include 80C + standard deduction
        assert result.total_deductions >= Decimal("150000")

    def test_80c_capped_at_1_5_lakh(self):
        """80C is capped at ₹1.5L even if more is claimed."""
        result_capped = calculate_income_tax(make_req(
            gross_income=Decimal("1000000"),
            salary_income=Decimal("1000000"),
            regime="old",
            section_80c=Decimal("200000"),
        ))
        result_limit = calculate_income_tax(make_req(
            gross_income=Decimal("1000000"),
            salary_income=Decimal("1000000"),
            regime="old",
            section_80c=Decimal("150000"),
        ))
        assert result_capped.taxable_income == result_limit.taxable_income

    def test_rebate_87a_old_regime(self):
        """Taxable income <= ₹5L gets rebate in old regime."""
        result = calculate_income_tax(make_req(
            gross_income=Decimal("500000"),
            salary_income=Decimal("500000"),
            regime="old",
        ))
        assert result.total_tax_liability == Decimal("0.00")

    def test_old_regime_multiple_deductions(self):
        result = calculate_income_tax(make_req(
            gross_income=Decimal("1500000"),
            salary_income=Decimal("1500000"),
            regime="old",
            section_80c=Decimal("150000"),
            section_80d=Decimal("25000"),
            section_80g=Decimal("10000"),
            hra_exemption=Decimal("120000"),
        ))
        assert result.total_deductions >= Decimal("305000")
        assert result.taxable_income < Decimal("1500000")


class TestRegimeComparison:
    def test_comparison_included(self):
        result = calculate_income_tax(make_req(
            gross_income=Decimal("1200000"),
            salary_income=Decimal("1200000"),
            regime="new",
        ))
        assert result.comparison is not None
        assert result.comparison["regime"] == "old"
        assert "savings" in result.comparison
        assert "recommended" in result.comparison

    def test_recommended_is_valid(self):
        result = calculate_income_tax(make_req(
            gross_income=Decimal("1200000"),
            salary_income=Decimal("1200000"),
            regime="new",
        ))
        assert result.comparison["recommended"] in ("current", "other")


class TestTaxApiEndpoint:
    def test_api_new_regime(self, client, auth_headers):
        res = client.post("/api/v1/tax/calculate", json={
            "regime": "new",
            "gross_income": 1200000,
            "salary_income": 1200000,
            "assessment_year": "2024-25",
        }, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "total_tax_liability" in data
        assert "slab_breakdown" in data
        assert "comparison" in data

    def test_api_old_regime(self, client, auth_headers):
        res = client.post("/api/v1/tax/calculate", json={
            "regime": "old",
            "gross_income": 1200000,
            "salary_income": 1200000,
            "section_80c": 150000,
            "assessment_year": "2024-25",
        }, headers=auth_headers)
        assert res.status_code == 200

    def test_api_invalid_regime(self, client, auth_headers):
        res = client.post("/api/v1/tax/calculate", json={
            "regime": "invalid",
            "gross_income": 1000000,
        }, headers=auth_headers)
        assert res.status_code == 422

    def test_api_slabs_new(self, client, auth_headers):
        res = client.get("/api/v1/tax/slabs?regime=new", headers=auth_headers)
        assert res.status_code == 200
        assert len(res.json()["slabs"]) > 0

    def test_api_slabs_old(self, client, auth_headers):
        res = client.get("/api/v1/tax/slabs?regime=old", headers=auth_headers)
        assert res.status_code == 200
        assert "deductions" in res.json()
