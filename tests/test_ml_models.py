import unittest
from app.ml.predict_classification import predict_dna_class
from app.ml.predict_disease import predict_disease_risk
from app.services.dna_service import SAMPLE_SEQUENCES


class TestMLModels(unittest.TestCase):

    def test_dna_classification_prediction(self):
        seq = SAMPLE_SEQUENCES["cancer_tp53"]["sequence"]
        result = predict_dna_class(seq)
        self.assertIn("predicted_class", result)
        self.assertIsNotNone(result["predicted_class"])
        self.assertIn("confidence", result)
        self.assertGreater(result["confidence"], 0.0)
        self.assertIn("probabilities", result)
        self.assertGreater(len(result["probabilities"]), 0)

    def test_disease_risk_prediction_5_classes(self):
        # 1. Test Sickle Cell
        seq_sickle = SAMPLE_SEQUENCES["sickle_cell_hbb"]["sequence"]
        res_sickle = predict_disease_risk(seq_sickle)
        self.assertIn("predicted_category", res_sickle)
        self.assertIn("probability", res_sickle)
        self.assertIn("probabilities", res_sickle)
        self.assertEqual(len(res_sickle["probabilities"]), 5)
        self.assertIn("Healthy", res_sickle["probabilities"])
        self.assertIn("Cancer", res_sickle["probabilities"])
        self.assertIn("Sickle Cell Disease", res_sickle["probabilities"])
        self.assertIn("Cystic Fibrosis", res_sickle["probabilities"])
        self.assertIn("Huntington's Disease", res_sickle["probabilities"])

        # 2. Test Huntington's repeat sequence
        seq_hd = SAMPLE_SEQUENCES["huntingtons_disease_htt"]["sequence"]
        res_hd = predict_disease_risk(seq_hd)
        self.assertEqual(res_hd["predicted_category"], "Huntington's Disease")
        self.assertGreater(res_hd["probability"], 40.0)

        # 3. Test Healthy normal sequence
        seq_norm = SAMPLE_SEQUENCES["healthy_normal"]["sequence"]
        res_norm = predict_disease_risk(seq_norm)
        self.assertIn(res_norm["predicted_category"], ["Healthy", "Sickle Cell Disease", "Cancer", "Cystic Fibrosis", "Huntington's Disease"])

        # 4. Check model metadata
        self.assertIn("RandomForestClassifier", res_sickle["algorithm"])
        self.assertIn("disclaimer_notice", res_sickle)
        self.assertIn("academic and research", res_sickle["disclaimer_notice"].lower())


if __name__ == '__main__':
    unittest.main()
