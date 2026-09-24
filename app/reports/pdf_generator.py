from pathlib import Path
from typing import Dict, Any, List, Optional

from app.reports.dna_report import generate_dna_sequence_report
from app.reports.similarity_report import generate_dna_similarity_report
from app.reports.mutation_report import generate_dna_mutation_report
from app.reports.classification_report import generate_dna_classification_report
from app.reports.disease_report import generate_dna_disease_report
from app.reports.visualization_report import generate_dna_visualization_report
from app.reports.complete_report import generate_complete_dna_report


def generate_sequence_pdf(analysis_data: Dict[str, Any], user_name: str, output_path: Path):
    return generate_dna_sequence_report(analysis_data, user_name, output_path)


def generate_similarity_pdf(sim_data: Dict[str, Any], user_name: str, output_path: Path):
    return generate_dna_similarity_report(sim_data, user_name, output_path)


def generate_mutation_pdf(mut_data: Dict[str, Any], mutations_list: List[Dict[str, Any]], user_name: str, output_path: Path):
    return generate_dna_mutation_report(mut_data, mutations_list, user_name, output_path)


def generate_classification_pdf(clf_data: Dict[str, Any], user_name: str, output_path: Path):
    return generate_dna_classification_report(clf_data, user_name, output_path)


def generate_disease_pdf(dis_data: Dict[str, Any], user_name: str, output_path: Path):
    return generate_dna_disease_report(dis_data, user_name, output_path)


def generate_visualization_pdf(vis_data: Dict[str, Any], user_name: str, output_path: Path):
    return generate_dna_visualization_report(vis_data, user_name, output_path)


def generate_complete_analysis_pdf(comp_data: Dict[str, Any], user_name: str, output_path: Path):
    return generate_complete_dna_report(comp_data, user_name, output_path)
