import json
import logging
import math
import os
import time
import threading
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_CACHE_LOCK = threading.Lock()
_GEOCODE_CACHE: Dict[str, Any] = {}
_REVERSE_GEOCODE_CACHE: Dict[tuple, Any] = {}
_NEARBY_HOSPITALS_CACHE: Dict[tuple, Any] = {}

GEOCODE_CACHE_TTL = 3600  # 1 hour
REVERSE_CACHE_TTL = 3600  # 1 hour
NEARBY_CACHE_TTL = 900    # 15 minutes


KNOWN_LOCATIONS = {
    'bengaluru': {'lat': 12.9716, 'lng': 77.5946},
    'bangalore': {'lat': 12.9716, 'lng': 77.5946},
    'manipal': {'lat': 13.3525, 'lng': 74.7874},
    'mangalore': {'lat': 12.9141, 'lng': 74.8560},
    'mangaluru': {'lat': 12.9141, 'lng': 74.8560},
    'karwar': {'lat': 14.8122, 'lng': 74.1323},
    'ankola': {'lat': 14.6653, 'lng': 74.3054},
    'mysore': {'lat': 12.2958, 'lng': 76.6394},
    'mysuru': {'lat': 12.2958, 'lng': 76.6394},
    'hubli': {'lat': 15.3647, 'lng': 75.1240},
    'hubballi': {'lat': 15.3647, 'lng': 75.1240},
    'dharwad': {'lat': 15.4589, 'lng': 75.0078},
    'belgaum': {'lat': 15.8497, 'lng': 74.4977},
    'belagavi': {'lat': 15.8497, 'lng': 74.4977},
    'udupi': {'lat': 13.3409, 'lng': 74.7421},
    'shimoga': {'lat': 13.9299, 'lng': 75.5681},
    'shivamogga': {'lat': 13.9299, 'lng': 75.5681},
    'delhi': {'lat': 28.6139, 'lng': 77.2090},
    'mumbai': {'lat': 19.0760, 'lng': 72.8777},
    'chennai': {'lat': 13.0827, 'lng': 80.2707},
    'hyderabad': {'lat': 17.3850, 'lng': 78.4867},
}


