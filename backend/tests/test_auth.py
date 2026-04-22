"""Tests for authentication endpoints."""
import pytest


class TestRegister:
    def test_register_success(self, client):
        res = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "full_name": "New User",
            "password": "NewPass@123",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["success"] is True
        assert data["data"]["email"] == "new@example.com"
        assert "hashed_password" not in data["data"]

    def test_register_duplicate_email(self, client, registered_user):
        res = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "full_name": "Duplicate",
            "password": "Test@1234",
        })
        assert res.status_code == 409

    def test_register_invalid_email(self, client):
        res = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "full_name": "Bad",
            "password": "Pass@1234",
        })
        assert res.status_code == 422

    def test_register_short_password(self, client):
        res = client.post("/api/v1/auth/register", json={
            "email": "short@example.com",
            "full_name": "Short Pass",
            "password": "abc",
        })
        assert res.status_code == 422


class TestLogin:
    def test_login_success(self, client, registered_user):
        res = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test@1234",
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"

    def test_login_wrong_password(self, client, registered_user):
        res = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword",
        })
        assert res.status_code == 401

    def test_login_unknown_email(self, client):
        res = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "Test@1234",
        })
        assert res.status_code == 401


class TestMe:
    def test_get_me(self, client, auth_headers):
        res = client.get("/api/v1/auth/me", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["email"] == "test@example.com"

    def test_get_me_no_token(self, client):
        res = client.get("/api/v1/auth/me")
        assert res.status_code in (401, 403)

    def test_get_me_invalid_token(self, client):
        res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert res.status_code == 401
