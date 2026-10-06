import json
import logging
from typing import Dict, Any, List, Optional
from app.database.connection import get_db

logger = logging.getLogger(__name__)

# Standard Specialties requested in specs
DOCTOR_SPECIALTIES = [
    "General Physician",
    "Cardiologist",
    "Neurologist",
    "Dermatologist",
    "Orthopedic Doctor",
    "Gynecologist",
    "Pediatrician"
]

def save_or_get_hospitals_batch(hospitals_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Optimized batch lookup/insertion for hospitals and doctor seeding using a single DB connection.
    Deduplicates hospitals by external_place_id, name+coords, or name+address.
    """
    if not hospitals_list:
        return hospitals_list

    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Load existing hospitals map by place_id, name+coords, and name+address
        cursor.execute("SELECT id, external_place_id, name, address, city, latitude as lat, longitude as lng FROM hospitals")
        existing_rows = cursor.fetchall()
        
        place_map = {}
        coord_map = {}
        name_addr_map = {}
        
        for r in existing_rows:
            h_id = r['id']
            if r.get('external_place_id'):
                place_map[r['external_place_id']] = r
            if r.get('name') and r.get('lat') is not None and r.get('lng') is not None:
                ckey = (r['name'].strip().lower(), round(float(r['lat']), 4), round(float(r['lng']), 4))
                coord_map[ckey] = r
            if r.get('name') and r.get('address'):
                nakey = (r['name'].strip().lower(), r['address'].strip().lower())
                name_addr_map[nakey] = r

        for hosp_data in hospitals_list:
            ext_id = hosp_data.get('external_place_id')
            h_name = hosp_data.get('name', 'Hospital').strip()
            h_lat = hosp_data.get('lat')
            h_lng = hosp_data.get('lng')
            h_addr = (hosp_data.get('address') or '').strip()

            matched_existing = None
            if ext_id and ext_id in place_map:
                matched_existing = place_map[ext_id]
            elif h_lat is not None and h_lng is not None and (h_name.lower(), round(float(h_lat), 4), round(float(h_lng), 4)) in coord_map:
                matched_existing = coord_map[(h_name.lower(), round(float(h_lat), 4), round(float(h_lng), 4))]
            elif h_addr and (h_name.lower(), h_addr.lower()) in name_addr_map:
                matched_existing = name_addr_map[(h_name.lower(), h_addr.lower())]

            if matched_existing:
                h_id = matched_existing['id']
                hosp_data['db_id'] = h_id
                # Update city if existing record lacked city or if new city is provided and valid
                if hosp_data.get('city') and not matched_existing.get('city'):
                    upd_cursor = conn.cursor()
                    upd_cursor.execute("UPDATE hospitals SET city = %s WHERE id = %s", (hosp_data['city'], h_id))
                    upd_cursor.close()
                if ext_id and not matched_existing.get('external_place_id'):
                    upd_cursor = conn.cursor()
                    upd_cursor.execute("UPDATE hospitals SET external_place_id = %s WHERE id = %s", (ext_id, h_id))
                    upd_cursor.close()
                
                # Check if doctors exist for this hospital
                doc_check = conn.cursor(dictionary=True)
                doc_check.execute("SELECT COUNT(*) as dcnt FROM doctors WHERE hospital_id = %s", (h_id,))
                cnt_row = doc_check.fetchone()
                doc_check.close()
                if not cnt_row or cnt_row['dcnt'] == 0:
                    _seed_doctors_with_cursor(cursor, h_id)
                continue

            query = """
                INSERT INTO hospitals (external_place_id, name, address, city, state, country, postal_code, latitude, longitude, phone, opening_hours)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                ext_id,
                h_name,
                h_addr,
                hosp_data.get('city', ''),
                hosp_data.get('state', ''),
                hosp_data.get('country', ''),
                hosp_data.get('postal_code', ''),
                h_lat,
                h_lng,
                hosp_data.get('phone'),
                hosp_data.get('opening_hours')
            ))
            hosp_id = cursor.lastrowid
            hosp_data['db_id'] = hosp_id
            
            # Update local lookup maps
            new_rec = {'id': hosp_id, 'external_place_id': ext_id, 'name': h_name, 'address': h_addr, 'city': hosp_data.get('city', ''), 'lat': h_lat, 'lng': h_lng}
            if ext_id:
                place_map[ext_id] = new_rec
            if h_lat is not None and h_lng is not None:
                coord_map[(h_name.lower(), round(float(h_lat), 4), round(float(h_lng), 4))] = new_rec
            if h_addr:
                name_addr_map[(h_name.lower(), h_addr.lower())] = new_rec

            _seed_doctors_with_cursor(cursor, hosp_id)
        
        cursor.close()

    return hospitals_list


