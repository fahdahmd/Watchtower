def _auth_headers(client, email="owner@example.com", password="supersecret1"):
    client.post("/auth/register", json={"email": email, "password": password})
    resp = client.post("/auth/login", data={"username": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_watch(client):
    headers = _auth_headers(client)
    resp = client.post(
        "/watches",
        json={"name": "Example", "url": "https://example.com", "check_interval_minutes": 60},
        headers=headers,
    )
    assert resp.status_code == 201

    resp = client.get("/watches", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_non_http_url_rejected(client):
    headers = _auth_headers(client)
    resp = client.post(
        "/watches",
        json={"name": "Bad", "url": "ftp://example.com", "check_interval_minutes": 60},
        headers=headers,
    )
    assert resp.status_code == 422


def test_interval_below_minimum_rejected(client):
    headers = _auth_headers(client)
    resp = client.post(
        "/watches",
        json={"name": "TooFast", "url": "https://example.com", "check_interval_minutes": 1},
        headers=headers,
    )
    assert resp.status_code == 422


def test_user_cannot_access_another_users_watch(client):
    headers_a = _auth_headers(client, email="alice@example.com")
    headers_b = _auth_headers(client, email="bob@example.com")

    create_resp = client.post(
        "/watches",
        json={"name": "Alice's watch", "url": "https://example.com", "check_interval_minutes": 60},
        headers=headers_a,
    )
    watch_id = create_resp.json()["id"]

    resp = client.get(f"/watches/{watch_id}", headers=headers_b)
    assert resp.status_code == 404  # not 403 — existence isn't revealed either


def test_watch_limit_enforced(client, monkeypatch):
    import watchtower.routers.watches as watches_module

    monkeypatch.setattr(watches_module.settings, "max_watches_per_user", 1)
    headers = _auth_headers(client)

    client.post(
        "/watches",
        json={"name": "First", "url": "https://example.com", "check_interval_minutes": 60},
        headers=headers,
    )
    resp = client.post(
        "/watches",
        json={"name": "Second", "url": "https://example.com", "check_interval_minutes": 60},
        headers=headers,
    )
    assert resp.status_code == 400
