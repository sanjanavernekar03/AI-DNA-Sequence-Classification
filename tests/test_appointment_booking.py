import unittest
import datetime
from app import create_app
from app.database.connection import get_db
from app.services.booking_service import create_appointment, get_user_appointments


class TestAppointmentBooking(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'raju45'

    def test_end_to_end_appointment_creation(self):
        """Test complete appointment creation in MySQL and retrieval in My Appointments."""
        target_date = (datetime.date.today() + datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        
        # 1. HTTP POST booking request
        res = self.client.post('/appointments/book', data={
            'hospital_id': 1,
            'doctor_id': 1,
            'appointment_date': target_date,
            'appointment_time': '11:00 AM',
            'reason_for_visit': 'Cardiology Consultation',
            'patient_name': 'Raju Patient',
            'phone': '9876543210',
            'patient_email': 'raju2@gmail.com',
            'notes': 'Unit test appointment booking'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Appointment Confirmed Successfully", res.data)
        self.assertIn(b"My Appointments", res.data)
        self.assertIn(b"Cardiology Consultation", res.data)

        # 2. Database verification directly in MySQL
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM appointments WHERE user_id = %s AND reason_for_visit = %s ORDER BY id DESC LIMIT 1",
                (1, 'Cardiology Consultation')
            )
            record = cursor.fetchone()
            cursor.close()

        self.assertIsNotNone(record)
        self.assertEqual(record['patient_name'], 'Raju Patient')
        self.assertEqual(record['patient_email'], 'raju2@gmail.com')
        self.assertEqual(record['status'], 'Confirmed')

    def test_duplicate_slot_validation(self):
        """Test duplicate doctor/slot booking returns friendly error."""
        target_date = (datetime.date.today() + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
        
        res1 = create_appointment(
            user_id=1, hospital_id=1, doctor_id=1,
            appointment_date_str=target_date, appointment_time='02:00 PM',
            reason_for_visit='First Visit', patient_name='Raju', phone='9876543210'
        )
        self.assertTrue(res1['success'])

        # Duplicate slot booking attempt
        res2 = create_appointment(
            user_id=1, hospital_id=1, doctor_id=1,
            appointment_date_str=target_date, appointment_time='02:00 PM',
            reason_for_visit='Duplicate Attempt', patient_name='Raju', phone='9876543210'
        )
        self.assertFalse(res2['success'])
        self.assertIn('already booked', res2['error'])


if __name__ == '__main__':
    unittest.main()
