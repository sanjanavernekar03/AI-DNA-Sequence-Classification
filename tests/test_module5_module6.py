import unittest
from app import create_app
from app.services.disease_service import process_disease_prediction
from app.services.visualization_service import generate_visualization_payload
from app.database.queries import get_disease_prediction_by_id, get_visualization_by_id


class TestModule5AndModule6(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'raju45'

    def test_module5_disease_prediction_flow(self):
        """Test Module 5 complete flow: prediction -> DB save -> retrieve."""
        test_seq = "ACTCCTGTGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGGCTGCTGGTGGTCTACCCTTGGACCCAGAGGTTCTTTGAGTCCTTTGGGGATCTGTCCACTCCTGATGCTGTTATGGGCAACCCTAAGGTGAAGGCTCATGGCAAGAAAGTGCTCGGTGCCTTTAGTGATGGCCTGGCT"
        
        # 1. Direct Service Test
        res = process_disease_prediction(user_id=1, sequence=test_seq, sequence_name="Unit Test Sequence")
        self.assertIsNotNone(res.get("id"))
        self.assertIn("predicted_category", res)
        self.assertIn("probability", res)
        self.assertIn("probabilities", res)
        self.assertIn("risk_category", res)

        # 2. Database Retrieval Test
        db_rec = get_disease_prediction_by_id(res["id"], user_id=1)
        self.assertIsNotNone(db_rec)
        self.assertEqual(db_rec["sequence_name"], "Unit Test Sequence")
        self.assertIn("probabilities", db_rec)
        self.assertEqual(len(db_rec["probabilities"]), 5)

        # 3. HTTP GET & POST Route Test
        get_res = self.client.get('/analysis/disease/')
        self.assertEqual(get_res.status_code, 200)

        post_res = self.client.post('/analysis/disease/', data={
            'sequence_name': 'HTTP Test Sequence',
            'sequence': test_seq
        }, follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)
        self.assertIn(b"Genomic Disease Risk assessment completed", post_res.data)

        # 4. View Route Test
        view_res = self.client.get(f'/analysis/disease/view/{res["id"]}')
        self.assertEqual(view_res.status_code, 200)

    def test_module6_dna_visualization_flow(self):
        """Test Module 6 complete flow: payload generation -> DB save -> HTTP endpoints."""
        test_seq = "ATGCGATCGATCGATCGATCGATC"

        # 1. Payload Generation
        payload = generate_visualization_payload(test_seq)
        self.assertIn("nucleotide_bar", payload)
        self.assertIn("nucleotide_doughnut", payload)
        self.assertIn("gc_vs_at", payload)
        self.assertIn("kmer_chart", payload)

        # 2. HTTP GET & POST Route Test
        get_res = self.client.get('/analysis/visualization/')
        self.assertEqual(get_res.status_code, 200)

        post_res = self.client.post('/analysis/visualization/', data={
            'sequence_name': 'Viz Test Sequence',
            'sequence': test_seq
        }, follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)
        self.assertIn(b"Interactive DNA sequence visualizations generated successfully", post_res.data)

    def test_regression_modules_1_to_4(self):
        """Re-verify Modules 1 to 4 remain fully functional."""
        # Module 1 GET
        r1 = self.client.get('/analysis/sequence/')
        self.assertIn(r1.status_code, [200, 302])

        # Module 2 GET
        r2 = self.client.get('/analysis/similarity/')
        self.assertIn(r2.status_code, [200, 302])

        # Module 3 GET
        r3 = self.client.get('/analysis/mutation/')
        self.assertIn(r3.status_code, [200, 302])

        # Module 4 GET
        r4 = self.client.get('/analysis/classification/')
        self.assertIn(r4.status_code, [200, 302])

        # Dashboard GET
        r_dash = self.client.get('/dashboard/')
        self.assertEqual(r_dash.status_code, 200)


if __name__ == '__main__':
    unittest.main()
