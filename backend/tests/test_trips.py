import uuid
from datetime import timedelta

from tests.conftest import (
    MALIOBORO,
    NEAR_MALIOBORO,
    NEAR_UGM,
    PRAMBANAN,
    UGM,
    auth,
    future,
    make_trip,
    make_user,
    make_vehicle,
    tomorrow_wib,
)


async def test_requires_auth(client):
    assert (await client.get("/trips")).status_code == 401
    assert (await client.get("/trips", headers={"Authorization": "Bearer rusak"})).status_code == 401


async def test_create_trip_computes_total_cost(client):
    driver = await make_user(driver_status="verified")
    vehicle = await make_vehicle(driver)
    trip = await make_trip(client, driver, vehicle, seats=3, cost=15000)
    assert trip["status"] == "published"
    assert trip["estimated_total_cost"] == 45000
    assert trip["origin"] == UGM


async def test_create_trip_guards(client):
    unverified = await make_user(driver_status="pending")
    passenger = await make_user()
    driver = await make_user(driver_status="verified")
    other_driver = await make_user(driver_status="verified")
    vehicle = await make_vehicle(driver, capacity=4)
    body = {
        "vehicle_id": str(vehicle),
        "origin": UGM,
        "destination": MALIOBORO,
        "departure_time": future().isoformat(),
        "available_seats": 2,
        "cost_per_seat": 5000,
    }
    assert (await client.post("/trips", json=body, headers=auth(unverified))).status_code == 403
    assert (await client.post("/trips", json=body, headers=auth(passenger))).status_code == 403
    assert (await client.post("/trips", json=body, headers=auth(other_driver))).status_code == 403
    unknown_vehicle = {**body, "vehicle_id": str(uuid.uuid4())}
    assert (await client.post("/trips", json=unknown_vehicle, headers=auth(driver))).status_code == 404
    too_many = {**body, "available_seats": 5}
    assert (await client.post("/trips", json=too_many, headers=auth(driver))).status_code == 400
    past = {**body, "departure_time": future(-1).isoformat()}
    assert (await client.post("/trips", json=past, headers=auth(driver))).status_code == 400
    naive = {**body, "departure_time": "2030-01-01T07:00:00"}
    assert (await client.post("/trips", json=naive, headers=auth(driver))).status_code == 422
    bad_lat = {**body, "origin": {"lat": 100, "lng": 0}}
    assert (await client.post("/trips", json=bad_lat, headers=auth(driver))).status_code == 422


async def test_search_by_location_date_and_time(client):
    driver = await make_user(driver_status="verified")
    vehicle = await make_vehicle(driver)
    departure = tomorrow_wib(10)
    match = await make_trip(client, driver, vehicle, departure=departure)
    await make_trip(client, driver, vehicle, destination=PRAMBANAN, departure=departure)
    later_same_day = await make_trip(client, driver, vehicle, departure=tomorrow_wib(20))
    await make_trip(client, driver, vehicle, departure=departure + timedelta(days=1))

    passenger = await make_user()
    params = {
        "origin_lat": NEAR_UGM["lat"],
        "origin_lng": NEAR_UGM["lng"],
        "destination_lat": NEAR_MALIOBORO["lat"],
        "destination_lng": NEAR_MALIOBORO["lng"],
        "date": departure.date().isoformat(),
    }
    resp = await client.get("/trips", params=params, headers=auth(passenger))
    assert resp.status_code == 200
    assert [t["trip_id"] for t in resp.json()] == [match["trip_id"], later_same_day["trip_id"]]

    resp = await client.get("/trips", params={**params, "time": "11:30"}, headers=auth(passenger))
    assert [t["trip_id"] for t in resp.json()] == [match["trip_id"]]

    resp = await client.get("/trips", params={**params, "limit": 1, "offset": 1}, headers=auth(passenger))
    assert [t["trip_id"] for t in resp.json()] == [later_same_day["trip_id"]]


