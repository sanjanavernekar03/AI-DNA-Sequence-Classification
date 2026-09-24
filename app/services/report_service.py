import os
import uuid
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from app.config import Config
from app.reports.pdf_generator import (
    generate_sequence_pdf,
    generate_similarity_pdf,
    generate_mutation_pdf,
    generate_classification_pdf,
    generate_disease_pdf,
    generate_visualization_pdf,
    generate_complete_analysis_pdf
)
from app.database.queries import create_report_record, get_report_by_uuid, get_report_by_id


def generate_and_store_report(user_id: int, user_name: str, analysis_id: Optional[int],
                              analysis_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the appropriate PDF report, save it to generated_reports/, and record in MySQL.
    """
    report_uuid = str(uuid.uuid4()).replace("-", "")[:16]
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"Genomix_Report_{analysis_type}_{timestamp_str}_{report_uuid}.pdf"
    file_path = Config.GENERATED_REPORTS_FOLDER / file_name

    title_map = {
        "sequence": "DNA Sequence Processing & Analysis Report",
        "similarity": "DNA Sequence Similarity & Alignment Report",
        "mutation": "DNA Mutation Detection & Analysis Report",
        "classification": "AI-Based DNA Classification Report",
        "disease": "Genomic Disease Risk Prediction Report",
        "visualization": "DNA Sequence Visualization Report",
        "complete": "Comprehensive Complete DNA Analysis Report"
    }
    title = title_map.get(analysis_type, "DNA Analysis Report")

    # Generate PDF
    if analysis_type == "sequence":
        generate_sequence_pdf(data, user_name, file_path)
    elif analysis_type == "similarity":
        generate_similarity_pdf(data, user_name, file_path)
    elif analysis_type == "mutation":
        mut_list = data.get("mutations_list", [])
        generate_mutation_pdf(data, mut_list, user_name, file_path)
    elif analysis_type == "classification":
        generate_classification_pdf(data, user_name, file_path)
    elif analysis_type == "disease":
        generate_disease_pdf(data, user_name, file_path)
    elif analysis_type == "visualization":
        generate_visualization_pdf(data, user_name, file_path)
    elif analysis_type == "complete":
        generate_complete_analysis_pdf(data, user_name, file_path)
    else:
        generate_sequence_pdf(data, user_name, file_path)

    file_size = os.path.getsize(file_path) if file_path.exists() else 0

    # Save to database
    db_id = create_report_record(
        user_id=user_id,
        report_uuid=report_uuid,
        analysis_id=analysis_id,
        analysis_type=analysis_type,
        title=title,
        file_name=file_name,
        file_path=str(file_path),
        file_size_bytes=file_size
    )

    return {
        "id": db_id,
        "report_uuid": report_uuid,
        "title": title,
        "file_name": file_name,
        "file_path": str(file_path),
        "file_size_bytes": file_size,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
