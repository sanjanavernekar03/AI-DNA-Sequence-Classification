import datetime
import logging
from typing import Dict, Any, List, Optional
from app.database.connection import get_db

logger = logging.getLogger(__name__)

def create_appointment(
    user_id: int,
    hospital_id: int,
    doctor_id: int,
    appointment_date_str: str,
    appointment_time: str,
    reason_for_visit: str,
    patient_name: str,
    phone: str,
    patient_email: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a new doctor appointment with validation.
    Checks for past dates and duplicate bookings for the same doctor at the same date & time slot.
    """
    # 1. Date Validation
    try:
        appt_date = datetime.datetime.strptime(appointment_date_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        if appt_date < today:
            return {"success": False, "error": "Appointment date cannot be in the past."}
    except ValueError:
        return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}

    # If patient_email is empty, attempt to resolve from user table
    if not patient_email or not patient_email.strip():
        try:
            with get_db() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
                user_rec = cursor.fetchone()
                cursor.close()
                if user_rec and user_rec.get('email'):
                    patient_email = user_rec['email']
        except Exception as exc:
            logger.warning("Could not fetch user email: %s", exc)

    final_email = (patient_email or "").strip()

    # 2. Check for duplicate booking for same doctor, date, and slot
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id FROM appointments 
            WHERE doctor_id = %s AND appointment_date = %s AND appointment_time = %s AND status != 'Cancelled'
            """,
            (doctor_id, appt_date, appointment_time)
        )
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            return {"success": False, "error": "This doctor is already booked for the selected date and time slot. Please choose another slot."}

        # 3. Create Appointment
        query = """
            INSERT INTO appointments (user_id, hospital_id, doctor_id, appointment_date, appointment_time, reason_for_visit, patient_name, patient_email, phone, notes, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Confirmed')
        """
        cursor = conn.cursor()
        cursor.execute(query, (
            user_id,
            hospital_id,
            doctor_id,
            appt_date,
            appointment_time,
            reason_for_visit.strip(),
            patient_name.strip(),
            final_email,
            phone.strip(),
            notes.strip() if notes else None
        ))
        appt_id = cursor.lastrowid
        cursor.close()

        return {"success": True, "appointment_id": appt_id}


def get_user_appointments(user_id: int) -> List[Dict[str, Any]]:
    query = """
        SELECT a.*, h.name as hospital_name, h.address as hospital_address, d.full_name as doctor_name, d.specialty as doctor_specialty, d.photo_url as doctor_photo
        FROM appointments a
        JOIN hospitals h ON a.hospital_id = h.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.user_id = %s
        ORDER BY a.appointment_date DESC, a.created_at DESC
    """
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        cursor.close()
        return results


def cancel_user_appointment(appointment_id: int, user_id: int) -> bool:
    query = "UPDATE appointments SET status = 'Cancelled' WHERE id = %s AND user_id = %s"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (appointment_id, user_id))
        affected = cursor.rowcount > 0
        cursor.close()
        return affected
