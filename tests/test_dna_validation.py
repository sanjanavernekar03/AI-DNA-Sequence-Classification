import unittest
from app.services.dna_service import sanitize_dna, validate_dna, parse_fasta


class TestDNAValidation(unittest.TestCase):

    def test_sanitize_dna(self):
        raw = "  atg cgt \n\t aac \r\n "
        self.assertEqual(sanitize_dna(raw), "ATGCGTAAC")

    def test_validate_dna_valid(self):
        valid_seq = "ATGCGATCGATCGATC"
        is_valid, error = validate_dna(valid_seq)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_dna_lowercase(self):
        is_valid, error = validate_dna("atgcgtac")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_dna_empty(self):
        is_valid, error = validate_dna("")
        self.assertFalse(is_valid)
        self.assertIn("cannot be empty", error)

    def test_validate_dna_invalid_characters(self):
        is_valid, error = validate_dna("ATGCZ123!X")
        self.assertFalse(is_valid)
        self.assertTrue("Invalid character" in error or "Only A, T, G, and C" in error)

    def test_parse_fasta_standard(self):
        fasta_text = ">Test_Gene_01 Sample Homo sapiens\nATGCGATCGATC\nGATCGATCGATC"
        header, seq, error = parse_fasta(fasta_text)
        self.assertIsNone(error)
        self.assertIn("Test_Gene_01", header)
        self.assertEqual(seq, "ATGCGATCGATCGATCGATCGATC")

    def test_parse_fasta_invalid_content(self):
        fasta_text = ">Invalid_Seq\nATGCXYZ123"
        header, seq, error = parse_fasta(fasta_text)
        self.assertIsNotNone(error)
        self.assertEqual(seq, "")


if __name__ == '__main__':
    unittest.main()
