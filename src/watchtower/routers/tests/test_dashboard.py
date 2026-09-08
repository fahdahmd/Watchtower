def _auth_headers(client, email="dashboard@example.com", password="supersecret1"):
    client.post("/auth/register", json={"email": email, "password": password})
    resp = client.post("/auth/login", data={"username": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_watch_rows_partial_requires_auth(client):
    resp = client.get("/partials/watch-rows")
    assert resp.status_code == 401


def test_watch_rows_partial_renders_empty_state(client):
    headers = _auth_headers(client)
    resp = client.get("/partials/watch-rows", headers=headers)
    assert resp.status_code == 200
    assert "No watches yet" in resp.text


def test_watch_rows_partial_renders_a_watch(client):
    headers = _auth_headers(client)
    client.post(
        "/watches",
        json={"name": "Dashboard test", "url": "https://example.com", "check_interval_minutes": 60},
        headers=headers,
    )
    resp = client.get("/partials/watch-rows", headers=headers)
    assert resp.status_code == 200
    assert "Dashboard test" in resp.text