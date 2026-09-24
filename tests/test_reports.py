import os
import unittest
import tempfile
from pathlib import Path

from app.reports.pdf_generator import (
    generate_sequence_pdf,
    generate_similarity_pdf,
    generate_mutation_pdf,
    generate_classification_pdf,
    generate_disease_pdf,
    generate_visualization_pdf,
    generate_complete_analysis_pdf
)


class TestReports(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)
        self.sample_seq = "ATGC" * 30  # 120 bp

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_sequence_pdf(self):
        output_path = self.tmp_path / "test_sequence_report.pdf"
        data = {
            "id": 1,
            "sequence_name": "Test Specimen",
            "length": len(self.sample_seq),
            "a_count": 30, "t_count": 30, "g_count": 30, "c_count": 30,
            "a_percentage": 25.0, "t_percentage": 25.0, "g_percentage": 25.0, "c_percentage": 25.0,
            "gc_content": 50.0, "at_content": 50.0,
            "purine_count": 60, "pyrimidine_count": 60, "molecular_weight": 35000.0,
            "cleaned_sequence": self.sample_seq
        }
        generate_sequence_pdf(data, "Dr. Lead Investigator", output_path)
        self.assertTrue(output_path.exists())
        self.assertGreater(os.path.getsize(output_path), 2000)

    def test_generate_similarity_pdf(self):
        output_path = self.tmp_path / "test_similarity_report.pdf"
        data = {
            "id": 2,
            "reference_name": "Wildtype TP53",
            "query_name": "Variant Specimen",
            "reference_length": len(self.sample_seq),
            "query_length": len(self.sample_seq),
            "similarity_percentage": 95.0,
            "difference_percentage": 5.0,
            "match_count": 114,
            "mismatch_count": 6,
            "gap_count": 0,
            "alignment_score": 110.0,
            "reference_sequence": self.sample_seq,
            "query_sequence": self.sample_seq[:10] + "TTTT" + self.sample_seq[14:]
        }
        generate_similarity_pdf(data, "Dr. Lead Investigator", output_path)
        self.assertTrue(output_path.exists())
        self.assertGreater(os.path.getsize(output_path), 2000)

    def test_generate_mutation_pdf(self):
        output_path = self.tmp_path / "test_mutation_report.pdf"
        data = {
            "id": 3,
            "sample_name": "Clinical Exon Variant",
            "total_mutations": 2,
            "substitutions_count": 2,
            "insertions_count": 0,
            "deletions_count": 0,
            "mutation_rate": 1.67,
            "sample_sequence": self.sample_seq
        }
        mut_list = [
            {"position": 12, "type": "Substitution", "ref_base": "C", "obs_base": "T", "consequence_note": "Transition (C->T)"},
            {"position": 45, "type": "Substitution", "ref_base": "A", "obs_base": "G", "consequence_note": "Transition (A->G)"}
        ]
        generate_mutation_pdf(data, mut_list, "Dr. Lead Investigator", output_path)
        self.assertTrue(output_path.exists())
        self.assertGreater(os.path.getsize(output_path), 2000)

    def test_generate_classification_pdf(self):
        output_path = self.tmp_path / "test_classification_report.pdf"
        data = {
            "id": 4,
            "sequence_name": "Promoter Candidate",
            "predicted_class": "Promoter Region",
            "confidence": 92.5,
            "model_name": "RandomForestClassifier (64-mer TF)",
            "sequence": self.sample_seq
        }
        generate_classification_pdf(data, "Dr. Lead Investigator", output_path)
        self.assertTrue(output_path.exists())
        self.assertGreater(os.path.getsize(output_path), 2000)

    def test_generate_disease_pdf(self):
        output_path = self.tmp_path / "test_disease_report.pdf"
        data = {
            "id": 5,
            "sequence_name": "HBB Codon 6 Variant",
            "predicted_category": "Sickle Cell Disease",
            "probability": 88.4,
            "risk_category": "High",
            "probabilities": {
                "Healthy": 3.2,
                "Cancer": 4.1,
                "Sickle Cell Disease": 88.4,
                "Cystic Fibrosis": 2.5,
                "Huntington's Disease": 1.8
            },
            "sequence": self.sample_seq
        }
        generate_disease_pdf(data, "Dr. Lead Investigator", output_path)
        self.assertTrue(output_path.exists())
        self.assertGreater(os.path.getsize(output_path), 2000)

    def test_generate_visualization_pdf(self):
        output_path = self.tmp_path / "test_visualization_report.pdf"
        data = {
            "id": 6,
            "sequence_name": "Target Visualization Exon",
            "length": 120,
            "a_count": 30, "t_count": 30, "g_count": 30, "c_count": 30,
            "a_percentage": 25.0, "t_percentage": 25.0, "g_percentage": 25.0, "c_percentage": 25.0,
            "gc_content": 50.0, "at_content": 50.0,
            "purine_count": 60, "pyrimidine_count": 60, "molecular_weight": 35000.0,
            "sequence": self.sample_seq
        }
        generate_visualization_pdf(data, "Dr. Lead Investigator", output_path)
        self.assertTrue(output_path.exists())
        self.assertGreater(os.path.getsize(output_path), 2000)

    def test_generate_complete_pdf(self):
        output_path = self.tmp_path / "test_complete_report.pdf"
        data = {
            "id": 101,
            "sequence_name": "Comprehensive Clinical Specimen",
            "length": 150,
            "a_count": 40, "t_count": 40, "g_count": 35, "c_count": 35,
            "a_percentage": 26.6, "t_percentage": 26.6, "g_percentage": 23.3, "c_percentage": 23.3,
            "gc_content": 46.6, "at_content": 53.4, "molecular_weight": 42000.0,
            "reference_name": "Wildtype TP53",
            "query_name": "Patient Query",
            "similarity_percentage": 97.5,
            "difference_percentage": 2.5,
            "match_count": 146,
            "mismatch_count": 4,
            "gap_count": 0,
            "total_mutations": 4,
            "substitutions_count": 4,
            "insertions_count": 0,
            "deletions_count": 0,
            "mutation_rate": 2.67,
            "predicted_class": "Coding Sequence (CDS)",
            "class_confidence": 91.2,
            "predicted_category": "Healthy",
            "disease_probability": 88.5,
            "risk_category": "Low",
            "sequence": self.sample_seq,
            "reference_sequence": self.sample_seq
        }
        generate_complete_analysis_pdf(data, "Dr. Lead Investigator", output_path)
        self.assertTrue(output_path.exists())
        self.assertGreater(os.path.getsize(output_path), 3000)


if __name__ == '__main__':
    unittest.main()
