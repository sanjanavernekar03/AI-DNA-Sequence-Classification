import unittest
from app.services.mutation_service import detect_mutations


class TestMutation(unittest.TestCase):

    def test_detect_substitution_mutation(self):
        ref = "ATGCGTAC"
        smp = "ATGAGTAC"  # C -> A substitution at pos 4
        res = detect_mutations(ref, smp)
        self.assertGreaterEqual(res["total_mutations"], 1)
        self.assertGreaterEqual(res["substitutions_count"], 1)
        subs = [m for m in res["mutations_list"] if m["type"] == "Substitution"]
        self.assertGreater(len(subs), 0)
        self.assertEqual(subs[0]["ref_base"], "C")
        self.assertEqual(subs[0]["obs_base"], "A")

    def test_detect_deletion_mutation(self):
        ref = "ATGCGTAC"
        smp = "ATGTAC"  # CG deleted
        res = detect_mutations(ref, smp)
        self.assertGreaterEqual(res["deletions_count"], 1)

    def test_detect_insertion_mutation(self):
        ref = "ATGCGTAC"
        smp = "ATGCCCGTAC"  # CC inserted
        res = detect_mutations(ref, smp)
        self.assertGreaterEqual(res["insertions_count"], 1)


if __name__ == '__main__':
    unittest.main()
