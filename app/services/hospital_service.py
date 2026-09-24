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

def save_or_get_hospital(hosp_data: Dict[str, Any]) -> int:
    """Inserts hospital into DB if not existing, or returns existing ID."""
    ext_id = hosp_data.get('external_place_id')
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        if ext_id:
            cursor.execute("SELECT id FROM hospitals WHERE external_place_id = %s", (ext_id,))
            row = cursor.fetchone()
            cursor.close()
            if row:
                return row['id']

        # Insert new hospital record
        query = """
            INSERT INTO hospitals (external_place_id, name, address, city, state, country, postal_code, latitude, longitude, phone, opening_hours)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor = conn.cursor()
        cursor.execute(query, (
            ext_id,
            hosp_data['name'],
            hosp_data['address'],
            hosp_data.get('city', ''),
            hosp_data.get('state', ''),
            hosp_data.get('country', ''),
            hosp_data.get('postal_code', ''),
            hosp_data.get('lat'),
            hosp_data.get('lng'),
            hosp_data.get('phone'),
            hosp_data.get('opening_hours')
        ))
        hosp_id = cursor.lastrowid
        cursor.close()
    
    # Seed 4-5 doctors for this hospital automatically outside transaction block
    seed_doctors_for_hospital(hosp_id, hosp_data['name'])
    return hosp_id


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


def seed_doctors_for_hospital(hospital_id: int, hospital_name: str):
    """
    Seeds 4-5 realistic doctor profiles labeled clearly as "Demo / Sample Doctor Profiles"
    as required for academic demonstration purposes.
    """
    sample_doctors = [
        {
            "full_name": "Dr. Alexander Wright",
            "specialty": "Cardiologist",
            "qualification": "MBBS, MD (Cardiology), FACC",
            "experience_years": 12,
            "availability_days": "Monday - Friday",
            "slots": ["09:00 AM", "10:30 AM", "01:30 PM", "03:30 PM"],
            "consultation_type": "In-person & Video",
            "photo_url": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=300&q=80"
        },
        {
            "full_name": "Dr. Priya Sharma",
            "specialty": "Genomic Medicine & Physician",
            "qualification": "MBBS, DNB (Internal Medicine)",
            "experience_years": 8,
            "availability_days": "Monday - Saturday",
            "slots": ["10:00 AM", "11:30 AM", "02:00 PM", "04:30 PM"],
            "consultation_type": "In-person & Video",
            "photo_url": "https://images.unsplash.com/photo-1594824813566-88855ce78961?auto=format&fit=crop&w=300&q=80"
        },
        {
            "full_name": "Dr. Marcus Vance",
            "specialty": "Neurologist",
            "qualification": "MBBS, DM (Neurology)",
            "experience_years": 15,
            "availability_days": "Tuesday, Thursday, Saturday",
            "slots": ["09:30 AM", "11:00 AM", "03:00 PM"],
            "consultation_type": "In-person",
            "photo_url": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&w=300&q=80"
        },
        {
            "full_name": "Dr. Ananya Reddy",
            "specialty": "Pediatrician",
            "qualification": "MBBS, MD (Pediatrics)",
            "experience_years": 7,
            "availability_days": "Monday - Friday",
            "slots": ["10:00 AM", "12:00 PM", "02:30 PM", "05:00 PM"],
            "consultation_type": "In-person & Video",
            "photo_url": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=300&q=80"
        },
        {
            "full_name": "Dr. David Chen",
            "specialty": "Dermatologist & Oncologist",
            "qualification": "MBBS, MD (Dermatology)",
            "experience_years": 10,
            "availability_days": "Monday, Wednesday, Friday",
            "slots": ["09:00 AM", "11:30 AM", "03:00 PM", "04:00 PM"],
            "consultation_type": "In-person & Video",
            "photo_url": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?auto=format&fit=crop&w=300&q=80"
        }
    ]

    query = """
        INSERT INTO doctors (hospital_id, full_name, specialty, qualification, experience_years, availability_days, available_slots_json, consultation_type, photo_url, is_demo_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        for doc in sample_doctors:
            cursor.execute(query, (
                hospital_id,
                doc['full_name'],
                doc['specialty'],
                doc['qualification'],
                doc['experience_years'],
                doc['availability_days'],
                json.dumps(doc['slots']),
                doc['consultation_type'],
                doc['photo_url']
            ))
        cursor.close()
