import io

import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_list_payment_methods(client, auth_headers):
    resp = await client.get('/api/v1/payment-methods/', headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4
    assert any(item['key'] == 'card' for item in data)


@pytest.mark.asyncio
async def test_create_update_delete_payment_method(client, auth_headers):
    create = await client.post(
        '/api/v1/payment-methods/',
        json={'name': 'Mobile Wallet'},
        headers=auth_headers,
    )
    assert create.status_code == 201, create.text
    created = create.json()
    assert created['name'] == 'Mobile Wallet'
    assert created['key'].startswith('mobile_wallet')

    update = await client.patch(
        f"/api/v1/payment-methods/{created['id']}",
        json={'name': 'Apple Pay'},
        headers=auth_headers,
    )
    assert update.status_code == 200, update.text
    assert update.json()['name'] == 'Apple Pay'

    delete = await client.delete(
        f"/api/v1/payment-methods/{created['id']}",
        headers=auth_headers,
    )
    assert delete.status_code == 204

    listing = await client.get('/api/v1/payment-methods/', headers=auth_headers)
    ids = [item['id'] for item in listing.json()]
    assert created['id'] not in ids


@pytest.mark.asyncio
async def test_create_operation_with_attachments(client, auth_headers, test_user, test_category, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'UPLOAD_DIR', str(tmp_path))

    data = {
        'amount': '150.00',
        'currency': 'EUR',
        'type': 'expense',
        'description': 'Groceries',
        'is_recurring': 'false',
        'operation_date': '2026-04-02T10:30:00Z',
        'category_id': str(test_category.id),
        'user_id': str(test_user.id),
    }
    files = [
        ('files', ('receipt.pdf', io.BytesIO(b'%PDF-1.4 test'), 'application/pdf')),
    ]

    resp = await client.post(
        '/api/v1/operations/with-attachments',
        data=data,
        files=files,
        headers=auth_headers,
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body['description'] == 'Groceries'
    assert len(body['attachments']) == 1
    assert body['attachments'][0]['original_filename'] == 'receipt.pdf'

