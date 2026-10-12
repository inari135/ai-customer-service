"""
测试 auth.py：密码哈希、JWT、注册、登录、鉴权
"""
import pytest
from fastapi import status

from backend.auth import hash_password, verify_password, create_token, verify_token


# ============================================================
# 纯函数测试：密码哈希
# ============================================================

class TestPasswordHashing:
    """hash_password / verify_password"""

    def test_hash_and_verify_success(self):
        """正常哈希 → 验证成功"""
        pw = "secure_password_123"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_verify_wrong_password(self):
        """错误密码 → 验证失败"""
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_verify_invalid_hash_format(self):
        """哈希格式损坏 → 返回 False 不抛异常"""
        assert verify_password("anything", "bad_hash_no_dollar") is False

    def test_verify_empty_hash(self):
        """空哈希 → 返回 False"""
        assert verify_password("anything", "") is False

    def test_hash_generates_unique_salts(self):
        """相同密码两次哈希结果不同（盐不同）"""
        pw = "same_password"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2
        # 但都能验证
        assert verify_password(pw, h1)
        assert verify_password(pw, h2)


# ============================================================
# 纯函数测试：JWT
# ============================================================

class TestJWT:
    """create_token / verify_token"""

    def test_create_and_verify_token(self):
        """正常签发 → 验证成功，payload 正确"""
        token = create_token(42, "test@example.com")
        payload = verify_token(token)
        assert payload["sub"] == "42"
        assert payload["email"] == "test@example.com"

    def test_verify_invalid_token(self):
        """伪造 token → 抛 HTTP 401"""
        with pytest.raises(Exception) as exc:
            verify_token("invalid.token.here")
        # FastAPI HTTPException
        assert hasattr(exc.value, "status_code")
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_expiry(self):
        """验证 exp 字段存在"""
        token = create_token(1, "a@b.com")
        payload = verify_token(token)
        assert "exp" in payload


# ============================================================
# API 端点测试：注册
# ============================================================

class TestRegisterAPI:
    """POST /api/auth/register"""

    def test_register_success(self, client):
        """正常注册 → 返回 token + 企业信息"""
        resp = client.post("/api/auth/register", json={
            "name": "测试企业",
            "email": "test@company.com",
            "password": "123456",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["company_name"] == "测试企业"
        assert data["company_id"] > 0
        assert len(data["access_token"]) > 10
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        """重复邮箱 → 返回 400"""
        payload = {"name": "重复企业", "email": "dup@company.com", "password": "123456"}
        # 第一次成功
        resp1 = client.post("/api/auth/register", json=payload)
        assert resp1.status_code == 200
        # 第二次失败
        resp2 = client.post("/api/auth/register", json=payload)
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST
        assert "已注册" in resp2.json()["detail"]

    def test_register_short_password(self, client):
        """密码过短 → 422"""
        resp = client.post("/api/auth/register", json={
            "name": "X", "email": "x@x.com", "password": "12345",
        })
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_invalid_email(self, client):
        """无效邮箱 → 422"""
        resp = client.post("/api/auth/register", json={
            "name": "X", "email": "not-an-email", "password": "123456",
        })
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================
# API 端点测试：登录
# ============================================================

class TestLoginAPI:
    """POST /api/auth/login"""

    def test_login_success(self, client):
        """注册后正常登录"""
        client.post("/api/auth/register", json={
            "name": "登录测试", "email": "login@test.com", "password": "mypassword",
        })
        resp = client.post("/api/auth/login", json={
            "email": "login@test.com", "password": "mypassword",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["company_name"] == "登录测试"
        assert len(data["access_token"]) > 10

    def test_login_wrong_password(self, client):
        """密码错误 → 401"""
        client.post("/api/auth/register", json={
            "name": "X", "email": "wrongpw@test.com", "password": "correct",
        })
        resp = client.post("/api/auth/login", json={
            "email": "wrongpw@test.com", "password": "wrong_password",
        })
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_email(self, client):
        """未注册邮箱 → 401"""
        resp = client.post("/api/auth/login", json={
            "email": "nobody@nowhere.com", "password": "anything",
        })
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================
# API 端点测试：获取当前企业
# ============================================================

class TestMeAPI:
    """GET /api/auth/me"""

    def test_me_with_valid_token(self, client):
        """有效 token → 返回企业信息"""
        # 先注册
        reg_resp = client.post("/api/auth/register", json={
            "name": "我的企业", "email": "me@test.com", "password": "123456",
        })
        token = reg_resp.json()["access_token"]

        resp = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "我的企业"
        assert data["email"] == "me@test.com"
        assert "ai_tone" in data

    def test_me_without_token(self, client):
        """无 token → 403"""
        resp = client.get("/api/auth/me")
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_invalid_token(self, client):
        """伪造 token → 401"""
        resp = client.get("/api/auth/me", headers={
            "Authorization": "Bearer fake.token.here",
        })
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
