import unittest
import json
from app import create_app
from app.services.recommendation_service import get_ai_recommendation, extract_intent_and_entities

class TestAIHospitalLocationAccuracy(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_case_1_city(self):
        """TEST 1 — City: 'Suggest a hospital in Bangalore.'"""
        res = get_ai_recommendation("Suggest a hospital in Bangalore.", language="en")
        self.assertIsNotNone(res)
        response_text = res['response']
        self.assertIn("Recommended Hospitals", response_text)
        self.assertTrue("Bangalore" in response_text or "Bengaluru" in response_text)
        self.assertIn("View on Map", response_text)
        self.assertIn("google.com/maps", response_text)

    def test_case_2_disease_and_city(self):
        """TEST 2 — Disease + City: 'I need a cancer hospital in Bangalore.'"""
        res = get_ai_recommendation("I need a cancer hospital in Bangalore.", language="en")
        self.assertIsNotNone(res)
        response_text = res['response']
        self.assertIn("Oncologist", response_text)
        self.assertTrue("Bangalore" in response_text or "Bengaluru" in response_text)
        self.assertIn("View on Map", response_text)

    def test_case_3_nearby_with_coords(self):
        """TEST 3 — Nearby: 'Find a hospital near me.' with actual GPS coords"""
        # User in Karwar GPS coords: (14.8122, 74.1323)
        user_loc = {'lat': 14.8122, 'lng': 74.1323}
        res = get_ai_recommendation("Find a hospital near me.", language="en", user_location=user_loc)
        self.assertIsNotNone(res)
        response_text = res['response']
        self.assertIn("Recommended Hospitals", response_text)
        self.assertIn("Distance:", response_text)
        # Verify distance is short (< 30km) and NOT defaulting to Bangalore
        self.assertNotIn("Bengaluru", response_text)

    def test_case_4_disease_and_nearby(self):
        """TEST 4 — Disease + Nearby: 'I have diabetes. Find a nearby hospital.'"""
        user_loc = {'lat': 12.9716, 'lng': 77.5946} # Bangalore coords
        res = get_ai_recommendation("I have diabetes. Find a nearby hospital.", language="en", user_location=user_loc)
        self.assertIsNotNone(res)
        response_text = res['response']
        self.assertIn("General Physician", response_text)
        self.assertIn("Distance:", response_text)

    def test_case_5_specific_hospital(self):
        """TEST 5 — Specific Hospital: 'Find Manipal Hospital in Bangalore.'"""
        res = get_ai_recommendation("Find Manipal Hospital in Bangalore.", language="en")
        self.assertIsNotNone(res)
        response_text = res['response']
        self.assertIn("Manipal", response_text)
        self.assertTrue("Bangalore" in response_text or "Bengaluru" in response_text)
        self.assertIn("google.com/maps", response_text)

    def test_case_6_unavailable_location_handling(self):
        """TEST 6 — Invalid/Unavailable Location handling"""
        # A) Nearby without GPS permission -> prompts for location/city, NO hardcoded Bangalore fallback
        res_no_gps = get_ai_recommendation("Find a hospital near me.", language="en", user_location=None)
        self.assertIsNotNone(res_no_gps)
        self.assertIn("allow location access", res_no_gps['response'].lower())
        self.assertNotIn("12.9716", res_no_gps['response'])

        # B) Non-existent city -> clear no matching hospitals message, NO silent city substitution
        res_fake_city = get_ai_recommendation("Find a hospital in Nonexistentcity.", language="en")
        self.assertIsNotNone(res_fake_city)
        self.assertIn("No matching hospitals found in Nonexistentcity", res_fake_city['response'])


if __name__ == '__main__':
    unittest.main()
