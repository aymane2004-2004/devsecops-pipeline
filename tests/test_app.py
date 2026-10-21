import pytest

from app.main import app


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_index(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.get_json()["service"] == "devsecops-demo-api"


def test_security_headers_present(client):
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in r.headers["Content-Security-Policy"]
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert r.headers["Cache-Control"] == "no-store"


def test_create_and_get_item(client):
    r = client.post("/api/items", json={"name": "demo"})
    assert r.status_code == 201
    item = r.get_json()
    r2 = client.get(f"/api/items/{item['id']}")
    assert r2.status_code == 200
    assert r2.get_json()["name"] == "demo"


def test_list_items(client):
    client.post("/api/items", json={"name": "a"})
    r = client.get("/api/items")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": 123},
        {"name": "<script>alert(1)</script>"},
        {"name": "'; DROP TABLE items;--"},
        {"name": "x" * 65},
    ],
)
def test_invalid_payload_rejected(client, payload):
    r = client.post("/api/items", json=payload)
    assert r.status_code == 400


def test_non_json_rejected(client):
    r = client.post("/api/items", data="not json", content_type="text/plain")
    assert r.status_code == 400


def test_item_not_found(client):
    r = client.get("/api/items/999999")
    assert r.status_code == 404


def test_non_integer_id_is_404(client):
    r = client.get("/api/items/abc")
    assert r.status_code == 404


def test_method_not_allowed(client):
    r = client.delete("/api/items")
    assert r.status_code == 405


def test_payload_too_large(client):
    r = client.post("/api/items", data="x" * (17 * 1024), content_type="application/json")
    assert r.status_code == 413
