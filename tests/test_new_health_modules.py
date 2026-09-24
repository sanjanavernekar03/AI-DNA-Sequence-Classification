import unittest
from unittest.mock import patch
from app import create_app
from app.services.chatbot_service import ChatbotServiceError

class TestNewHealthModules(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_chatbot_api_unauthorized(self):
        resp = self.client.post('/api/chatbot/chat', json={'message': 'Hello'}, follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/auth/login', resp.headers['Location'])

    def test_chatbot_api_authorized(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
            sess['full_name'] = 'Test User'

        with patch('app.routes.auth.get_user_by_id', return_value={'id': 1, 'full_name': 'Test User'}), \
             patch('app.routes.chatbot.get_db'), \
             patch('app.routes.chatbot.get_chatbot_response', return_value={
                 'response': 'DNA is genetic material.',
                 'disclaimer': 'Educational purposes only.',
                 'language': 'en'
             }) as mock_chat:
            resp = self.client.post('/api/chatbot/chat', json={'message': 'What is DNA sequence processing?', 'language': 'en'})
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn('response', data)
            self.assertNotIn('disclaimer', data)
            mock_chat.assert_called_once()

    def test_chatbot_provider_failure_is_visible(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('app.routes.auth.get_user_by_id', return_value={'id': 1, 'full_name': 'Test User'}), \
             patch('app.routes.chatbot.get_chatbot_response', side_effect=ChatbotServiceError('provider unavailable')):
            resp = self.client.post('/api/chatbot/chat', json={'message': 'What is DNA?'})
            self.assertEqual(resp.status_code, 503)
            self.assertEqual(resp.get_json()['error'], 'provider unavailable')

    def test_health_guidance_multilingual(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('app.routes.auth.get_user_by_id', return_value={'id': 1, 'full_name': 'Test User'}):
            # English test
            resp_en = self.client.post('/health-guidance/api/generate', json={'problem': 'I feel tired frequently', 'language': 'en'})
            self.assertEqual(resp_en.status_code, 200)
            data_en = resp_en.get_json()
            self.assertIn('healthy_foods', data_en)
            self.assertIn('exercise_suggestions', data_en)

            # Hindi test
            resp_hi = self.client.post('/health-guidance/api/generate', json={'problem': 'थकान महसूस होती है', 'language': 'hi'})
            self.assertEqual(resp_hi.status_code, 200)
            data_hi = resp_hi.get_json()
            self.assertIn('healthy_foods', data_hi)

            # Kannada test
            resp_kn = self.client.post('/health-guidance/api/generate', json={'problem': 'ಆಯಾಸವಾಗುತ್ತದೆ', 'language': 'kn'})
            self.assertEqual(resp_kn.status_code, 200)
            data_kn = resp_kn.get_json()
            self.assertIn('healthy_foods', data_kn)

    def test_hospital_recommendations_route(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1

        user_mock = {
            'id': 1,
            'full_name': 'Test User',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'country': 'India',
            'address': '104 Tech Boulevard',
            'postal_code': '560001'
        }

        with patch('app.routes.auth.get_user_by_id', return_value=user_mock), \
             patch('app.routes.hospitals.save_or_get_hospital', return_value=1):
            resp = self.client.get('/hospitals/')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Hospital Recommendations", resp.data)

    @patch('app.services.maps_service.os.getenv', return_value='google-test-key')
    @patch('app.services.maps_service.urllib.request.urlopen')
    def test_hospital_provider_results_are_distance_sorted(self, mock_urlopen, _mock_env):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"status":"OK","results":[' \
                    b'{"place_id":"far","name":"Far Hospital","vicinity":"Far St","geometry":{"location":{"lat":12.02,"lng":77.59}}},' \
                    b'{"place_id":"near","name":"Near Hospital","vicinity":"Near St","geometry":{"location":{"lat":12.001,"lng":77.59}}}' \
                    b']}'

        mock_urlopen.return_value = FakeResponse()
        from app.services.maps_service import search_nearby_hospitals

        results = search_nearby_hospitals(12.0, 77.59, radius_km=5)
        self.assertEqual([result['name'] for result in results], ['Near Hospital', 'Far Hospital'])
        self.assertLessEqual(results[0]['distance_km'], results[1]['distance_km'])
        self.assertTrue(all(not result['external_place_id'].startswith('hosp_seed_') for result in results))

    def test_appointment_booking_flow(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1

        mock_hosp = {'id': 1, 'name': 'Genomix Medical Center', 'address': '104 Health St'}
        mock_doc = {'id': 1, 'full_name': 'Dr. Wright', 'specialty': 'Cardiologist', 'available_slots': ['10:00 AM']}

        with patch('app.routes.auth.get_user_by_id', return_value={'id': 1, 'full_name': 'Test User'}), \
             patch('app.routes.appointments.get_hospital_by_id', return_value=mock_hosp), \
             patch('app.routes.appointments.get_doctors_by_hospital_id', return_value=[mock_doc]), \
             patch('app.routes.appointments.create_appointment', return_value={'success': True, 'appointment_id': 10}):

            payload = {
                'hospital_id': 1,
                'doctor_id': 1,
                'appointment_date': '2026-10-15',
                'appointment_time': '10:00 AM',
                'reason_for_visit': 'Cardiovascular review',
                'patient_name': 'Test User',
                'phone': '+1555000111'
            }

            resp = self.client.post('/appointments/book', data=payload, follow_redirects=False)
            self.assertEqual(resp.status_code, 302)
            self.assertIn('/appointments/my-appointments', resp.headers['Location'])


if __name__ == '__main__':
    unittest.main()
