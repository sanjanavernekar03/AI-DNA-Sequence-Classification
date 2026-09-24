from typing import Dict, Any, List
from app.services.dna_service import calculate_sequence_metrics, sanitize_dna
from app.ml.feature_extraction import compute_kmer_frequencies


def generate_visualization_payload(sequence: str, mutation_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate structured datasets for Chart.js rendering across multiple visualization modes.
    """
    metrics = calculate_sequence_metrics(sequence)
    seq = metrics["cleaned_sequence"]

    # 1. Nucleotide Distribution Bar Chart
    nucleotide_bar = {
        "labels": ["Adenine (A)", "Thymine (T)", "Guanine (G)", "Cytosine (C)"],
        "datasets": [{
            "label": "Count (bp)",
            "data": [metrics["a_count"], metrics["t_count"], metrics["g_count"], metrics["c_count"]],
            "backgroundColor": [
                "rgba(16, 185, 129, 0.8)",  # Green
                "rgba(239, 68, 68, 0.8)",   # Red
                "rgba(245, 158, 11, 0.8)",  # Amber
                "rgba(59, 130, 246, 0.8)"   # Blue
            ],
            "borderColor": [
                "#10B981", "#EF4444", "#F59E0B", "#3B82F6"
            ],
            "borderWidth": 1.5
        }]
    }

    # 2. Nucleotide Percentage Doughnut
    nucleotide_doughnut = {
        "labels": ["Adenine (A)", "Thymine (T)", "Guanine (G)", "Cytosine (C)"],
        "datasets": [{
            "data": [metrics["a_percentage"], metrics["t_percentage"], metrics["g_percentage"], metrics["c_percentage"]],
            "backgroundColor": [
                "rgba(16, 185, 129, 0.85)",
                "rgba(239, 68, 68, 0.85)",
                "rgba(245, 158, 11, 0.85)",
                "rgba(59, 130, 246, 0.85)"
            ],
            "borderColor": "#1E293B",
            "borderWidth": 2
        }]
    }

    # 3. GC vs AT Content Comparison
    gc_vs_at = {
        "labels": ["GC Content (%)", "AT Content (%)"],
        "datasets": [{
            "data": [metrics["gc_content"], metrics["at_content"]],
            "backgroundColor": [
                "rgba(6, 182, 212, 0.85)",  # Cyan
                "rgba(168, 85, 247, 0.85)"  # Purple
            ],
            "borderColor": "#1E293B",
            "borderWidth": 2
        }]
    }

    # 4. Top 10 Trinucleotide (3-mer) Frequencies
    kmers_dict = compute_kmer_frequencies(seq, k=3)
    sorted_kmers = sorted(kmers_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    kmer_chart = {
        "labels": [k[0] for k in sorted_kmers],
        "datasets": [{
            "label": "Frequency",
            "data": [k[1] for k in sorted_kmers],
            "backgroundColor": "rgba(99, 102, 241, 0.75)",
            "borderColor": "#6366F1",
            "borderWidth": 1.5
        }]
    }

    # 5. Mutation Position Visualization (if present)
    mutation_chart = None
    if mutation_data and mutation_data.get("mutations_list"):
        mutations = mutation_data["mutations_list"]
        sub_pts = []
        ins_pts = []
        del_pts = []

        for m in mutations:
            pos = m["position"]
            mtype = m["type"]
            if mtype == "Substitution":
                sub_pts.append({"x": pos, "y": 1, "label": f"{m['ref_base']}->{m['obs_base']} @ {pos}"})
            elif mtype == "Insertion":
                ins_pts.append({"x": pos, "y": 2, "label": f"+{m['obs_base']} @ {pos}"})
            elif mtype == "Deletion":
                del_pts.append({"x": pos, "y": 3, "label": f"-{m['ref_base']} @ {pos}"})

        mutation_chart = {
            "datasets": [
                {
                    "label": f"Substitutions ({len(sub_pts)})",
                    "data": sub_pts,
                    "backgroundColor": "rgba(239, 68, 68, 0.9)",
                    "pointRadius": 6
                },
                {
                    "label": f"Insertions ({len(ins_pts)})",
                    "data": ins_pts,
                    "backgroundColor": "rgba(16, 185, 129, 0.9)",
                    "pointRadius": 6
                },
                {
                    "label": f"Deletions ({len(del_pts)})",
                    "data": del_pts,
                    "backgroundColor": "rgba(245, 158, 11, 0.9)",
                    "pointRadius": 6
                }
            ],
            "sequence_length": metrics["length"]
        }

    return {
        "metrics": metrics,
        "nucleotide_bar": nucleotide_bar,
        "nucleotide_doughnut": nucleotide_doughnut,
        "gc_vs_at": gc_vs_at,
        "kmer_chart": kmer_chart,
        "mutation_chart": mutation_chart
    }
