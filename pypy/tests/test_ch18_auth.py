# ch18 section 6 — Testing Authentication
# Verbatim from chapter 18 section 6 — no patches applied. Created blind.

from tina4_python.test import Test, assert_equal, assert_true, assert_not_none
import json

class AuthTest(Test):

    def test_login_with_valid_credentials(self):
        resp = self.post("/api/auth/login", {
            "email": "admin@example.com",
            "password": "correct-password"
        })

        assert_equal(resp.status_code, 200, "Login should succeed")

        body = json.loads(resp.body)
        assert_not_none(body.get("token"), "Should return a JWT token")
        assert_true(len(body["token"]) > 50, "Token should be a substantial string")

    def test_login_with_invalid_password(self):
        resp = self.post("/api/auth/login", {
            "email": "admin@example.com",
            "password": "wrong-password"
        })

        assert_equal(resp.status_code, 401, "Should reject invalid password")

    def test_login_with_missing_fields(self):
        resp = self.post("/api/auth/login", {
            "email": "admin@example.com"
        })

        assert_true(
            resp.status_code in (400, 401),
            "Should reject missing password"
        )

    def test_protected_route_without_token(self):
        resp = self.get("/api/profile")

        assert_equal(resp.status_code, 401, "Should reject unauthenticated request")

    def test_protected_route_with_valid_token(self):
        # Login first to get a token
        login_resp = self.post("/api/auth/login", {
            "email": "admin@example.com",
            "password": "correct-password"
        })
        login_body = json.loads(login_resp.body)
        token = login_body["token"]

        # Access protected route with token
        resp = self.get("/api/profile", headers={
            "Authorization": f"Bearer {token}"
        })

        assert_equal(resp.status_code, 200, "Should allow authenticated request")

        body = json.loads(resp.body)
        assert_equal(body["user"]["email"], "admin@example.com", "Should return user data")

    def test_protected_route_with_invalid_token(self):
        resp = self.get("/api/profile", headers={
            "Authorization": "Bearer invalid.token.here"
        })

        assert_equal(resp.status_code, 401, "Should reject invalid token")
