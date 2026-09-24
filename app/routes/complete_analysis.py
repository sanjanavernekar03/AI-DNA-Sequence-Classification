from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from app.routes.auth import login_required
from app.services.dna_service import (
    sanitize_dna, validate_dna, parse_fasta, calculate_sequence_metrics, SAMPLE_SEQUENCES
)
from app.services.similarity_service import perform_pairwise_alignment
from app.services.mutation_service import detect_mutations
from app.services.classification_service import process_dna_classification
from app.services.disease_service import process_disease_prediction
from app.services.visualization_service import generate_visualization_payload
from app.database.queries import (
    create_dna_sequence, save_sequence_analysis, save_similarity_analysis,
    save_mutation_analysis, save_mutations_batch, create_complete_analysis,
    get_complete_analysis_by_id
)

complete_bp = Blueprint('complete_analysis', __name__, url_prefix='/analysis/complete')


@complete_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user_id = session['user_id']
    target_seq = ""
    ref_seq = ""
    target_name = "Target Sample Sequence"
    ref_name = "Wildtype Reference Sequence"

    if request.method == 'POST':
        file = request.files.get('dna_file')
        source_type = 'manual'

        if file and file.filename:
            source_type = 'fasta_upload'
            content = file.read().decode('utf-8', errors='ignore')
            header, parsed_seq, error = parse_fasta(content)
            if error:
                flash(f"File error: {error}", "danger")
                return render_template('analysis/complete.html', samples=SAMPLE_SEQUENCES)
            target_name = header if header else file.filename
            target_seq = parsed_seq
        else:
            raw_seq = request.form.get('sequence', '')
            t_name = request.form.get('sequence_name', '').strip()
            if t_name:
                target_name = t_name
            target_seq = sanitize_dna(raw_seq)

        ref_raw = request.form.get('reference_sequence', '')
        r_name = request.form.get('reference_name', '').strip()
        if r_name:
            ref_name = r_name

        # If reference sequence is empty, default to standard human TP53 or reference benchmark
        if ref_raw.strip():
            ref_seq = sanitize_dna(ref_raw)
        else:
            ref_seq = SAMPLE_SEQUENCES["human_tp53"]["sequence"]
            ref_name = "Standard Benchmark Reference (TP53)"

        # Validate
        v_tgt, err_tgt = validate_dna(target_seq)
        if not v_tgt:
            flash(f"Target Sequence Error: {err_tgt}", "danger")
            return render_template('analysis/complete.html', samples=SAMPLE_SEQUENCES, target_seq=target_seq, ref_seq=ref_seq, target_name=target_name, ref_name=ref_name)

        v_ref, err_ref = validate_dna(ref_seq)
        if not v_ref:
            flash(f"Reference Sequence Error: {err_ref}", "danger")
            return render_template('analysis/complete.html', samples=SAMPLE_SEQUENCES, target_seq=target_seq, ref_seq=ref_seq, target_name=target_name, ref_name=ref_name)

        # -------------------------------------------------------------
        # 1. Sequence Processing & Metrics (Module 1)
        # -------------------------------------------------------------
        seq_metrics = calculate_sequence_metrics(target_seq)
        target_seq_id = create_dna_sequence(user_id, target_name, target_seq, seq_metrics["length"], source_type=source_type)
        ref_seq_id = create_dna_sequence(user_id, ref_name, ref_seq, len(ref_seq), source_type='reference')

        sa_id = save_sequence_analysis(
            user_id=user_id,
            sequence_id=target_seq_id,
            sequence_name=target_name,
            length=seq_metrics["length"],
            a_count=seq_metrics["a_count"],
            t_count=seq_metrics["t_count"],
            g_count=seq_metrics["g_count"],
            c_count=seq_metrics["c_count"],
            a_percentage=seq_metrics["a_percentage"],
            t_percentage=seq_metrics["t_percentage"],
            g_percentage=seq_metrics["g_percentage"],
            c_percentage=seq_metrics["c_percentage"],
            gc_content=seq_metrics["gc_content"],
            at_content=seq_metrics["at_content"],
            purine_count=seq_metrics["purine_count"],
            pyrimidine_count=seq_metrics["pyrimidine_count"],
            molecular_weight=seq_metrics["molecular_weight"]
        )

        # -------------------------------------------------------------
        # 2. Similarity Analysis (Module 2)
        # -------------------------------------------------------------
        alignment_data = perform_pairwise_alignment(ref_seq, target_seq)
        sim_id = save_similarity_analysis(
            user_id=user_id,
            ref_id=ref_seq_id,
            query_id=target_seq_id,
            ref_name=ref_name,
            query_name=target_name,
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

        # -------------------------------------------------------------
        # 3. Mutation Detection (Module 3)
        # -------------------------------------------------------------
        mut_data = detect_mutations(ref_seq, target_seq)
        mut_id = save_mutation_analysis(
            user_id=user_id,
            ref_id=ref_seq_id,
            sample_id=target_seq_id,
            ref_name=ref_name,
            sample_name=target_name,
            total_mut=mut_data["total_mutations"],
            subs=mut_data["substitutions_count"],
            ins=mut_data["insertions_count"],
            dels=mut_data["deletions_count"],
            mutation_rate=mut_data["mutation_rate"]
        )
        save_mutations_batch(user_id, mut_id, mut_data["mutations_list"])

        # -------------------------------------------------------------
        # 4. AI DNA Classification (Module 4)
        # -------------------------------------------------------------
        clf_result = process_dna_classification(
            user_id=user_id,
            sequence=target_seq,
            sequence_name=target_name,
            sequence_id=target_seq_id
        )
        clf_id = clf_result["id"]

        # -------------------------------------------------------------
        # 5. Disease Prediction (Module 5)
        # -------------------------------------------------------------
        dis_result = process_disease_prediction(
            user_id=user_id,
            sequence=target_seq,
            sequence_name=target_name,
            sequence_id=target_seq_id
        )
        dis_id = dis_result["id"]

        # -------------------------------------------------------------
        # 6. Visualization & Consolidation (Module 6)
        # -------------------------------------------------------------
        vis_payload = generate_visualization_payload(target_seq, mut_data)

        summary_metrics = {
            "length": seq_metrics["length"],
            "gc_content": seq_metrics["gc_content"],
            "at_content": seq_metrics["at_content"],
            "similarity_percentage": alignment_data["similarity_percentage"],
            "total_mutations": mut_data["total_mutations"],
            "predicted_class": clf_result["predicted_class"],
            "class_confidence": clf_result["confidence"],
            "predicted_category": dis_result["predicted_category"],
            "disease_probability": dis_result["probability"],
            "risk_category": dis_result["risk_category"]
        }

        comp_id = create_complete_analysis(
            user_id=user_id,
            sequence_id=target_seq_id,
            ref_id=ref_seq_id,
            sequence_name=target_name,
            sa_id=sa_id,
            sim_id=sim_id,
            mut_id=mut_id,
            clf_id=clf_id,
            dis_id=dis_id,
            summary=summary_metrics
        )

        flash("Complete DNA Multi-Module Analysis successfully executed!", "success")
        return redirect(url_for('complete_analysis.result', analysis_id=comp_id))

    return render_template('analysis/complete.html', samples=SAMPLE_SEQUENCES)


@complete_bp.route('/result/<int:analysis_id>')
@login_required
def result(analysis_id: int):
    user_id = session['user_id']
    comp = get_complete_analysis_by_id(analysis_id, user_id)
    if not comp:
        flash("Complete analysis record not found.", "warning")
        return redirect(url_for('complete_analysis.index'))

    # Reconstruct visualization payload and alignment tokens
    from app.services.visualization_service import generate_visualization_payload
    from app.services.similarity_service import perform_pairwise_alignment

    seq = comp.get("sequence", "")
    mut_data = {
        "mutations_list": [],
        "total_mutations": comp.get("total_mutations", 0),
        "substitutions_count": comp.get("substitutions_count", 0),
        "insertions_count": comp.get("insertions_count", 0),
        "deletions_count": comp.get("deletions_count", 0)
    }

    vis_payload = generate_visualization_payload(seq, mut_data)
    comp["visualization"] = vis_payload

    # Reconstruct alignment blocks
    align_recomputed = perform_pairwise_alignment(
        comp.get('alignment_ref', '').replace('-', ''),
        comp.get('alignment_query', '').replace('-', '')
    )
    comp['visual_blocks'] = align_recomputed['visual_blocks']

    return render_template('analysis/complete_result.html', result=comp)


@complete_bp.route('/api/run', methods=['POST'])
@login_required
def run_ajax():
    """Asynchronous endpoint for dynamic frontend step-by-step progress tracking."""
    user_id = session['user_id']
    data = request.get_json() or {}
    raw_seq = data.get('sequence', '')
    ref_raw = data.get('reference_sequence', '')
    target_name = data.get('sequence_name', 'Target Sample Sequence').strip() or 'Target Sample Sequence'
    ref_name = data.get('reference_name', 'Wildtype Reference').strip() or 'Wildtype Reference'

    target_seq = sanitize_dna(raw_seq)
    if not ref_raw.strip():
        ref_seq = SAMPLE_SEQUENCES["human_tp53"]["sequence"]
        ref_name = "Standard Benchmark Reference (TP53)"
    else:
        ref_seq = sanitize_dna(ref_raw)

    v_tgt, err_tgt = validate_dna(target_seq)
    if not v_tgt:
        return jsonify({"success": False, "error": f"Target Sequence Error: {err_tgt}"}), 400

    v_ref, err_ref = validate_dna(ref_seq)
    if not v_ref:
        return jsonify({"success": False, "error": f"Reference Sequence Error: {err_ref}"}), 400

    try:
        # Execute all 6 modules
        seq_metrics = calculate_sequence_metrics(target_seq)
        target_seq_id = create_dna_sequence(user_id, target_name, target_seq, seq_metrics["length"], source_type='manual')
        ref_seq_id = create_dna_sequence(user_id, ref_name, ref_seq, len(ref_seq), source_type='reference')
    
        sa_id = save_sequence_analysis(
            user_id=user_id, sequence_id=target_seq_id, sequence_name=target_name,
            length=seq_metrics["length"], a_count=seq_metrics["a_count"], t_count=seq_metrics["t_count"],
            g_count=seq_metrics["g_count"], c_count=seq_metrics["c_count"],
            a_percentage=seq_metrics["a_percentage"], t_percentage=seq_metrics["t_percentage"],
            g_percentage=seq_metrics["g_percentage"], c_percentage=seq_metrics["c_percentage"],
            gc_content=seq_metrics["gc_content"], at_content=seq_metrics["at_content"],
            purine_count=seq_metrics["purine_count"], pyrimidine_count=seq_metrics["pyrimidine_count"],
            molecular_weight=seq_metrics["molecular_weight"]
        )
    
        alignment_data = perform_pairwise_alignment(ref_seq, target_seq)
        sim_id = save_similarity_analysis(
            user_id=user_id, ref_id=ref_seq_id, query_id=target_seq_id, ref_name=ref_name, query_name=target_name,
            ref_len=alignment_data["reference_length"], query_len=alignment_data["query_length"],
            sim_pct=alignment_data["similarity_percentage"], diff_pct=alignment_data["difference_percentage"],
            matches=alignment_data["match_count"], mismatches=alignment_data["mismatch_count"],
            gaps=alignment_data["gap_count"], score=alignment_data["alignment_score"],
            align_ref=alignment_data["alignment_ref"], align_query=alignment_data["alignment_query"],
            align_match=alignment_data["alignment_match"]
        )
    
        mut_data = detect_mutations(ref_seq, target_seq)
        mut_id = save_mutation_analysis(
            user_id=user_id, ref_id=ref_seq_id, sample_id=target_seq_id, ref_name=ref_name, sample_name=target_name,
            total_mut=mut_data["total_mutations"], subs=mut_data["substitutions_count"],
            ins=mut_data["insertions_count"], dels=mut_data["deletions_count"], mutation_rate=mut_data["mutation_rate"]
        )
        save_mutations_batch(user_id, mut_id, mut_data["mutations_list"])
    
        clf_result = process_dna_classification(user_id, target_seq, target_name, target_seq_id)
        dis_result = process_disease_prediction(user_id, target_seq, target_name, target_seq_id)
    
        summary_metrics = {
            "length": seq_metrics["length"],
            "gc_content": seq_metrics["gc_content"],
            "at_content": seq_metrics["at_content"],
            "similarity_percentage": alignment_data["similarity_percentage"],
            "total_mutations": mut_data["total_mutations"],
            "predicted_class": clf_result["predicted_class"],
            "class_confidence": clf_result["confidence"],
            "predicted_category": dis_result["predicted_category"],
            "disease_probability": dis_result["probability"],
            "risk_category": dis_result["risk_category"]
        }
    
        comp_id = create_complete_analysis(
            user_id=user_id, sequence_id=target_seq_id, ref_id=ref_seq_id, sequence_name=target_name,
            sa_id=sa_id, sim_id=sim_id, mut_id=mut_id, clf_id=clf_result["id"], dis_id=dis_result["id"],
            summary=summary_metrics
        )
    
        return jsonify({
            "success": True,
            "analysis_id": comp_id,
            "redirect_url": url_for('complete_analysis.result', analysis_id=comp_id),
            "summary": summary_metrics
        })
    except Exception as e:
        import traceback
        import logging
        logging.error("Error in Complete Analysis API: " + traceback.format_exc())
        return jsonify({
            "success": False,
            "error": "A database or execution error occurred. Please try logging out and logging back in. Detail: " + str(e)
        }), 500
