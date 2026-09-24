import unittest
from app.services.dna_service import calculate_sequence_metrics


class TestSequenceAnalysis(unittest.TestCase):

    def test_calculate_sequence_metrics(self):
        # 10 bp sequence: 3 A, 2 T, 3 G, 2 C => GC = 5/10 = 50%, AT = 5/10 = 50%
        seq = "AAATTGGGCC"
        metrics = calculate_sequence_metrics(seq)

        self.assertEqual(metrics["length"], 10)
        self.assertEqual(metrics["a_count"], 3)
        self.assertEqual(metrics["t_count"], 2)
        self.assertEqual(metrics["g_count"], 3)
        self.assertEqual(metrics["c_count"], 2)
        self.assertEqual(metrics["gc_content"], 50.0)
        self.assertEqual(metrics["at_content"], 50.0)
        self.assertEqual(metrics["purine_count"], 6)
        self.assertEqual(metrics["pyrimidine_count"], 4)
        self.assertGreater(metrics["molecular_weight"], 0)

    def test_calculate_metrics_all_gc(self):
        seq = "GGGGCCCC"
        metrics = calculate_sequence_metrics(seq)
        self.assertEqual(metrics["length"], 8)
        self.assertEqual(metrics["gc_content"], 100.0)
        self.assertEqual(metrics["at_content"], 0.0)


if __name__ == '__main__':
    unittest.main()
