from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.routes.auth import login_required
from app.services.dna_service import sanitize_dna, validate_dna, SAMPLE_SEQUENCES
from app.services.mutation_service import detect_mutations
from app.database.queries import (
    create_dna_sequence, save_mutation_analysis, save_mutations_batch,
    get_mutation_analysis_by_id, get_mutations_by_analysis_id
)

mutation_bp = Blueprint('mutation', __name__, url_prefix='/analysis/mutation')


@mutation_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user_id = session['user_id']
    result = None
    ref_seq = ""
    sample_seq = ""
    ref_name = "Wildtype Reference"
    sample_name = "Mutant / Sample"

    if request.method == 'POST':
        ref_seq_raw = request.form.get('reference_sequence', '')
        sample_seq_raw = request.form.get('sample_sequence', '')
        ref_name_input = request.form.get('reference_name', '').strip()
        sample_name_input = request.form.get('sample_name', '').strip()

        if ref_name_input:
            ref_name = ref_name_input
        if sample_name_input:
            sample_name = sample_name_input

        ref_seq = sanitize_dna(ref_seq_raw)
        sample_seq = sanitize_dna(sample_seq_raw)

        v_ref, err_ref = validate_dna(ref_seq)
        if not v_ref:
            flash(f"Reference Sequence Error: {err_ref}", "danger")
            return render_template('analysis/mutation.html', samples=SAMPLE_SEQUENCES, ref_seq=ref_seq, sample_seq=sample_seq, ref_name=ref_name, sample_name=sample_name)

        v_smp, err_smp = validate_dna(sample_seq)
        if not v_smp:
            flash(f"Sample Sequence Error: {err_smp}", "danger")
            return render_template('analysis/mutation.html', samples=SAMPLE_SEQUENCES, ref_seq=ref_seq, sample_seq=sample_seq, ref_name=ref_name, sample_name=sample_name)

        # Detect mutations
        mut_data = detect_mutations(ref_seq, sample_seq)

        ref_id = create_dna_sequence(user_id, ref_name, ref_seq, len(ref_seq), source_type='reference')
        smp_id = create_dna_sequence(user_id, sample_name, sample_seq, len(sample_seq), source_type='sample')

        analysis_id = save_mutation_analysis(
            user_id=user_id,
            ref_id=ref_id,
            sample_id=smp_id,
            ref_name=ref_name,
            sample_name=sample_name,
            total_mut=mut_data["total_mutations"],
            subs=mut_data["substitutions_count"],
            ins=mut_data["insertions_count"],
            dels=mut_data["deletions_count"],
            mutation_rate=mut_data["mutation_rate"]
        )

        save_mutations_batch(user_id, analysis_id, mut_data["mutations_list"])

        result = mut_data
        result["id"] = analysis_id
        result["reference_name"] = ref_name
        result["sample_name"] = sample_name
        flash(f"Mutation detection complete! Identified {mut_data['total_mutations']} variations across coordinates.", "success")

    return render_template(
        'analysis/mutation.html',
        samples=SAMPLE_SEQUENCES,
        result=result,
        ref_seq=ref_seq,
        sample_seq=sample_seq,
        ref_name=ref_name,
        sample_name=sample_name
    )


@mutation_bp.route('/view/<int:analysis_id>')
@login_required
def view(analysis_id: int):
    user_id = session['user_id']
    analysis = get_mutation_analysis_by_id(analysis_id, user_id)
    if not analysis:
        flash("Mutation analysis record not found.", "warning")
        return redirect(url_for('mutation.index'))

    mutations = get_mutations_by_analysis_id(analysis_id, user_id)
    analysis["mutations_list"] = mutations

    # Compute density bins for display
    ref_len = 200
    num_bins = 10
    bin_size = max(1, ref_len // num_bins)
    mutation_bins = [0] * num_bins
    bin_labels = [f"{b * bin_size + 1}-{(b + 1) * bin_size} bp" for b in range(num_bins)]
    for m in mutations:
        pos = m["position"]
        bin_idx = min(num_bins - 1, (pos - 1) // bin_size)
        if 0 <= bin_idx < num_bins:
            mutation_bins[bin_idx] += 1
    analysis["density_labels"] = bin_labels
    analysis["density_counts"] = mutation_bins

    return render_template(
        'analysis/mutation.html',
        samples=SAMPLE_SEQUENCES,
        result=analysis,
        ref_name=analysis.get('reference_name', 'Reference'),
        sample_name=analysis.get('sample_name', 'Sample')
    )
