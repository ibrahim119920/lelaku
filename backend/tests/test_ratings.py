import uuid

from tests.conftest import auth, make_trip_with_passenger, make_user


async def _complete(client, trip_id: str, driver: uuid.UUID):
    for new_status in ("ongoing", "completed"):
        resp = await client.patch(f"/trips/{trip_id}/status", json={"status": new_status}, headers=auth(driver))
        assert resp.status_code == 200


async def _rate(client, trip_id: str, rater: uuid.UUID, rated: uuid.UUID, role: str, score=5):
    return await client.post(
        f"/trips/{trip_id}/ratings",
        json={"rated_user_id": str(rated), "role_context": role, "score": score},
        headers=auth(rater),
    )


async def test_two_way_rating_updates_aggregates(client):
    driver, passenger, trip = await make_trip_with_passenger(client)
    await _complete(client, trip["trip_id"], driver)

    resp = await _rate(client, trip["trip_id"], passenger, driver, "passenger_to_driver", 4)
    assert resp.status_code == 201
    assert resp.json()["score"] == 4
    assert (await _rate(client, trip["trip_id"], driver, passenger, "driver_to_passenger", 5)).status_code == 201

    detail = (await client.get(f"/trips/{trip['trip_id']}", headers=auth(passenger))).json()
    assert detail["driver"]["avg_rating_driver"] == 4
    assert detail["driver"]["total_ratings_driver"] == 1

    # Agregat passenger terlihat di daftar request milik driver.
    requests = (await client.get(f"/trips/{trip['trip_id']}/requests", headers=auth(driver))).json()
    assert requests[0]["requester"]["avg_rating"] == 5
    assert requests[0]["requester"]["total_ratings"] == 1

    received = (await client.get(f"/users/{driver}/ratings", headers=auth(passenger))).json()
    assert [(r["role_context"], r["score"], r["rater_name"]) for r in received] == [
        ("passenger_to_driver", 4, "Passenger")
    ]


async def test_average_across_trips(client):
    driver, passenger, trip = await make_trip_with_passenger(client)
    await _complete(client, trip["trip_id"], driver)
    await _rate(client, trip["trip_id"], driver, passenger, "driver_to_passenger", 3)

    # Driver lain memberi rating ke passenger yang sama di trip lain.
    driver2, passenger2, trip2 = await make_trip_with_passenger(client)
    req = await client.post(f"/trips/{trip2['trip_id']}/requests", json={"pickup": "x"}, headers=auth(passenger))
    await client.patch(
        f"/trips/{trip2['trip_id']}/requests/{req.json()['request_id']}", json={"status": "accepted"}, headers=auth(driver2)
    )
    await _complete(client, trip2["trip_id"], driver2)
    await _rate(client, trip2["trip_id"], driver2, passenger, "driver_to_passenger", 4)

    received = (await client.get(f"/users/{passenger}/ratings", headers=auth(passenger))).json()
    assert sorted(r["score"] for r in received) == [3, 4]
    requests = (await client.get(f"/trips/{trip2['trip_id']}/requests", headers=auth(driver2))).json()
    sari = next(r for r in requests if r["requester_id"] == str(passenger))
    assert sari["requester"]["avg_rating"] == 3.5
    assert sari["requester"]["total_ratings"] == 2


async def test_rating_requires_completed_trip(client):
    driver, passenger, trip = await make_trip_with_passenger(client)
    assert (await _rate(client, trip["trip_id"], passenger, driver, "passenger_to_driver")).status_code == 409


async def test_rating_guards(client):
    driver, passenger, trip = await make_trip_with_passenger(client)
    await _complete(client, trip["trip_id"], driver)
    outsider = await make_user()
    tid = trip["trip_id"]

    assert (await _rate(client, tid, outsider, driver, "passenger_to_driver")).status_code == 403
    assert (await _rate(client, tid, passenger, passenger, "passenger_to_driver")).status_code == 400
    # role_context tidak cocok dengan peran sebenarnya
    assert (await _rate(client, tid, passenger, driver, "driver_to_passenger")).status_code == 400
    assert (await _rate(client, tid, driver, passenger, "passenger_to_driver")).status_code == 400
    # driver merating orang yang bukan passenger trip ini
    assert (await _rate(client, tid, driver, outsider, "driver_to_passenger")).status_code == 400

    for bad in (0, 6, 4.5, "5"):
        resp = await _rate(client, tid, passenger, driver, "passenger_to_driver", bad)
        assert resp.status_code == 422, bad
    assert (await _rate(client, str(uuid.uuid4()), passenger, driver, "passenger_to_driver")).status_code == 404


async def test_duplicate_rating_conflict(client):
    driver, passenger, trip = await make_trip_with_passenger(client)
    await _complete(client, trip["trip_id"], driver)
    assert (await _rate(client, trip["trip_id"], passenger, driver, "passenger_to_driver", 5)).status_code == 201
    assert (await _rate(client, trip["trip_id"], passenger, driver, "passenger_to_driver", 1)).status_code == 409


async def test_list_ratings_filter_and_404(client):
    driver, passenger, trip = await make_trip_with_passenger(client)
    await _complete(client, trip["trip_id"], driver)
    await _rate(client, trip["trip_id"], passenger, driver, "passenger_to_driver", 5)

    url = f"/users/{driver}/ratings"
    assert (await client.get(url, params={"role_context": "driver_to_passenger"}, headers=auth(driver))).json() == []
    assert len((await client.get(url, params={"role_context": "passenger_to_driver"}, headers=auth(driver))).json()) == 1
    assert (await client.get(f"/users/{uuid.uuid4()}/ratings", headers=auth(driver))).status_code == 404
