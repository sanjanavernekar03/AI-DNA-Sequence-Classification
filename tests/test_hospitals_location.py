import unittest
from app import create_app
from app.services.maps_service import geocode_address, search_nearby_hospitals


class TestHospitalsLocationModes(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'raju45'

    def test_option_1_registered_address(self):
        """Test Option 1: Default to registered user address."""
        res = self.client.get('/hospitals/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Registered Address", res.data)
        self.assertIn(b"Hospitals", res.data)

    def test_option_2_current_location_coords(self):
        """Test Option 2: Device geolocation coordinates (lat/lng)."""
        res = self.client.get('/hospitals/?lat=12.9716&lng=77.5946')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"CURRENT LOCATION", res.data)

    def test_option_3_manual_location_search(self):
        """Test Option 3: Manual address or city search."""
        res = self.client.get('/hospitals/?location=Bengaluru%2C+Karnataka')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Bengaluru", res.data)

    def test_invalid_location_graceful_handling(self):
        """Test handling of invalid location search string without crashing."""
        res = self.client.get('/hospitals/?location=xyznonexistentplace999')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Unable to find location for", res.data)

    def test_geocode_address_index_safety(self):
        """Verify geocode_address safely handles empty/invalid results without IndexError."""
        # Empty string
        self.assertIsNone(geocode_address(""))
        self.assertIsNone(geocode_address("   "))
        # Non-existent query
        res = geocode_address("xyznonexistentplace9999999")
        # Should return None cleanly, not raise IndexError
        self.assertIsNone(res)


if __name__ == '__main__':
    unittest.main()
