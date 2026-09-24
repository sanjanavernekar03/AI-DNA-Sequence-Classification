import itertools
import math
import numpy as np
from typing import Dict, List, Any

ALL_2MERS = ["".join(p) for p in itertools.product("ACGT", repeat=2)]
ALL_3MERS = ["".join(p) for p in itertools.product("ACGT", repeat=3)]

DIAGNOSTIC_4MERS = [
    "CCTG", "GTGG", "GAGT", "ACTC", "TGAG", "GAGG",
    "CAGC", "AGCA", "GCAG", "CAGC", "CCGC", "CGCC",
    "ATCA", "TCAT", "TTTG", "TTTC", "ATCG", "CGGT",
    "CCCC", "GGGG", "TGTA", "TGTG", "GTAG", "TTGG"
]

DIAGNOSTIC_5MERS = [
    "CAGCA", "GCAGC", "ATCGG", "TCGGT", "TGTGA",
    "GTGAC", "CCTGG", "CTGGG", "GAGTG", "AGTGG"
]


def compute_kmer_frequencies(sequence: str, k: int = 3) -> Dict[str, float]:
    """Compute normalized k-mer frequencies for a given DNA sequence."""
    seq = sequence.upper()
    total_kmers = len(seq) - k + 1

    if total_kmers <= 0:
        kmers = [
            "".join(p)
            for p in itertools.product("ACGT", repeat=k)
        ]
        return {kmer: 0.0 for kmer in kmers}

    kmer_counts = {}

    for i in range(total_kmers):
        kmer = seq[i:i + k]

        if all(base in "ACGT" for base in kmer):
            kmer_counts[kmer] = kmer_counts.get(kmer, 0) + 1

    all_possible = [
        "".join(p)
        for p in itertools.product("ACGT", repeat=k)
    ]

    return {
        kmer: round(kmer_counts.get(kmer, 0) / total_kmers, 5)
        for kmer in all_possible
    }


def compute_sequence_entropy(sequence: str) -> float:
    """Calculate Shannon entropy of nucleotide distribution."""
    seq = sequence.upper()
    length = len(seq)

    if length == 0:
        return 0.0

    entropy = 0.0

    for base in "ACGT":
        p = seq.count(base) / length

        if p > 0:
            entropy -= p * math.log2(p)

    return round(entropy, 4)


def extract_disease_feature_vector(sequence: str) -> np.ndarray:
    """
    Extract multi-dimensional numerical genomic feature representations:
    - Basic features: Length, A/T/G/C counts & percentages, GC content, AT content,
      Purine/Pyrimidine ratio, Entropy
    - 16 Dinucleotide frequencies (k=2)
    - 64 Trinucleotide frequencies (k=3)
    - Diagnostic 4-mer frequencies (24 features)
    - Specific clinical diagnostic markers
    """
    seq = sequence.upper()
    length = max(len(seq), 1)

    a_count = seq.count("A")
    t_count = seq.count("T")
    g_count = seq.count("G")
    c_count = seq.count("C")

    a_pct = a_count / length
    t_pct = t_count / length
    g_pct = g_count / length
    c_pct = c_count / length

    gc_content = g_pct + c_pct
    at_content = a_pct + t_pct

    purines = a_count + g_count
    pyrimidines = t_count + c_count

    purine_ratio = (
        purines / pyrimidines
        if pyrimidines > 0
        else 1.0
    )

    entropy = compute_sequence_entropy(seq)

    kmers_2 = compute_kmer_frequencies(seq, k=2)
    kmer_2_vals = [kmers_2[km] for km in ALL_2MERS]

    kmers_3 = compute_kmer_frequencies(seq, k=3)
    kmer_3_vals = [kmers_3[km] for km in ALL_3MERS]

    kmer_4_vals = [
        seq.count(m4) / max(1, length - 3)
        for m4 in DIAGNOSTIC_4MERS
    ]

    kmer_5_vals = [
        seq.count(m5) / max(1, length - 4)
        for m5 in DIAGNOSTIC_5MERS
    ]

    cag_count = seq.count("CAG") / max(1, length / 3)
    cag_repeats = seq.count("CAGCAG") / max(1, length / 6)

    gtg_hbb = seq.count("ACTCCTGTGGAG")
    gag_hbb = seq.count("ACTCCTGAGGAG")

    ctt_cftr = seq.count("CTT") / max(1, length / 3)
    del_cftr = seq.count("ATCGGT") / max(1, length / 6)

    tp53_mut = seq.count("TGTGAC") / max(1, length / 6)

    base_features = [
        length,
        a_count,
        t_count,
        g_count,
        c_count,
        a_pct,
        t_pct,
        g_pct,
        c_pct,
        gc_content,
        at_content,
        purine_ratio,
        entropy,
        cag_count,
        cag_repeats,
        gtg_hbb,
        gag_hbb,
        ctt_cftr,
        del_cftr,
        tp53_mut
    ]

    return np.array(
        base_features
        + kmer_2_vals
        + kmer_3_vals
        + kmer_4_vals
        + kmer_5_vals,
        dtype=np.float64
    )


def get_disease_feature_names() -> List[str]:
    base_names = [
        "length",
        "a_count",
        "t_count",
        "g_count",
        "c_count",
        "a_pct",
        "t_pct",
        "g_pct",
        "c_pct",
        "gc_content",
        "at_content",
        "purine_ratio",
        "entropy",
        "cag_codon_freq",
        "cag_tandem_repeats",
        "gtg_codon_freq",
        "gag_codon_freq",
        "ctt_codon_freq",
        "cftr_deltaF508_junction",
        "tp53_mut_motif"
    ]

    kmer2_names = ["dimer_" + km for km in ALL_2MERS]
    kmer3_names = ["trimer_" + km for km in ALL_3MERS]
    kmer4_names = ["diag4mer_" + km for km in DIAGNOSTIC_4MERS]
    kmer5_names = ["diag5mer_" + km for km in DIAGNOSTIC_5MERS]

    return (
        base_names
        + kmer2_names
        + kmer3_names
        + kmer4_names
        + kmer5_names
    )