def save_or_get_hospital(hosp_data: Dict[str, Any]) -> int:
    """Inserts hospital into DB if not existing, or returns existing ID (single connection)."""
    res = save_or_get_hospitals_batch([hosp_data])
    return res[0].get('db_id', 1)


def get_hospital_by_id(hospital_id: int) -> Optional[Dict[str, Any]]:
    query = "SELECT * FROM hospitals WHERE id = %s"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (hospital_id,))
        res = cursor.fetchone()
        cursor.close()
        return res


def get_doctors_by_hospital_id(hospital_id: int) -> List[Dict[str, Any]]:
    query = "SELECT * FROM doctors WHERE hospital_id = %s ORDER BY id ASC"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (hospital_id,))
        results = cursor.fetchall()
        for r in results:
            if r.get('available_slots_json'):
                try:
                    r['available_slots'] = json.loads(r['available_slots_json'])
                except Exception:
                    r['available_slots'] = ["09:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"]
        cursor.close()
        return results


def get_hospitals_from_db_near(lat: float, lng: float, radius_km: float = 50.0) -> List[Dict[str, Any]]:
    """Retrieves hospitals already in DB near coordinates, ordered by distance."""
    import math
    def _dist(lat1, lon1, lat2, lon2):
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        v = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        return r * 2 * math.atan2(math.sqrt(v), math.sqrt(1 - v))

    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id as db_id, external_place_id, name, address, city, state, country, postal_code, latitude as lat, longitude as lng, phone, opening_hours FROM hospitals WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        rows = cursor.fetchall()
        cursor.close()

    nearby = []
    for r in rows:
        h_lat = r.get('lat')
        h_lng = r.get('lng')
        if h_lat is not None and h_lng is not None:
            dist = round(_dist(lat, lng, float(h_lat), float(h_lng)), 1)
            if dist <= radius_km:
                r['distance_km'] = dist
                r['lat'] = float(h_lat)
                r['lng'] = float(h_lng)
                nearby.append(r)

    return sorted(nearby, key=lambda x: x['distance_km'])


def _seed_doctors_with_cursor(cursor, hospital_id: int):
    """Bulk insert doctor seeds using an active database cursor."""
    sample_doctors = [
        ("Dr. Alexander Wright", "Cardiologist", "MBBS, MD (Cardiology), FACC", 12, "Monday - Friday", json.dumps(["09:00 AM", "10:30 AM", "01:30 PM", "03:30 PM"]), "In-person & Video", "https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=300&q=80"),
        ("Dr. Priya Sharma", "Genomic Medicine & Physician", "MBBS, DNB (Internal Medicine)", 8, "Monday - Saturday", json.dumps(["10:00 AM", "11:30 AM", "02:00 PM", "04:30 PM"]), "In-person & Video", "https://images.unsplash.com/photo-1594824813566-88855ce78961?auto=format&fit=crop&w=300&q=80"),
        ("Dr. Marcus Vance", "Neurologist", "MBBS, DM (Neurology)", 15, "Tuesday, Thursday, Saturday", json.dumps(["09:30 AM", "11:00 AM", "03:00 PM"]), "In-person", "https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&w=300&q=80"),
        ("Dr. Ananya Reddy", "Pediatrician", "MBBS, MD (Pediatrics)", 7, "Monday - Friday", json.dumps(["10:00 AM", "12:00 PM", "02:30 PM", "05:00 PM"]), "In-person & Video", "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=300&q=80"),
        ("Dr. David Chen", "Dermatologist & Oncologist", "MBBS, MD (Dermatology)", 10, "Monday, Wednesday, Friday", json.dumps(["09:00 AM", "11:30 AM", "03:00 PM", "04:00 PM"]), "In-person & Video", "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?auto=format&fit=crop&w=300&q=80")
    ]

    query = """
        INSERT INTO doctors (hospital_id, full_name, specialty, qualification, experience_years, availability_days, available_slots_json, consultation_type, photo_url, is_demo_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
    """
    for doc in sample_doctors:
        cursor.execute(query, (hospital_id, *doc))


def seed_doctors_for_hospital(hospital_id: int, hospital_name: str):
    """Seeds 4-5 realistic doctor profiles."""
    with get_db() as conn:
        cursor = conn.cursor()
        _seed_doctors_with_cursor(cursor, hospital_id)
        cursor.close()

