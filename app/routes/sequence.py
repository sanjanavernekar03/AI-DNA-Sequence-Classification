from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from app.routes.auth import login_required
from app.services.dna_service import (
    sanitize_dna, validate_dna, parse_fasta, calculate_sequence_metrics, SAMPLE_SEQUENCES
)
from app.database.queries import (
    create_dna_sequence, save_sequence_analysis, get_sequence_analysis_by_id
)

sequence_bp = Blueprint('sequence', __name__, url_prefix='/analysis/sequence')


@sequence_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user_id = session['user_id']
    result = None
    input_sequence = ""
    sequence_name = "DNA Sequence"

    if request.method == 'POST':
        source_type = 'manual'
        file = request.files.get('dna_file')

        if file and file.filename:
            source_type = 'fasta_upload'
            content = file.read().decode('utf-8', errors='ignore')
            header, parsed_seq, error = parse_fasta(content)
            if error:
                flash(f"File error: {error}", "danger")
                return render_template('analysis/sequence.html', samples=SAMPLE_SEQUENCES, input_sequence=input_sequence)
            sequence_name = header if header else file.filename
            input_sequence = parsed_seq
        else:
            raw_seq = request.form.get('sequence', '')
            seq_name_input = request.form.get('sequence_name', '').strip()
            if seq_name_input:
                sequence_name = seq_name_input
            input_sequence = sanitize_dna(raw_seq)

        # Validate
        is_valid, error = validate_dna(input_sequence)
        if not is_valid:
            flash(error, "danger")
            return render_template('analysis/sequence.html', samples=SAMPLE_SEQUENCES, input_sequence=input_sequence, sequence_name=sequence_name)

        # Compute Metrics
        metrics = calculate_sequence_metrics(input_sequence)

        # Save to MySQL
        seq_id = create_dna_sequence(
            user_id=user_id,
            sequence_name=sequence_name,
            sequence=input_sequence,
            sequence_length=metrics["length"],
            source_type=source_type
        )

        analysis_id = save_sequence_analysis(
            user_id=user_id,
            sequence_id=seq_id,
            sequence_name=sequence_name,
            length=metrics["length"],
            a_count=metrics["a_count"],
            t_count=metrics["t_count"],
            g_count=metrics["g_count"],
            c_count=metrics["c_count"],
            a_percentage=metrics["a_percentage"],
            t_percentage=metrics["t_percentage"],
            g_percentage=metrics["g_percentage"],
            c_percentage=metrics["c_percentage"],
            gc_content=metrics["gc_content"],
            at_content=metrics["at_content"],
            purine_count=metrics["purine_count"],
            pyrimidine_count=metrics["pyrimidine_count"],
            molecular_weight=metrics["molecular_weight"]
        )

        result = metrics
        result["id"] = analysis_id
        result["sequence_id"] = seq_id
        result["sequence_name"] = sequence_name
        flash("DNA Sequence successfully processed and analyzed!", "success")

    return render_template(
        'analysis/sequence.html',
        samples=SAMPLE_SEQUENCES,
        result=result,
        input_sequence=input_sequence,
        sequence_name=sequence_name
    )


@sequence_bp.route('/view/<int:analysis_id>')
@login_required
def view(analysis_id: int):
    user_id = session['user_id']
    analysis = get_sequence_analysis_by_id(analysis_id, user_id)
    if not analysis:
        flash("Sequence analysis record not found.", "warning")
        return redirect(url_for('sequence.index'))

    return render_template(
        'analysis/sequence.html',
        samples=SAMPLE_SEQUENCES,
        result=analysis,
        input_sequence=analysis.get('sequence', ''),
        sequence_name=analysis.get('sequence_name', 'DNA Sequence')
    )
