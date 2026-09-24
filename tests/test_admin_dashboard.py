import unittest
from unittest.mock import patch

from app import create_app


class TestAdminDashboard(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_dashboard_renders_all_live_metric_labels(self):
        stats = {
            'users': 12,
            'analyses': 34,
            'predictions': 8,
            'mutation_analyses': 5,
            'reports': 7,
            'chatbot_conversations': 19,
        }
        with self.client.session_transaction() as session:
            session['admin_id'] = 1
            session['admin_username'] = 'admin'
            session['admin_name'] = 'System Admin'

        def fake_one(sql, params=()):
            if 'admin_settings' in sql:
                return {'setting_value': 'light'}
            return {'c': 1}

        with patch('app.routes.admin._one', side_effect=fake_one), \
             patch('app.routes.admin._all', side_effect=[[], [], []]):
            response = self.client.get('/admin/dashboard')

        self.assertEqual(response.status_code, 200)
        for label in (
            'Total Users',
            'Total DNA Analyses',
            'Total Predictions',
            'Total Mutation Analyses',
            'Total Reports',
            'Chatbot Conversations',
        ):
            self.assertIn(label.encode(), response.data)


if __name__ == '__main__':
    unittest.main()
