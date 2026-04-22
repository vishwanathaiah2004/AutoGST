"""Tests for transaction CRUD endpoints."""
import pytest


class TestCreateTransaction:
    def test_create_income(self, client, auth_headers, sample_transaction_payload):
        res = client.post("/api/v1/transactions", json=sample_transaction_payload, headers=auth_headers)
        assert res.status_code == 201
        data = res.json()
        assert data["description"] == sample_transaction_payload["description"]
        assert data["transaction_type"] == "income"
        assert float(data["amount"]) == 50000
        # GST should be computed
        assert float(data["total_gst"]) == pytest.approx(9000.0, rel=1e-2)
        assert float(data["total_amount"]) == pytest.approx(59000.0, rel=1e-2)
        assert float(data["cgst_amount"]) == pytest.approx(4500.0, rel=1e-2)
        assert float(data["sgst_amount"]) == pytest.approx(4500.0, rel=1e-2)

    def test_create_expense(self, client, auth_headers):
        res = client.post("/api/v1/transactions", json={
            "description": "Office rent",
            "amount": 35000,
            "transaction_type": "expense",
            "transaction_date": "2024-11-05",
            "gst_type": "CGST",
            "gst_rate": 18,
        }, headers=auth_headers)
        assert res.status_code == 201
        assert res.json()["transaction_type"] == "expense"

    def test_create_exempt_transaction(self, client, auth_headers):
        res = client.post("/api/v1/transactions", json={
            "description": "Employee salary",
            "amount": 80000,
            "transaction_type": "expense",
            "transaction_date": "2024-11-30",
            "gst_type": "exempt",
            "gst_rate": 0,
        }, headers=auth_headers)
        assert res.status_code == 201
        assert float(res.json()["total_gst"]) == 0.0

    def test_create_igst_transaction(self, client, auth_headers):
        res = client.post("/api/v1/transactions", json={
            "description": "Interstate sale",
            "amount": 100000,
            "transaction_type": "income",
            "transaction_date": "2024-11-15",
            "gst_type": "IGST",
            "gst_rate": 18,
        }, headers=auth_headers)
        assert res.status_code == 201
        data = res.json()
        assert float(data["igst_amount"]) == pytest.approx(18000.0, rel=1e-2)
        assert float(data["cgst_amount"]) == 0.0

    def test_create_invalid_gst_rate(self, client, auth_headers):
        res = client.post("/api/v1/transactions", json={
            "description": "Bad rate",
            "amount": 1000,
            "transaction_type": "income",
            "transaction_date": "2024-11-01",
            "gst_type": "CGST",
            "gst_rate": 15,  # Invalid rate
        }, headers=auth_headers)
        assert res.status_code == 422

    def test_create_requires_auth(self, client, sample_transaction_payload):
        res = client.post("/api/v1/transactions", json=sample_transaction_payload)
        assert res.status_code in (401, 403)


class TestListTransactions:
    def test_list_empty(self, client, auth_headers):
        res = client.get("/api/v1/transactions", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["total"] == 0

    def test_list_with_data(self, client, auth_headers, sample_transaction_payload):
        # Create 3 transactions
        for i in range(3):
            payload = {**sample_transaction_payload, "description": f"Service {i}"}
            client.post("/api/v1/transactions", json=payload, headers=auth_headers)

        res = client.get("/api/v1/transactions", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["total"] == 3

    def test_list_filter_by_type(self, client, auth_headers, sample_transaction_payload):
        client.post("/api/v1/transactions", json=sample_transaction_payload, headers=auth_headers)
        client.post("/api/v1/transactions", json={
            **sample_transaction_payload,
            "transaction_type": "expense",
            "description": "Rent",
        }, headers=auth_headers)

        res = client.get("/api/v1/transactions?transaction_type=income", headers=auth_headers)
        assert res.status_code == 200
        items = res.json()["items"]
        assert all(t["transaction_type"] == "income" for t in items)

    def test_list_pagination(self, client, auth_headers, sample_transaction_payload):
        for i in range(5):
            client.post("/api/v1/transactions", json={**sample_transaction_payload, "description": f"T{i}"}, headers=auth_headers)

        res = client.get("/api/v1/transactions?page=1&size=2", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) == 2
        assert data["pages"] >= 3


class TestUpdateTransaction:
    def test_update_description(self, client, auth_headers, sample_transaction_payload):
        create = client.post("/api/v1/transactions", json=sample_transaction_payload, headers=auth_headers)
        txn_id = create.json()["id"]

        res = client.put(f"/api/v1/transactions/{txn_id}", json={"description": "Updated desc"}, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["description"] == "Updated desc"

    def test_update_amount_recalculates_gst(self, client, auth_headers, sample_transaction_payload):
        create = client.post("/api/v1/transactions", json=sample_transaction_payload, headers=auth_headers)
        txn_id = create.json()["id"]

        res = client.put(f"/api/v1/transactions/{txn_id}", json={"amount": 100000}, headers=auth_headers)
        assert res.status_code == 200
        assert float(res.json()["total_gst"]) == pytest.approx(18000.0, rel=1e-2)

    def test_update_not_found(self, client, auth_headers):
        res = client.put("/api/v1/transactions/99999", json={"description": "x"}, headers=auth_headers)
        assert res.status_code == 404


class TestDeleteTransaction:
    def test_delete_success(self, client, auth_headers, sample_transaction_payload):
        create = client.post("/api/v1/transactions", json=sample_transaction_payload, headers=auth_headers)
        txn_id = create.json()["id"]

        res = client.delete(f"/api/v1/transactions/{txn_id}", headers=auth_headers)
        assert res.status_code == 200

        # Confirm deleted
        get = client.get(f"/api/v1/transactions/{txn_id}", headers=auth_headers)
        assert get.status_code == 404

    def test_delete_not_found(self, client, auth_headers):
        res = client.delete("/api/v1/transactions/99999", headers=auth_headers)
        assert res.status_code == 404
