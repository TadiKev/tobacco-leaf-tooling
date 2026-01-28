# mltools/utils.py
from math import radians, cos, sin, asin, sqrt

def haversine_km(lat1, lon1, lat2, lon2):
    """Return distance in km between two lat/lon points."""
    # degrees -> radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371.0
    return c * r

def bounding_box(lat, lon, radius_km):
    """Return (min_lat, max_lat, min_lon, max_lon) approximate bounding box."""
    # Approx: 1 deg lat ~ 111 km
    lat_deg = radius_km / 111.0
    # lon deg varies by latitude
    lon_deg = abs(radius_km / (111.320 * cos(radians(lat)) if cos(radians(lat)) != 0 else 1))
    return (lat - lat_deg, lat + lat_deg, lon - lon_deg, lon + lon_deg)