def geocode_address(address_str: str) -> Optional[Dict[str, float]]:
    """Resolve a supplied address through Google, OSM, or fast location map with caching."""
    if not address_str or not address_str.strip():
        return None

    clean_key = address_str.strip().lower()
    now = time.time()
    with _CACHE_LOCK:
        if clean_key in _GEOCODE_CACHE:
            ts, val = _GEOCODE_CACHE[clean_key]
            if now - ts < GEOCODE_CACHE_TTL:
                return val

    # Fast Path: Check known city dictionary
    for city, coords in KNOWN_LOCATIONS.items():
        if city in clean_key:
            with _CACHE_LOCK:
                _GEOCODE_CACHE[clean_key] = (now, coords)
            return coords

    result = None
    google_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if google_key:
        try:
            params = urllib.parse.urlencode({"address": address_str, "key": google_key})
            with urllib.request.urlopen(
                f"https://maps.googleapis.com/maps/api/geocode/json?{params}",
                timeout=2,
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
            results = data.get("results")
            if results and isinstance(results, list) and len(results) > 0:
                location = results[0].get("geometry", {}).get("location")
                if location and "lat" in location and "lng" in location:
                    result = {"lat": float(location["lat"]), "lng": float(location["lng"])}
        except Exception as exc:
            logger.warning("Google geocoding failed: %s", type(exc).__name__)

    if not result:
        try:
            params = urllib.parse.urlencode({"q": address_str, "format": "json", "limit": 1})
            request = urllib.request.Request(
                f"https://nominatim.openstreetmap.org/search?{params}",
                headers={"User-Agent": "GENOMIX-AI-Health/1.0"},
            )
            with urllib.request.urlopen(request, timeout=2) as response:
                data = json.loads(response.read().decode("utf-8"))
            if data:
                result = {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"])}
        except Exception as exc:
            logger.warning("OSM geocoding failed: %s", type(exc).__name__)

    if result:
        with _CACHE_LOCK:
            _GEOCODE_CACHE[clean_key] = (now, result)

    return result


def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """Reverse geocode coordinates to an address/location string with caching."""
    key = (round(float(lat), 3), round(float(lng), 3))
    now = time.time()
    with _CACHE_LOCK:
        if key in _REVERSE_GEOCODE_CACHE:
            ts, val = _REVERSE_GEOCODE_CACHE[key]
            if now - ts < REVERSE_CACHE_TTL:
                return val

    result = None
    google_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if google_key:
        try:
            params = urllib.parse.urlencode({"latlng": f"{lat},{lng}", "key": google_key})
            with urllib.request.urlopen(
                f"https://maps.googleapis.com/maps/api/geocode/json?{params}",
                timeout=2,
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
            results = data.get("results")
            if results and isinstance(results, list) and len(results) > 0:
                formatted = results[0].get("formatted_address")
                if formatted:
                    result = formatted
        except Exception as exc:
            logger.warning("Google reverse geocoding failed: %s", type(exc).__name__)

    if not result:
        try:
            params = urllib.parse.urlencode({"lat": str(lat), "lon": str(lng), "format": "json"})
            request = urllib.request.Request(
                f"https://nominatim.openstreetmap.org/reverse?{params}",
                headers={"User-Agent": "GENOMIX-AI-Health/1.0"},
            )
            with urllib.request.urlopen(request, timeout=2) as response:
                data = json.loads(response.read().decode("utf-8"))
            if data and isinstance(data, dict):
                display_name = data.get("display_name")
                if display_name:
                    result = display_name
        except Exception as exc:
            logger.warning("OSM reverse geocoding failed: %s", type(exc).__name__)

    if result:
        with _CACHE_LOCK:
            _REVERSE_GEOCODE_CACHE[key] = (now, result)

    return result


def search_nearby_hospitals(lat: float, lng: float, radius_km: float = 50.0) -> List[Dict[str, Any]]:
    """Search real hospital providers and return facilities nearest first with caching."""
    key = (round(float(lat), 2), round(float(lng), 2))
    now = time.time()
    with _CACHE_LOCK:
        if key in _NEARBY_HOSPITALS_CACHE:
            ts, val = _NEARBY_HOSPITALS_CACHE[key]
            if now - ts < NEARBY_CACHE_TTL:
                return [dict(h) for h in val]

    # Fast Path 1: Google Places API if key configured
    google_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if google_key:
        google_results = _search_google_places(lat, lng, google_key)
        if google_results:
            with _CACHE_LOCK:
                _NEARBY_HOSPITALS_CACHE[key] = (now, google_results)
            return google_results

    # Fast Path 2: Check if DB already has hospitals near these coordinates
    try:
        from app.services.hospital_service import get_hospitals_from_db_near
        db_hospitals = get_hospitals_from_db_near(lat, lng, radius_km=radius_km)
        if not db_hospitals:
            db_hospitals = get_hospitals_from_db_near(lat, lng, radius_km=1000.0)

        if db_hospitals and len(db_hospitals) >= 1:
            with _CACHE_LOCK:
                _NEARBY_HOSPITALS_CACHE[key] = (now, db_hospitals)
            return db_hospitals
    except Exception as exc:
        logger.warning("DB nearby hospital lookup skipped: %s", exc)

    # Path 3: Single optimized Overpass API query (50km radius, 2s max timeout)
    hospitals: List[Dict[str, Any]] = []
    try:
        query = f"""
        [out:json][timeout:2];
        (node["amenity"="hospital"](around:50000,{lat},{lng});
         way["amenity"="hospital"](around:50000,{lat},{lng}););
        out center 50;
        """
        request = urllib.request.Request(
            "https://overpass-api.de/api/interpreter",
            data=query.encode("utf-8"),
            headers={"User-Agent": "GENOMIX-AI-Health/1.0"},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            h_lat = element.get("lat") or element.get("center", {}).get("lat")
            h_lng = element.get("lon") or element.get("center", {}).get("lon")
            if h_lat is None or h_lng is None or not tags.get("name"):
                continue
            hospitals.append(_hospital_record(
                f"osm_{element.get('type')}_{element.get('id')}",
                tags["name"],
                tags.get("addr:full") or tags.get("addr:street") or tags.get("addr:city") or "",
                float(h_lat),
                float(h_lng),
                lat,
                lng,
                tags.get("phone") or tags.get("contact:phone"),
                tags.get("opening_hours"),
            ))
        
        hospitals = _deduplicate_and_sort(hospitals)
    except Exception as exc:
        logger.warning("Overpass hospital search failed: %s", type(exc).__name__)

    # Fallback to any DB hospitals if Overpass had no results or timed out
    if not hospitals:
        try:
            from app.services.hospital_service import get_hospitals_from_db_near
            hospitals = get_hospitals_from_db_near(lat, lng, radius_km=500.0)
        except Exception:
            pass

    if hospitals:
        with _CACHE_LOCK:
            _NEARBY_HOSPITALS_CACHE[key] = (now, hospitals)

    return hospitals



def _search_google_places(lat: float, lng: float, api_key: str) -> List[Dict[str, Any]]:
    try:
        params = urllib.parse.urlencode({
            "location": f"{lat},{lng}",
            "radius": 50000,
            "type": "hospital",
            "key": api_key,
        })
        with urllib.request.urlopen(
            f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?{params}",
            timeout=5,
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
        if data.get("status") not in {"OK", "ZERO_RESULTS"}:
            logger.warning("Google Places returned status %s", data.get("status"))
        hospitals = []
        for place in data.get("results", []):
            location = place.get("geometry", {}).get("location", {})
            if not location.get("lat") or not location.get("lng"):
                continue
            hospitals.append(_hospital_record(
                f"google_{place.get('place_id')}",
                place.get("name"),
                place.get("vicinity", ""),
                float(location["lat"]),
                float(location["lng"]),
                lat,
                lng,
                None,
                "Open now" if place.get("opening_hours", {}).get("open_now") else None,
            ))
        return _deduplicate_and_sort(hospitals)
    except Exception as exc:
        logger.warning("Google Places search failed: %s", type(exc).__name__)
        return []


def _hospital_record(external_id: str, name: Optional[str], address: str, h_lat: float, h_lng: float, user_lat: float, user_lng: float, phone: Optional[str], opening_hours: Optional[str]) -> Dict[str, Any]:
    return {
        "external_place_id": external_id,
        "name": name or "Hospital",
        "address": address,
        "lat": h_lat,
        "lng": h_lng,
        "distance_km": round(_haversine_distance(user_lat, user_lng, h_lat, h_lng), 1),
        "phone": phone,
        "opening_hours": opening_hours,
    }


def _deduplicate_and_sort(hospitals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for hospital in hospitals:
        key = (round(hospital["lat"], 4), round(hospital["lng"], 4))
        if key not in seen:
            seen.add(key)
            unique.append(hospital)
    return sorted(unique, key=lambda item: item["distance_km"])


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    value = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))

