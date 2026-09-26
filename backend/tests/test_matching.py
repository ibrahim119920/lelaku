from datetime import timedelta

from backend.app.trip import matching


def test_haversine_known_distance():
    # Tugu Jogja -> Malioboro, kira-kira 1.07 km
    assert 1.0 < matching.haversine_km(-7.7829, 110.3671, -7.7925, 110.3658) < 1.2


def test_haversine_zero():
    assert matching.haversine_km(-7.77, 110.37, -7.77, 110.37) == 0


def test_bounding_box_contains_radius():
    min_lat, max_lat, min_lng, max_lng = matching.bounding_box(-7.77, 110.37, 2.0)
    assert matching.haversine_km(-7.77, 110.37, max_lat, 110.37) >= 1.99
    assert matching.haversine_km(-7.77, 110.37, -7.77, max_lng) >= 1.99


def test_match_score_bounds():
    assert matching.match_score(0, 0, timedelta(0)) == 1
    assert matching.match_score(2, 2, timedelta(hours=2)) == 0
