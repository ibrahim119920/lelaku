"""Logika kemiripan trip (FR-07), dihitung on-the-fly tanpa menyentuh tabel trip_matches."""

import math
from datetime import datetime, timedelta

# Angka awal, silakan diubah sesuai hasil evaluasi.
MATCH_DISTANCE_THRESHOLD_KM = 2.0
MATCH_TIME_THRESHOLD = timedelta(hours=2)

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bounding_box(lat: float, lng: float, radius_km: float) -> tuple[float, float, float, float]:
    """Kotak (min_lat, max_lat, min_lng, max_lng) yang pasti memuat lingkaran radius_km.

    Dipakai sebagai prefilter murah di SQL sebelum Haversine yang presisi di memory.
    """
    d_lat = math.degrees(radius_km / EARTH_RADIUS_KM)
    cos_lat = max(math.cos(math.radians(lat)), 1e-6)
    d_lng = min(math.degrees(radius_km / (EARTH_RADIUS_KM * cos_lat)), 180.0)
    return lat - d_lat, lat + d_lat, lng - d_lng, lng + d_lng


def match_score(origin_km: float, destination_km: float, time_diff: timedelta) -> float:
    """Skor 0..1 (1 = identik). Bobot sama untuk origin, destination, dan waktu."""
    origin_part = 1 - origin_km / MATCH_DISTANCE_THRESHOLD_KM
    destination_part = 1 - destination_km / MATCH_DISTANCE_THRESHOLD_KM
    time_part = 1 - abs(time_diff) / MATCH_TIME_THRESHOLD
    return round((origin_part + destination_part + time_part) / 3, 4)


def time_window(center: datetime) -> tuple[datetime, datetime]:
    return center - MATCH_TIME_THRESHOLD, center + MATCH_TIME_THRESHOLD
