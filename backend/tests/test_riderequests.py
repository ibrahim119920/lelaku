import asyncio
import uuid

from backend.tests.conftest import auth, make_trip, make_user, make_vehicle


async def _setup(client, seats: int = 2):
    driver = await make_user("Driver", driver_status="verified")
    vehicle = await make_vehicle(driver)
    trip = await make_trip(client, driver, vehicle, seats=seats)
    return driver, trip


async def _request(client, trip_id: str, user_id: uuid.UUID, pickup: str = "Gerbang UGM"):
    return await client.post(f"/trips/{trip_id}/requests", json={"pickup": pickup}, headers=auth(user_id))


async def test_create_request(client):
    _, trip = await _setup(client)
    passenger = await make_user()
    resp = await _request(client, trip["trip_id"], passenger)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    assert body["pickup"] == "Gerbang UGM"
    assert body["created_at"]


async def test_create_request_guards(client):
    driver, trip = await _setup(client)
    passenger = await make_user()
    assert (await _request(client, trip["trip_id"], driver)).status_code == 403
    assert (await _request(client, str(uuid.uuid4()), passenger)).status_code == 404
    empty = await client.post(f"/trips/{trip['trip_id']}/requests", json={"pickup": ""}, headers=auth(passenger))
    assert empty.status_code == 422

    await client.patch(f"/trips/{trip['trip_id']}/status", json={"status": "ongoing"}, headers=auth(driver))
    assert (await _request(client, trip["trip_id"], passenger)).status_code == 409


async def test_duplicate_pending_rejected_then_allowed_after_reject(client):
    driver, trip = await _setup(client)
    passenger = await make_user()
    first = (await _request(client, trip["trip_id"], passenger)).json()
    assert (await _request(client, trip["trip_id"], passenger)).status_code == 409

    await client.patch(
        f"/trips/{trip['trip_id']}/requests/{first['request_id']}", json={"status": "rejected"}, headers=auth(driver)
    )
    assert (await _request(client, trip["trip_id"], passenger)).status_code == 201


async def test_cannot_request_again_after_accepted(client):
    driver, trip = await _setup(client)
    passenger = await make_user()
    req = (await _request(client, trip["trip_id"], passenger)).json()
    await client.patch(
        f"/trips/{trip['trip_id']}/requests/{req['request_id']}", json={"status": "accepted"}, headers=auth(driver)
    )
    assert (await _request(client, trip["trip_id"], passenger)).status_code == 409


async def test_list_requests_only_driver(client):
    driver, trip = await _setup(client)
    passenger = await make_user("Sari")
    await _request(client, trip["trip_id"], passenger)
    url = f"/trips/{trip['trip_id']}/requests"

    assert (await client.get(url, headers=auth(passenger))).status_code == 403
    resp = await client.get(url, headers=auth(driver))
    assert resp.status_code == 200
    assert resp.json()[0]["requester"]["name"] == "Sari"
    assert (await client.get(url, params={"status": "accepted"}, headers=auth(driver))).json() == []


async def test_accept_creates_member_and_decrements_seats(client):
    driver, trip = await _setup(client, seats=2)
    passenger = await make_user("Sari")
    req = (await _request(client, trip["trip_id"], passenger)).json()
    url = f"/trips/{trip['trip_id']}/requests/{req['request_id']}"

    assert (await client.patch(url, json={"status": "accepted"}, headers=auth(passenger))).status_code == 403
    resp = await client.patch(url, json={"status": "accepted"}, headers=auth(driver))
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"
    assert (await client.patch(url, json={"status": "rejected"}, headers=auth(driver))).status_code == 409

    detail = (await client.get(f"/trips/{trip['trip_id']}", headers=auth(driver))).json()
    assert detail["available_seats"] == 1

    members = (await client.get(f"/trips/{trip['trip_id']}/members", headers=auth(passenger))).json()
    assert [(m["role"], m["name"]) for m in members] == [("driver", "Driver"), ("passenger", "Sari")]
    assert members[0]["trip_member_id"] is None
    assert members[1]["status"] == "active"

    joined = (await client.get("/trips/me/joined", headers=auth(passenger))).json()
    assert [(t["trip_id"], t["member_status"]) for t in joined] == [(trip["trip_id"], "active")]


async def test_accept_rejected_when_no_seats(client):
    driver, trip = await _setup(client, seats=1)
    p1, p2 = await make_user(), await make_user()
    r1 = (await _request(client, trip["trip_id"], p1)).json()
    r2 = (await _request(client, trip["trip_id"], p2)).json()
    base = f"/trips/{trip['trip_id']}/requests"
    assert (await client.patch(f"{base}/{r1['request_id']}", json={"status": "accepted"}, headers=auth(driver))).status_code == 200
    resp = await client.patch(f"{base}/{r2['request_id']}", json={"status": "accepted"}, headers=auth(driver))
    assert resp.status_code == 409
    # Request baru juga ditolak karena kursi sudah penuh.
    assert (await _request(client, trip["trip_id"], await make_user())).status_code == 409


async def test_concurrent_accepts_never_oversell(client):
    driver, trip = await _setup(client, seats=1)
    passengers = [await make_user() for _ in range(4)]
    requests = [(await _request(client, trip["trip_id"], p)).json() for p in passengers]
    base = f"/trips/{trip['trip_id']}/requests"

    responses = await asyncio.gather(
        *(
            client.patch(f"{base}/{r['request_id']}", json={"status": "accepted"}, headers=auth(driver))
            for r in requests
        )
    )
    assert sorted(r.status_code for r in responses) == [200, 409, 409, 409]
    detail = (await client.get(f"/trips/{trip['trip_id']}", headers=auth(driver))).json()
    assert detail["available_seats"] == 0


async def test_request_not_in_trip_is_404(client):
    driver, trip = await _setup(client)
    _, other_trip = await _setup(client)
    passenger = await make_user()
    req = (await _request(client, other_trip["trip_id"], passenger)).json()
    resp = await client.patch(
        f"/trips/{trip['trip_id']}/requests/{req['request_id']}", json={"status": "accepted"}, headers=auth(driver)
    )
    assert resp.status_code == 404


async def test_cancel_trip_cancels_members(client):
    driver, trip = await _setup(client)
    passenger = await make_user()
    req = (await _request(client, trip["trip_id"], passenger)).json()
    await client.patch(
        f"/trips/{trip['trip_id']}/requests/{req['request_id']}", json={"status": "accepted"}, headers=auth(driver)
    )
    await client.patch(f"/trips/{trip['trip_id']}/status", json={"status": "cancelled"}, headers=auth(driver))

    joined = (await client.get("/trips/me/joined", headers=auth(passenger))).json()
    assert joined[0]["member_status"] == "cancelled"
    assert joined[0]["status"] == "cancelled"
