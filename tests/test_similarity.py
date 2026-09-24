import unittest
from app.services.similarity_service import perform_pairwise_alignment


class TestSimilarity(unittest.TestCase):

    def test_identical_sequence_similarity(self):
        seq = "ATGCGATCGATC"
        res = perform_pairwise_alignment(seq, seq)
        self.assertEqual(res["similarity_percentage"], 100.0)
        self.assertEqual(res["difference_percentage"], 0.0)
        self.assertEqual(res["match_count"], len(seq))
        self.assertEqual(res["mismatch_count"], 0)
        self.assertEqual(res["gap_count"], 0)

    def test_mismatched_sequence_similarity(self):
        ref = "ATGCGTAC"
        qry = "ATGAGTAC"  # 1 mismatch at pos 4
        res = perform_pairwise_alignment(ref, qry)
        self.assertLess(res["similarity_percentage"], 100.0)
        self.assertEqual(res["match_count"], 7)
        self.assertEqual(res["mismatch_count"], 1)


if __name__ == '__main__':
    unittest.main()
