import pytest


@pytest.mark.asyncio
async def test_list_categories(client, auth_headers, test_category):
    resp = await client.get("/api/v1/categories/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(c["name"] == "Other" for c in data)


@pytest.mark.asyncio
async def test_create_category(client, auth_headers):
    resp = await client.post(
        "/api/v1/categories/",
        json={"name": "TestCat", "color": "#FF0000"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "TestCat"
    assert data["color"] == "#FF0000"
    assert data["is_default"] is False


@pytest.mark.asyncio
async def test_create_duplicate_category(client, auth_headers, test_category):
    resp = await client.post(
        "/api/v1/categories/",
        json={"name": "Other"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_category(client, auth_headers):
    create = await client.post(
        "/api/v1/categories/",
        json={"name": "UpdateMe", "color": "#00FF00"},
        headers=auth_headers,
    )
    cat_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/categories/{cat_id}",
        json={"color": "#0000FF"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["color"] == "#0000FF"


@pytest.mark.asyncio
async def test_delete_category(client, auth_headers):
    create = await client.post(
        "/api/v1/categories/",
        json={"name": "DeleteMe"},
        headers=auth_headers,
    )
    cat_id = create.json()["id"]
    resp = await client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_cannot_delete_default_category(client, auth_headers, test_category):
    resp = await client.delete(
        f"/api/v1/categories/{test_category.id}", headers=auth_headers
    )
    assert resp.status_code == 400
