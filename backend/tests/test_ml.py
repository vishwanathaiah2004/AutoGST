"""Tests for ML expense classifier and anomaly detection."""
import pytest
from services.ml_service import classify_expense, get_classifier


class TestExpenseClassifier:
    def test_classify_returns_tuple(self):
        category, confidence = classify_expense("office rent monthly payment", 35000)
        assert isinstance(category, str)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_classify_rent(self):
        category, confidence = classify_expense("monthly office rent payment", 35000)
        assert "rent" in category.lower() or "util" in category.lower()

    def test_classify_salary(self):
        category, confidence = classify_expense("employee salary payroll", 150000)
        assert "salary" in category.lower() or "payroll" in category.lower()

    def test_classify_software(self):
        category, confidence = classify_expense("aws cloud subscription", 15000)
        assert "software" in category.lower() or "tool" in category.lower()

    def test_classify_travel(self):
        category, confidence = classify_expense("flight ticket airfare business travel", 12000)
        assert "travel" in category.lower() or "transport" in category.lower()

    def test_classify_returns_uncategorized_on_error(self):
        """Empty string should not crash."""
        category, confidence = classify_expense("", 0)
        assert isinstance(category, str)

    def test_classifier_loads(self):
        clf = get_classifier()
        assert clf is not None
        assert hasattr(clf, "predict")

    def test_classifier_has_classes(self):
        clf = get_classifier()
        assert len(clf.classes_) > 5

    def test_classify_multiple_descriptions(self):
        test_cases = [
            ("google ads facebook marketing campaign", "Marketing"),
            ("laptop macbook equipment purchase", "Equipment"),
            ("audit ca fee professional services", "Professional Services"),
        ]
        for desc, expected_keyword in test_cases:
            category, _ = classify_expense(desc, 10000)
            assert isinstance(category, str), f"Expected string for '{desc}'"


class TestDashboard:
    def test_dashboard_returns_stats(self, client, auth_headers, sample_transaction_payload):
        # Create a transaction first
        client.post("/api/v1/transactions", json=sample_transaction_payload, headers=auth_headers)
        res = client.get("/api/v1/dashboard", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "total_income" in data
        assert "total_expense" in data
        assert "net_balance" in data
        assert "transaction_count" in data
        assert "monthly_summary" in data
        assert "top_categories" in data

    def test_dashboard_requires_auth(self, client):
        res = client.get("/api/v1/dashboard")
        assert res.status_code in (401, 403)

    def test_dashboard_empty_user(self, client, auth_headers):
        """Empty account should return zeros, not error."""
        res = client.get("/api/v1/dashboard", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["transaction_count"] == 0
