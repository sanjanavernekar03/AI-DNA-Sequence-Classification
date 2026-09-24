from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.routes.auth import login_required
from app.services.dna_service import sanitize_dna, validate_dna, SAMPLE_SEQUENCES
from app.services.similarity_service import perform_pairwise_alignment
from app.database.queries import (
    create_dna_sequence, save_similarity_analysis, get_similarity_analysis_by_id
)

similarity_bp = Blueprint('similarity', __name__, url_prefix='/analysis/similarity')


@similarity_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user_id = session['user_id']
    result = None
    ref_seq = ""
    query_seq = ""
    ref_name = "Reference Sequence"
    query_name = "Query Sequence"

    if request.method == 'POST':
        ref_seq_raw = request.form.get('reference_sequence', '')
        query_seq_raw = request.form.get('query_sequence', '')
        ref_name_input = request.form.get('reference_name', '').strip()
        query_name_input = request.form.get('query_name', '').strip()

        if ref_name_input:
            ref_name = ref_name_input
        if query_name_input:
            query_name = query_name_input

        ref_seq = sanitize_dna(ref_seq_raw)
        query_seq = sanitize_dna(query_seq_raw)

        # Validate both
        v_ref, err_ref = validate_dna(ref_seq)
        if not v_ref:
            flash(f"Reference Sequence Error: {err_ref}", "danger")
            return render_template('analysis/similarity.html', samples=SAMPLE_SEQUENCES, ref_seq=ref_seq, query_seq=query_seq, ref_name=ref_name, query_name=query_name)

        v_qry, err_qry = validate_dna(query_seq)
        if not v_qry:
            flash(f"Query Sequence Error: {err_qry}", "danger")
            return render_template('analysis/similarity.html', samples=SAMPLE_SEQUENCES, ref_seq=ref_seq, query_seq=query_seq, ref_name=ref_name, query_name=query_name)

        # Align & Compare
        alignment_data = perform_pairwise_alignment(ref_seq, query_seq)

        # Save Sequences
        ref_id = create_dna_sequence(user_id, ref_name, ref_seq, len(ref_seq), source_type='reference')
        qry_id = create_dna_sequence(user_id, query_name, query_seq, len(query_seq), source_type='query')

        # Save Analysis
        analysis_id = save_similarity_analysis(
            user_id=user_id,
            ref_id=ref_id,
            query_id=qry_id,
            ref_name=ref_name,
            query_name=query_name,
            ref_len=alignment_data["reference_length"],
            query_len=alignment_data["query_length"],
            sim_pct=alignment_data["similarity_percentage"],
            diff_pct=alignment_data["difference_percentage"],
            matches=alignment_data["match_count"],
            mismatches=alignment_data["mismatch_count"],
            gaps=alignment_data["gap_count"],
            score=alignment_data["alignment_score"],
            align_ref=alignment_data["alignment_ref"],
            align_query=alignment_data["alignment_query"],
            align_match=alignment_data["alignment_match"]
        )

        result = alignment_data
        result["id"] = analysis_id
        result["reference_name"] = ref_name
        result["query_name"] = query_name
        flash("Pairwise sequence alignment and similarity analysis completed!", "success")

    return render_template(
        'analysis/similarity.html',
        samples=SAMPLE_SEQUENCES,
        result=result,
        ref_seq=ref_seq,
        query_seq=query_seq,
        ref_name=ref_name,
        query_name=query_name
    )


@similarity_bp.route('/view/<int:analysis_id>')
@login_required
def view(analysis_id: int):
    user_id = session['user_id']
    analysis = get_similarity_analysis_by_id(analysis_id, user_id)
    if not analysis:
        flash("Similarity analysis record not found.", "warning")
        return redirect(url_for('similarity.index'))

    # Reconstruct visual blocks
    from app.services.similarity_service import perform_pairwise_alignment
    recomputed = perform_pairwise_alignment(
        analysis.get('alignment_ref', '').replace('-', ''),
        analysis.get('alignment_query', '').replace('-', '')
    )
    analysis['visual_blocks'] = recomputed['visual_blocks']

    return render_template(
        'analysis/similarity.html',
        samples=SAMPLE_SEQUENCES,
        result=analysis,
        ref_seq=analysis.get('alignment_ref', '').replace('-', ''),
        query_seq=analysis.get('alignment_query', '').replace('-', ''),
        ref_name=analysis.get('reference_name', 'Reference Sequence'),
        query_name=analysis.get('query_name', 'Query Sequence')
    )
