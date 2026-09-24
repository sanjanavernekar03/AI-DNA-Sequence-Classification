from typing import Dict, Any, List
from app.services.dna_service import sanitize_dna
from app.services.similarity_service import perform_pairwise_alignment


def detect_mutations(reference_seq: str, sample_seq: str) -> Dict[str, Any]:
    """
    Detect substitutions, insertions, and deletions between reference and sample sequences.
    """
    ref = sanitize_dna(reference_seq)
    sample = sanitize_dna(sample_seq)

    alignment = perform_pairwise_alignment(ref, sample)
    aligned_ref = alignment["alignment_ref"]
    aligned_sample = alignment["alignment_query"]

    mutations = []
    substitutions = 0
    insertions = 0
    deletions = 0

    ref_pos = 0
    sample_pos = 0

    for i in range(len(aligned_ref)):
        r_char = aligned_ref[i]
        s_char = aligned_sample[i]

        if r_char != "-":
            ref_pos += 1
        if s_char != "-":
            sample_pos += 1

        if r_char == s_char:
            continue

        # Substitution: both have valid characters, but differ
        if r_char != "-" and s_char != "-":
            substitutions += 1
            # Transition vs Transversion classification
            purines = {"A", "G"}
            pyrimidines = {"C", "T"}
            if (r_char in purines and s_char in purines) or (r_char in pyrimidines and s_char in pyrimidines):
                sub_type = "Transition (Substitution)"
            else:
                sub_type = "Transversion (Substitution)"

            mutations.append({
                "position": ref_pos,
                "type": "Substitution",
                "sub_type": sub_type,
                "ref_base": r_char,
                "obs_base": s_char,
                "context": f"{r_char}{ref_pos}{s_char}",
                "note": f"Point variation at coordinate {ref_pos}: {r_char} mutated to {s_char} ({sub_type})"
            })

        # Deletion: present in reference, absent (gap) in sample
        elif r_char != "-" and s_char == "-":
            deletions += 1
            mutations.append({
                "position": ref_pos,
                "type": "Deletion",
                "sub_type": "Frameshift/Indel Deletion",
                "ref_base": r_char,
                "obs_base": "-",
                "context": f"del_{r_char}{ref_pos}",
                "note": f"Nucleotide '{r_char}' at reference position {ref_pos} missing in sample"
            })

        # Insertion: absent (gap) in reference, present in sample
        elif r_char == "-" and s_char != "-":
            insertions += 1
            mutations.append({
                "position": ref_pos if ref_pos > 0 else 1,
                "type": "Insertion",
                "sub_type": "Frameshift/Indel Insertion",
                "ref_base": "-",
                "obs_base": s_char,
                "context": f"ins_{s_char}@{ref_pos}",
                "note": f"Novel nucleotide '{s_char}' inserted adjacent to reference coordinate {ref_pos}"
            })

    total_mutations = substitutions + insertions + deletions
    ref_len = len(ref) if len(ref) > 0 else 1
    mutation_rate = round((total_mutations / ref_len) * 100.0, 2)

    # Bin mutations for density visualization across sequence segments (e.g. 10 bins)
    num_bins = 10
    bin_size = max(1, ref_len // num_bins)
    mutation_bins = [0] * num_bins
    bin_labels = []

    for b in range(num_bins):
        start = b * bin_size + 1
        end = (b + 1) * bin_size if b < num_bins - 1 else ref_len
        bin_labels.append(f"{start}-{end} bp")

    for m in mutations:
        pos = m["position"]
        bin_idx = min(num_bins - 1, (pos - 1) // bin_size)
        if 0 <= bin_idx < num_bins:
            mutation_bins[bin_idx] += 1

    return {
        "reference_length": len(ref),
        "sample_length": len(sample),
        "total_mutations": total_mutations,
        "substitutions_count": substitutions,
        "insertions_count": insertions,
        "deletions_count": deletions,
        "mutation_rate": mutation_rate,
        "mutations_list": mutations,
        "density_labels": bin_labels,
        "density_counts": mutation_bins,
        "alignment_summary": {
            "similarity_percentage": alignment["similarity_percentage"],
            "difference_percentage": alignment["difference_percentage"],
            "match_count": alignment["match_count"]
        }
    }
