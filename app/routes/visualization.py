from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.routes.auth import login_required
from app.services.dna_service import sanitize_dna, validate_dna, parse_fasta, SAMPLE_SEQUENCES
from app.services.mutation_service import detect_mutations
from app.services.visualization_service import generate_visualization_payload
from app.database.queries import create_dna_sequence, save_visualization, get_visualization_by_id

visualization_bp = Blueprint('visualization', __name__, url_prefix='/analysis/visualization')


@visualization_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user_id = session['user_id']
    result = None
    input_sequence = ""
    ref_sequence = ""
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
                return render_template('analysis/visualization.html', samples=SAMPLE_SEQUENCES, input_sequence=input_sequence)
            sequence_name = header if header else file.filename
            input_sequence = parsed_seq
        else:
            raw_seq = request.form.get('sequence', '')
            seq_name_input = request.form.get('sequence_name', '').strip()
            if seq_name_input:
                sequence_name = seq_name_input
            input_sequence = sanitize_dna(raw_seq)

        ref_raw = request.form.get('ref_sequence', '')
        if ref_raw:
            ref_sequence = sanitize_dna(ref_raw)

        is_valid, error = validate_dna(input_sequence)
        if not is_valid:
            flash(error, "danger")
            return render_template('analysis/visualization.html', samples=SAMPLE_SEQUENCES, input_sequence=input_sequence, sequence_name=sequence_name)

        # Optional mutation detection if reference provided
        mutation_data = None
        if ref_sequence:
            v_ref, _ = validate_dna(ref_sequence)
            if v_ref:
                mutation_data = detect_mutations(ref_sequence, input_sequence)

        payload = generate_visualization_payload(input_sequence, mutation_data)

        seq_id = create_dna_sequence(user_id, sequence_name, input_sequence, len(input_sequence), source_type=source_type)

        vis_id = save_visualization(
            user_id=user_id,
            sequence_id=seq_id,
            sequence_name=sequence_name,
            visualization_type="multi_chart_analytics",
            chart_config=payload
        )

        result = payload
        result["id"] = vis_id
        result["sequence_name"] = sequence_name
        flash("Interactive DNA sequence visualizations generated successfully!", "success")

    return render_template(
        'analysis/visualization.html',
        samples=SAMPLE_SEQUENCES,
        result=result,
        input_sequence=input_sequence,
        ref_sequence=ref_sequence,
        sequence_name=sequence_name
    )


@visualization_bp.route('/view/<int:vis_id>')
@login_required
def view(vis_id: int):
    user_id = session['user_id']
    analysis = get_visualization_by_id(vis_id, user_id)
    if not analysis:
        flash("Visualization record not found.", "warning")
        return redirect(url_for('visualization.index'))

    result = analysis.get("chart_config", {})
    result["id"] = analysis.get("id")
    result["sequence_name"] = analysis.get("sequence_name")

    return render_template(
        'analysis/visualization.html',
        samples=SAMPLE_SEQUENCES,
        result=result,
        sequence_name=analysis.get('sequence_name', 'DNA Sequence')
    )
