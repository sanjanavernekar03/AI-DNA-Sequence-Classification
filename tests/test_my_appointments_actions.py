import unittest
from app import create_app

class TestMyAppointmentsActions(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_my_appointments_actions_column_rendering(self):
        with self.app.test_request_context('/appointments/my-appointments'):
            from flask import render_template
            test_appts = [
                {
                    'id': 101,
                    'status': 'Confirmed',
                    'doctor_name': 'Dr. Alexander Wright',
                    'doctor_specialty': 'Cardiologist',
                    'hospital_name': 'Sondekoppa Government Hospital',
                    'hospital_address': 'Sondekoppa',
                    'appointment_date': '2026-10-15',
                    'appointment_time': '10:00 AM',
                    'patient_name': 'Raju',
                    'phone': '9876543210',
                    'reason_for_visit': 'General Checkup',
                    'doctor_photo': None
                },
                {
                    'id': 102,
                    'status': 'Cancelled',
                    'doctor_name': 'Dr. Alexander Wright',
                    'doctor_specialty': 'Cardiologist',
                    'hospital_name': 'Sondekoppa Government Hospital',
                    'hospital_address': 'Sondekoppa',
                    'appointment_date': '2026-10-15',
                    'appointment_time': '10:00 AM',
                    'patient_name': 'Raju',
                    'phone': '9876543210',
                    'reason_for_visit': 'General Checkup',
                    'doctor_photo': None
                }
            ]
            html_output = render_template('appointments/my_appointments.html', appointments=test_appts)

            # 1. Ensure no garbled 'â€”' exists in rendered HTML
            self.assertNotIn('â€”', html_output)

            # 2. Check that Confirmed appointment has Cancel button
            self.assertIn('Cancel', html_output)
            self.assertIn('action="/appointments/cancel/101"', html_output)

            # 3. Check that Cancelled appointment has auto_d5fd8e span with clean em-dash '—'
            self.assertIn('data-i18n="auto_d5fd8e">—</span>', html_output)

if __name__ == '__main__':
    unittest.main()
