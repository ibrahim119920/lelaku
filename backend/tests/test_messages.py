import uuid

from tests.conftest import auth, make_trip_with_passenger, make_user


async def _send(client, trip_id: str, user_id: uuid.UUID, content: str):
    return await client.post(f"/trips/{trip_id}/messages", json={"content": content}, headers=auth(user_id))


async def test_driver_and_member_can_chat(client):
    driver, passenger, trip = await make_trip_with_passenger(client)
    first = await _send(client, trip["trip_id"], passenger, "Halo pak, saya di gerbang")
    assert first.status_code == 201
    assert first.json()["sender_name"] == "Passenger"
    assert (await _send(client, trip["trip_id"], driver, "Oke, 5 menit lagi")).status_code == 201

    resp = await client.get(f"/trips/{trip['trip_id']}/messages", headers=auth(driver))
    assert resp.status_code == 200
    assert [m["content"] for m in resp.json()] == ["Halo pak, saya di gerbang", "Oke, 5 menit lagi"]


async def test_polling_with_after(client):
    driver, passenger, trip = await make_trip_with_passenger(client)
    first = (await _send(client, trip["trip_id"], passenger, "satu")).json()
    await _send(client, trip["trip_id"], driver, "dua")
    await _send(client, trip["trip_id"], passenger, "tiga")

    resp = await client.get(
        f"/trips/{trip['trip_id']}/messages", params={"after": first["sent_at"]}, headers=auth(passenger)
    )
    assert [m["content"] for m in resp.json()] == ["dua", "tiga"]

    latest_two = await client.get(f"/trips/{trip['trip_id']}/messages", params={"limit": 2}, headers=auth(passenger))
    assert [m["content"] for m in latest_two.json()] == ["dua", "tiga"]


async def test_non_member_forbidden(client):
    _, _, trip = await make_trip_with_passenger(client)
    outsider = await make_user()
    assert (await _send(client, trip["trip_id"], outsider, "hai")).status_code == 403
    assert (await client.get(f"/trips/{trip['trip_id']}/messages", headers=auth(outsider))).status_code == 403


async def test_pending_requester_forbidden(client):
    _, _, trip = await make_trip_with_passenger(client)
    pending = await make_user()
    await client.post(f"/trips/{trip['trip_id']}/requests", json={"pickup": "x"}, headers=auth(pending))
    assert (await _send(client, trip["trip_id"], pending, "hai")).status_code == 403


async def test_cancelled_member_loses_access(client):
    driver, passenger, trip = await make_trip_with_passenger(client)
    await client.patch(f"/trips/{trip['trip_id']}/status", json={"status": "cancelled"}, headers=auth(driver))
    assert (await _send(client, trip["trip_id"], passenger, "hai")).status_code == 403


async def test_validation_and_404(client):
    driver, _, trip = await make_trip_with_passenger(client)
    assert (await _send(client, trip["trip_id"], driver, "")).status_code == 422
    assert (await _send(client, trip["trip_id"], driver, "x" * 2001)).status_code == 422
    assert (await _send(client, str(uuid.uuid4()), driver, "hai")).status_code == 404
    naive = await client.get(
        f"/trips/{trip['trip_id']}/messages", params={"after": "2026-01-01T00:00:00"}, headers=auth(driver)
    )
    assert naive.status_code == 422
