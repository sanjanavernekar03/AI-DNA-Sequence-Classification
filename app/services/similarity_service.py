from typing import Dict, Any, Tuple, List
from app.services.dna_service import sanitize_dna, validate_dna


def _pure_python_needleman_wunsch(seq1: str, seq2: str, match_score: float = 2.0, mismatch_score: float = -1.0, gap_score: float = -2.0) -> Tuple[str, str, float]:
    """
    Pure-Python Needleman-Wunsch global pairwise sequence alignment algorithm.
    Used as a mathematically accurate fallback when native Biopython extensions (_pairwisealigner / _arraycore) are blocked by OS security policy.
    """
    m, n = len(seq1), len(seq2)
    dp = [[0.0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        dp[i][0] = i * gap_score
    for j in range(1, n + 1):
        dp[0][j] = j * gap_score

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s = match_score if seq1[i - 1] == seq2[j - 1] else mismatch_score
            diag = dp[i - 1][j - 1] + s
            up = dp[i - 1][j] + gap_score
            left = dp[i][j - 1] + gap_score
            dp[i][j] = max(diag, up, left)

    align1, align2 = [], []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            s = match_score if seq1[i - 1] == seq2[j - 1] else mismatch_score
            if dp[i][j] == dp[i - 1][j - 1] + s:
                align1.append(seq1[i - 1])
                align2.append(seq2[j - 1])
                i -= 1
                j -= 1
                continue
        if i > 0 and (j == 0 or dp[i][j] == dp[i - 1][j] + gap_score):
            align1.append(seq1[i - 1])
            align2.append('-')
            i -= 1
        else:
            align1.append('-')
            align2.append(seq2[j - 1])
            j -= 1

    return "".join(reversed(align1)), "".join(reversed(align2)), float(dp[m][n])


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

    aligned_ref = None
    aligned_query = None
    score = 0.0

    # Try Biopython PairwiseAligner first
    try:
        from Bio.Align import PairwiseAligner
        aligner = PairwiseAligner()
        aligner.mode = 'global'
        aligner.match_score = 2.0
        aligner.mismatch_score = -1.0
        aligner.open_gap_score = -2.0
        aligner.extend_gap_score = -0.5

        alignments = aligner.align(ref, query)
        best_alignment = next(alignments)
        score = float(best_alignment.score)
        aligned_ref = str(best_alignment[0])
        aligned_query = str(best_alignment[1])
    except Exception:
        # Fallback to pure Python Needleman-Wunsch global alignment when native extension is blocked
        aligned_ref, aligned_query, score = _pure_python_needleman_wunsch(ref, query, 2.0, -1.0, -2.0)

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
