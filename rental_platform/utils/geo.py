"""Latitude / longitude helpers (Haversine distance)."""
import math

EARTH_RADIUS_KM = 6371.0088


def parse_coordinate(value):
    """Return value as a float, or None if it is empty / not a number."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == '':
            return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def is_valid_pair(lat, lng):
    """True only when both values are numbers inside the real lat/long range."""
    lat = parse_coordinate(lat)
    lng = parse_coordinate(lng)
    if lat is None or lng is None:
        return False
    return -90 <= lat <= 90 and -180 <= lng <= 180


def haversine_km(lat1, lng1, lat2, lng2):
    """Distance in kilometres between two points, or None if any value is invalid."""
    if not (is_valid_pair(lat1, lng1) and is_valid_pair(lat2, lng2)):
        return None
    lat1, lng1, lat2, lng2 = (float(parse_coordinate(v)) for v in (lat1, lng1, lat2, lng2))
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return round(2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a)), 1)


def route_points(lat1, lng1, lat2, lng2, width=420, height=200, pad=55):
    """Pixel positions (x1, y1, x2, y2) of two places inside a width x height map box.

    Point 1 is the user, point 2 is the resource. North is up. The scale fits both points in the box.
    """
    mid_lat = math.radians((lat1 + lat2) / 2)
    dx = (lng2 - lng1) * math.cos(mid_lat)
    dy = lat2 - lat1
    abs_x, abs_y = abs(dx), abs(dy)
    centre_x, centre_y = width / 2, height / 2
    if abs_x < 1e-9 and abs_y < 1e-9:      # same place: draw a short line
        return (centre_x - 40, centre_y, centre_x + 40, centre_y)
    scale_x = (width - 2 * pad) / abs_x if abs_x > 1e-9 else float('inf')
    scale_y = (height - 2 * pad) / abs_y if abs_y > 1e-9 else float('inf')
    scale = min(scale_x, scale_y)
    shift_x, shift_y = dx * scale, -dy * scale     # screen y grows downwards
    return (round(centre_x - shift_x / 2, 1), round(centre_y - shift_y / 2, 1),
            round(centre_x + shift_x / 2, 1), round(centre_y + shift_y / 2, 1))
