import json
import logging
import math
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def geocode_address(address_str: str) -> Optional[Dict[str, float]]:
    """Resolve a supplied address through Google, then real OSM geocoding."""
    if not address_str or not address_str.strip():
        return None

    google_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if google_key:
        try:
            params = urllib.parse.urlencode({"address": address_str, "key": google_key})
            with urllib.request.urlopen(
                f"https://maps.googleapis.com/maps/api/geocode/json?{params}",
                timeout=8,
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
            results = data.get("results")
            if results and isinstance(results, list) and len(results) > 0:
                location = results[0].get("geometry", {}).get("location")
                if location and "lat" in location and "lng" in location:
                    return {"lat": float(location["lat"]), "lng": float(location["lng"])}
            logger.warning("Google geocoding returned status %s", data.get("status"))
        except Exception as exc:
            logger.warning("Google geocoding failed: %s", type(exc).__name__)

    try:
        params = urllib.parse.urlencode({"q": address_str, "format": "json", "limit": 1})
        request = urllib.request.Request(
            f"https://nominatim.openstreetmap.org/search?{params}",
            headers={"User-Agent": "GENOMIX-AI-Health/1.0"},
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
        if data:
            return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"])}
    except Exception as exc:
        logger.warning("OSM geocoding failed: %s", type(exc).__name__)
    return None


def search_nearby_hospitals(lat: float, lng: float) -> List[Dict[str, Any]]:
    """Search real hospital providers and return facilities nearest first."""
    google_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if google_key:
        google_results = _search_google_places(lat, lng, google_key)
        if google_results:
            return google_results

    hospitals: List[Dict[str, Any]] = []
    current_distance = 10
    max_distance = 50

    while current_distance <= max_distance and len(hospitals) < 5:
        try:
            distance_meters = current_distance * 1000
            query = f"""
            [out:json][timeout:15];
            (node["amenity"="hospital"](around:{distance_meters},{lat},{lng});
             way["amenity"="hospital"](around:{distance_meters},{lat},{lng}););
            out center 50;
            """
            request = urllib.request.Request(
                "https://overpass-api.de/api/interpreter",
                data=query.encode("utf-8"),
                headers={"User-Agent": "GENOMIX-AI-Health/1.0"},
            )
            with urllib.request.urlopen(request, timeout=20) as response:
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
            
            if len(hospitals) < 5:
                current_distance += 20
            else:
                break
                
        except Exception as exc:
            logger.warning("Overpass hospital search failed: %s", type(exc).__name__)
            break

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
            timeout=10,
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
