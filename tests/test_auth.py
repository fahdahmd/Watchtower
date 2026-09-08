def test_register_then_login(client):
    resp = client.post("/auth/register", json={"email": "a@example.com", "password": "supersecret1"})
    assert resp.status_code == 201

    resp = client.post(
        "/auth/login", data={"username": "a@example.com", "password": "supersecret1"}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "b@example.com", "password": "supersecret1"})
    resp = client.post("/auth/login", data={"username": "b@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_duplicate_registration_rejected(client):
    client.post("/auth/register", json={"email": "c@example.com", "password": "supersecret1"})
    resp = client.post("/auth/register", json={"email": "c@example.com", "password": "different1"})
    assert resp.status_code == 400


def test_short_password_rejected(client):
    resp = client.post("/auth/register", json={"email": "d@example.com", "password": "short"})
    assert resp.status_code == 422


def test_watches_endpoint_requires_auth(client):
    resp = client.get("/watches")
    assert resp.status_code == 401
