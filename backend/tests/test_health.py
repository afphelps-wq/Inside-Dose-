from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_pages_origin():
    origin = "https://afphelps-wq.github.io"
    response = client.get("/health", headers={"Origin": origin})
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_other_origin():
    response = client.get("/health", headers={"Origin": "https://example.com"})
    assert "access-control-allow-origin" not in response.headers


def test_unknown_path_uses_error_format():
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
