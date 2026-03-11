import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_and_stats():
    # 健康检查
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "健康"

    # 统计接口
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_requests" in data


def test_register_and_login_flow():
    # 使用随机用户名避免与已有用户冲突
    username = f"user_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "test1234"

    # 注册
    r = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True

    # 登录
    r = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    # 登录后应该设置了 session_id cookie
    assert "session_id" in r.cookies


def test_predict_requires_login():
    # 未登录直接访问预测接口，应被中间件拦截
    r = client.post("/api/predict", json={})
    # 对于 API 请求，中间件返回 401 JSON
    assert r.status_code == 401


def test_batch_bad_file_type():
    # 使用随机用户完成登录，获取会话
    username = f"user_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "test1234"
    client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert login_resp.status_code == 200

    cookies = {"session_id": login_resp.cookies.get("session_id")}

    # 上传一个不支持的文件类型，应该返回 500，并带有可读错误信息
    files = {
        "file": ("bad.txt", b"not a csv", "text/plain"),
    }
    r = client.post("/api/batch-predict", files=files, cookies=cookies)
    assert r.status_code == 500
    data = r.json()
    assert "detail" in data

