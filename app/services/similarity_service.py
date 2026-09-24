from typing import Dict, Any, Tuple, List
from Bio.Align import PairwiseAligner
from app.services.dna_service import sanitize_dna, validate_dna


def perform_pairwise_alignment(ref_seq: str, query_seq: str) -> Dict[str, Any]:
    """
    Perform pairwise global sequence alignment between reference and query DNA sequences.
    """
    ref = sanitize_dna(ref_seq)
    query = sanitize_dna(query_seq)

    ref_len = len(ref)
    query_len = len(query)

    if ref_len == 0 or query_len == 0:
        return {
            "reference_length": ref_len,
            "query_length": query_len,
            "similarity_percentage": 0.0,
            "difference_percentage": 100.0,
            "match_count": 0,
            "mismatch_count": 0,
            "gap_count": 0,
            "alignment_score": 0.0,
            "alignment_ref": "",
            "alignment_query": "",
            "alignment_match": "",
            "visual_blocks": []
        }

    # Initialize Biopython PairwiseAligner
    aligner = PairwiseAligner()
    aligner.mode = 'global'
    aligner.match_score = 2.0
    aligner.mismatch_score = -1.0
    aligner.open_gap_score = -2.0
    aligner.extend_gap_score = -0.5

    alignments = aligner.align(ref, query)
    try:
        best_alignment = next(alignments)
        score = float(best_alignment.score)
        # Format alignment strings
        aligned_ref = str(best_alignment[0])
        aligned_query = str(best_alignment[1])
    except StopIteration:
        # Fallback simple alignment
        aligned_ref = ref
        aligned_query = query
        score = 0.0

    # Calculate matches, mismatches, gaps
    match_chars = []
    matches = 0
    mismatches = 0
    gaps = 0
    align_len = len(aligned_ref)

    for i in range(align_len):
        r_char = aligned_ref[i]
        q_char = aligned_query[i] if i < len(aligned_query) else "-"

        if r_char == q_char and r_char != "-":
            match_chars.append("|")
            matches += 1
        elif r_char == "-" or q_char == "-":
            match_chars.append(" ")
            gaps += 1
        else:
            match_chars.append("•")
            mismatches += 1

    match_str = "".join(match_chars)
    total_positions = matches + mismatches + gaps
    sim_pct = round((matches / total_positions) * 100.0, 2) if total_positions > 0 else 0.0
    diff_pct = round(100.0 - sim_pct, 2)

    # Build visual chunks for frontend rendering (50 characters per block)
    chunk_size = 50
    visual_blocks = []
    for start in range(0, align_len, chunk_size):
        end = min(start + chunk_size, align_len)
        block_ref = aligned_ref[start:end]
        block_query = aligned_query[start:end]
        block_match = match_str[start:end]

        # Generate styled HTML tokens
        html_tokens = []
        for j in range(len(block_ref)):
            rc = block_ref[j]
            qc = block_query[j]
            if rc == qc and rc != "-":
                status = "match"
            elif rc == "-" or qc == "-":
                status = "gap"
            else:
                status = "mismatch"
            html_tokens.append({
                "pos": start + j + 1,
                "ref": rc,
                "query": qc,
                "status": status
            })

        visual_blocks.append({
            "block_index": (start // chunk_size) + 1,
            "start_pos": start + 1,
            "end_pos": end,
            "ref_segment": block_ref,
            "query_segment": block_query,
            "match_segment": block_match,
            "tokens": html_tokens
        })

    return {
        "reference_length": ref_len,
        "query_length": query_len,
        "alignment_length": align_len,
        "similarity_percentage": sim_pct,
        "difference_percentage": diff_pct,
        "match_count": matches,
        "mismatch_count": mismatches,
        "gap_count": gaps,
        "alignment_score": score,
        "alignment_ref": aligned_ref,
        "alignment_query": aligned_query,
        "alignment_match": match_str,
        "visual_blocks": visual_blocks
    }
