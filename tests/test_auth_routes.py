import unittest
from app import create_app
from app.database.queries import get_user_by_username


class TestAuthRoutes(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_welcome_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"GENOMIX", response.data)
        self.assertIn(b"AI-Powered", response.data)
        self.assertIn(b"Complete DNA Multi-Module Analysis", response.data)

    def test_login_page_loads(self):
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome Back", response.data)
        self.assertIn(b"password-toggle-btn", response.data)

    def test_register_page_loads_with_steps(self):
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Account Credentials", response.data)
        self.assertIn(b"Personal Details", response.data)
        self.assertIn(b"step-1-pane", response.data)
        self.assertIn(b"step-2-pane", response.data)

    def test_complete_two_step_registration_and_login_flow(self):
        import uuid
        from unittest.mock import patch

        test_uid = uuid.uuid4().hex[:6]
        test_username = f"rosalind_{test_uid}"
        test_email = f"rosalind_{test_uid}@lab.org"

        fake_user = {
            "id": 1,
            "username": test_username,
            "email": test_email,
            "password_hash": "pbkdf2:sha256:260000$fake$hash",
            "full_name": "Dr. Rosalind Franklin",
            "role": "researcher",
            "country": "United Kingdom"
        }

        with patch('app.routes.auth.get_user_by_username', return_value=None), \
             patch('app.routes.auth.get_user_by_email', return_value=None), \
             patch('app.routes.auth.create_user', return_value=1), \
             patch('app.routes.auth.get_user_by_username_or_email', return_value=fake_user), \
             patch('app.routes.auth.check_password_hash', return_value=True), \
             patch('app.routes.dashboard.get_user_dashboard_stats', return_value={"total_sequences": 0, "total_analyses": 0, "total_mutations_detected": 0, "total_classifications": 0, "total_disease_predictions": 0, "total_reports": 0, "total_complete_analyses": 0, "recent_activities": []}):

            # 1. Register with Step 1 + Step 2 fields
            reg_payload = {
                # Step 1
                "email": test_email,
                "username": test_username,
                "password": "SecretPassword123!",
                "confirm_password": "SecretPassword123!",
                # Step 2
                "full_name": "Dr. Rosalind Franklin",
                "date_of_birth": "1920-07-25",
                "gender": "Female",
                "phone": "+44 20 7946 0919",
                "country": "United Kingdom",
                "state": "England",
                "city": "London",
                "address": "104 Healthcare Boulevard",
                "postal_code": "560001"
            }

            reg_resp = self.client.post('/auth/register', data=reg_payload, follow_redirects=False)
            self.assertEqual(reg_resp.status_code, 302)
            self.assertIn('/auth/login', reg_resp.headers['Location'])

            # 2. Login
            login_payload = {
                "identifier": test_username,
                "password": "SecretPassword123!"
            }
            login_resp = self.client.post('/auth/login', data=login_payload, follow_redirects=False)
            self.assertEqual(login_resp.status_code, 302)
            self.assertIn('/dashboard', login_resp.headers['Location'])

            # 3. Access protected dashboard with session
            dash_resp = self.client.get('/dashboard/')
            self.assertEqual(dash_resp.status_code, 200)

            # 4. Logout
            logout_resp = self.client.get('/auth/logout', follow_redirects=False)
            self.assertEqual(logout_resp.status_code, 302)
            self.assertIn('/auth/login', logout_resp.headers['Location'])

        # 5. Accessing dashboard after logout redirects to login
        dash_after_resp = self.client.get('/dashboard/', follow_redirects=False)
        self.assertEqual(dash_after_resp.status_code, 302)
        self.assertIn('/auth/login', dash_after_resp.headers['Location'])

    def test_unauthorized_dashboard_redirect(self):
        response = self.client.get('/dashboard/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.headers['Location'])


if __name__ == '__main__':
    unittest.main()
