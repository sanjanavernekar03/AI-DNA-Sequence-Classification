from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.routes.auth import login_required
from app.services.dna_service import sanitize_dna, validate_dna, parse_fasta, SAMPLE_SEQUENCES
from app.services.disease_service import process_disease_prediction
from app.database.queries import create_dna_sequence, get_disease_prediction_by_id

from app.ml.predict_disease import get_disease_model

disease_bp = Blueprint('disease', __name__, url_prefix='/analysis/disease')


@disease_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user_id = session['user_id']
    result = None
    input_sequence = ""
    sequence_name = "DNA Sequence"

    if request.method == 'POST':
        file = request.files.get('dna_file')
        source_type = 'manual'

        if file and file.filename:
            source_type = 'fasta_upload'
            content = file.read().decode('utf-8', errors='ignore')
            header, parsed_seq, error = parse_fasta(content)
            if error:
                flash(f"File error: {error}", "danger")
                return render_template('analysis/disease.html', samples=SAMPLE_SEQUENCES, input_sequence=input_sequence)
            sequence_name = header if header else file.filename
            input_sequence = parsed_seq
        else:
            raw_seq = request.form.get('sequence', '')
            seq_name_input = request.form.get('sequence_name', '').strip()
            if seq_name_input:
                sequence_name = seq_name_input
            input_sequence = sanitize_dna(raw_seq)

        is_valid, error = validate_dna(input_sequence)
        if not is_valid:
            flash(error, "danger")
            return render_template('analysis/disease.html', samples=SAMPLE_SEQUENCES, input_sequence=input_sequence, sequence_name=sequence_name)

        seq_id = create_dna_sequence(user_id, sequence_name, input_sequence, len(input_sequence), source_type=source_type)

        result = process_disease_prediction(
            user_id=user_id,
            sequence=input_sequence,
            sequence_name=sequence_name,
            sequence_id=seq_id
        )
        result["sequence_id"] = seq_id
        flash(f"Genomic Disease Risk assessment completed! Category: {result['predicted_category']} [{result['risk_category']} Risk]", "info")

    return render_template(
        'analysis/disease.html',
        samples=SAMPLE_SEQUENCES,
        result=result,
        input_sequence=input_sequence,
        sequence_name=sequence_name
    )


@disease_bp.route('/view/<int:analysis_id>')
@login_required
def view(analysis_id: int):
    user_id = session['user_id']
    analysis = get_disease_prediction_by_id(analysis_id, user_id)
    if not analysis:
        flash("Disease prediction record not found.", "warning")
        return redirect(url_for('disease.index'))

    try:
        _, metadata = get_disease_model()
        analysis["metrics"] = metadata.get("metrics", {})
        analysis["confusion_matrix"] = metadata.get("confusion_matrix", {})
        analysis["classification_report"] = metadata.get("classification_report", {})
    except Exception:
        pass

    return render_template(
        'analysis/disease.html',
        samples=SAMPLE_SEQUENCES,
        result=analysis,
        sequence_name=analysis.get('sequence_name', 'DNA Sequence')
    )