async def test_search_param_validation(client):
    user = await make_user()
    assert (await client.get("/trips", params={"origin_lat": 1}, headers=auth(user))).status_code == 400
    assert (await client.get("/trips", params={"time": "07:00"}, headers=auth(user))).status_code == 400


async def test_search_hides_non_published(client):
    driver = await make_user(driver_status="verified")
    vehicle = await make_vehicle(driver)
    trip = await make_trip(client, driver, vehicle)
    await client.patch(f"/trips/{trip['trip_id']}/status", json={"status": "cancelled"}, headers=auth(driver))
    assert (await client.get("/trips", headers=auth(driver))).json() == []


async def test_recommended(client):
    driver_a = await make_user(driver_status="verified")
    driver_b = await make_user(driver_status="verified")
    vehicle_a = await make_vehicle(driver_a)
    vehicle_b = await make_vehicle(driver_b)
    departure = future(24)
    ref = await make_trip(client, driver_a, vehicle_a, departure=departure)
    close = await make_trip(
        client, driver_b, vehicle_b, origin=NEAR_UGM, destination=NEAR_MALIOBORO,
        departure=departure + timedelta(minutes=30),
    )
    exact = await make_trip(client, driver_b, vehicle_b, departure=departure)
    await make_trip(client, driver_b, vehicle_b, destination=PRAMBANAN, departure=departure)
    await make_trip(client, driver_b, vehicle_b, departure=departure + timedelta(hours=3))
    await make_trip(client, driver_a, vehicle_a, departure=departure)  # trip milik yang request

    resp = await client.get("/trips/recommended", params={"trip_id": ref["trip_id"]}, headers=auth(driver_a))
    assert resp.status_code == 200
    body = resp.json()
    assert [r["trip"]["trip_id"] for r in body] == [exact["trip_id"], close["trip_id"]]
    assert body[0]["score"] == 1
    assert body[1]["time_diff_minutes"] == 30

    missing = await client.get("/trips/recommended", params={"trip_id": str(uuid.uuid4())}, headers=auth(driver_a))
    assert missing.status_code == 404


async def test_trip_detail(client):
    driver = await make_user("Budi", driver_status="verified")
    vehicle = await make_vehicle(driver)
    trip = await make_trip(client, driver, vehicle)
    resp = await client.get(f"/trips/{trip['trip_id']}", headers=auth(driver))
    body = resp.json()
    assert resp.status_code == 200
    assert body["driver"]["name"] == "Budi"
    assert body["vehicle"]["brand"] == "Toyota"
    assert (await client.get(f"/trips/{uuid.uuid4()}", headers=auth(driver))).status_code == 404


async def test_my_published(client):
    driver = await make_user(driver_status="verified")
    vehicle = await make_vehicle(driver)
    trip = await make_trip(client, driver, vehicle)
    resp = await client.get("/trips/me/published", headers=auth(driver))
    assert [t["trip_id"] for t in resp.json()] == [trip["trip_id"]]


async def test_status_transitions(client):
    driver = await make_user(driver_status="verified")
    other = await make_user()
    vehicle = await make_vehicle(driver)
    trip = await make_trip(client, driver, vehicle)
    url = f"/trips/{trip['trip_id']}/status"

    assert (await client.patch(url, json={"status": "ongoing"}, headers=auth(other))).status_code == 403
    assert (await client.patch(url, json={"status": "completed"}, headers=auth(driver))).status_code == 409
    assert (await client.patch(url, json={"status": "published"}, headers=auth(driver))).status_code == 422
    assert (await client.patch(url, json={"status": "ongoing"}, headers=auth(driver))).json()["status"] == "ongoing"
    assert (await client.patch(url, json={"status": "ongoing"}, headers=auth(driver))).status_code == 409
    assert (await client.patch(url, json={"status": "completed"}, headers=auth(driver))).json()["status"] == "completed"
    assert (await client.patch(url, json={"status": "cancelled"}, headers=auth(driver))).status_code == 409
