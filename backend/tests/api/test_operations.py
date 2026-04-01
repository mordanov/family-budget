import pytest
from datetime import datetime, timezone


def make_op(user_id: int, category_id: int, **kwargs):
    return {
        "amount": "150.00",
        "currency": "EUR",
        "type": "expense",
        "payment_type": "card",
        "description": "Test operation",
        "is_recurring": False,
        "recurring_end_date": None,
        "operation_date": datetime.now(timezone.utc).isoformat(),
        "category_id": category_id,
        "user_id": user_id,
        **kwargs,
    }


@pytest.mark.asyncio
async def test_create_operation(client, auth_headers, test_user, test_category):
    payload = make_op(test_user.id, test_category.id)
    resp = await client.post("/api/v1/operations/", json=payload, headers=auth_headers)
    assert resp.status_code == 201, f"Got {resp.status_code}: {resp.json()}"
    data = resp.json()
    assert data["amount"] == "150.00"
    assert data["type"] == "expense"
    assert data["user"]["id"] == test_user.id
    assert data["category"]["id"] == test_category.id


@pytest.mark.asyncio
async def test_get_operation(client, auth_headers, test_user, test_category):
    create = await client.post(
        "/api/v1/operations/",
        json=make_op(test_user.id, test_category.id),
        headers=auth_headers,
    )
    op_id = create.json()["id"]
    resp = await client.get(f"/api/v1/operations/{op_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == op_id


@pytest.mark.asyncio
async def test_list_operations(client, auth_headers, test_user, test_category):
    await client.post(
        "/api/v1/operations/",
        json=make_op(test_user.id, test_category.id, amount="50.00"),
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/operations/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_update_operation(client, auth_headers, test_user, test_category):
    create = await client.post(
        "/api/v1/operations/",
        json=make_op(test_user.id, test_category.id),
        headers=auth_headers,
    )
    op_id = create.json()["id"]
    resp = await client.patch(
        f"/api/v1/operations/{op_id}",
        json={"amount": "200.00", "description": "Updated"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["amount"] == "200.00"
    assert resp.json()["description"] == "Updated"


@pytest.mark.asyncio
async def test_delete_operation(client, auth_headers, test_user, test_category):
    create = await client.post(
        "/api/v1/operations/",
        json=make_op(test_user.id, test_category.id),
        headers=auth_headers,
    )
    op_id = create.json()["id"]
    resp = await client.delete(f"/api/v1/operations/{op_id}", headers=auth_headers)
    assert resp.status_code == 204
    # Should not be found after soft delete
    get = await client.get(f"/api/v1/operations/{op_id}", headers=auth_headers)
    assert get.status_code == 404


@pytest.mark.asyncio
async def test_create_recurring_operation(client, auth_headers, test_user, test_category):
    payload = make_op(
        test_user.id,
        test_category.id,
        is_recurring=True,
        recurring_end_date="2025-12-31T00:00:00Z",
        description="Monthly rent",
    )
    resp = await client.post("/api/v1/operations/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_recurring"] is True
    assert data["recurring_end_date"] is not None


@pytest.mark.asyncio
async def test_filter_by_type(client, auth_headers, test_user, test_category):
    await client.post(
        "/api/v1/operations/",
        json=make_op(test_user.id, test_category.id, type="income", amount="1000.00"),
        headers=auth_headers,
    )
    resp = await client.get(
        "/api/v1/operations/?type=income", headers=auth_headers
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(i["type"] == "income" for i in items)
