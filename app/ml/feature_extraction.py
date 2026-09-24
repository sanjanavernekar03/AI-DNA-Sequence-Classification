import itertools
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Any


ALL_3MERS = ["".join(p) for p in itertools.product("ACGT", repeat=3)]
ALL_2MERS = ["".join(p) for p in itertools.product("ACGT", repeat=2)]


import collections

def compute_kmer_frequencies(sequence: str, k: int = 3) -> Dict[str, float]:
    """Compute normalized k-mer frequencies for a given DNA sequence."""
    seq = sequence.upper()
    total_kmers = len(seq) - k + 1
    if total_kmers <= 0:
        kmers = ["".join(p) for p in itertools.product("ACGT", repeat=k)]
        return {kmer: 0.0 for kmer in kmers}

    # Extremely fast C-optimized counting. Since sanitize_dna ensures only ACGT, we skip validation.
    kmers = [seq[i:i+k] for i in range(total_kmers)]
    kmer_counts = collections.Counter(kmers)

    all_possible = ["".join(p) for p in itertools.product("ACGT", repeat=k)]
    return {kmer: round(kmer_counts.get(kmer, 0) / total_kmers, 5) for kmer in all_possible}


def compute_sequence_entropy(sequence: str) -> float:
    """Calculate Shannon entropy of the nucleotide distribution."""
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


def extract_dna_feature_vector(sequence: str) -> np.ndarray:
    """
    Extract a rich multi-dimensional numerical feature vector from a DNA sequence:
    - Sequence length
    - A, T, G, C frequencies
    - GC content and AT content
    - Purine/Pyrimidine ratio
    - Dinucleotide (2-mer) frequencies (16 features)
    - Trinucleotide (3-mer) frequencies (64 features)
    - Shannon entropy
    """
    seq = sequence.upper()
    length = max(len(seq), 1)

    a_freq = seq.count("A") / length
    t_freq = seq.count("T") / length
    g_freq = seq.count("G") / length
    c_freq = seq.count("C") / length

    gc_content = (g_freq + c_freq)
    at_content = (a_freq + t_freq)
    purines = (a_freq + g_freq)
    pyrimidines = (t_freq + c_freq)
    purine_ratio = purines / pyrimidines if pyrimidines > 0 else 1.0

    entropy = compute_sequence_entropy(seq)

    # 2-mer frequencies (16)
    kmers_2 = compute_kmer_frequencies(seq, k=2)
    kmer_2_vals = [kmers_2[km] for km in ALL_2MERS]

    # 3-mer frequencies (64)
    kmers_3 = compute_kmer_frequencies(seq, k=3)
    kmer_3_vals = [kmers_3[km] for km in ALL_3MERS]

    base_features = [
        length,
        a_freq,
        t_freq,
        g_freq,
        c_freq,
        gc_content,
        at_content,
        purine_ratio,
        entropy
    ]

    return np.array(base_features + kmer_2_vals + kmer_3_vals, dtype=np.float64)


def get_feature_names() -> List[str]:
    """Return explicit names for all extracted features."""
    base_names = [
        "length", "a_freq", "t_freq", "g_freq", "c_freq",
        "gc_content", "at_content", "purine_ratio", "entropy"
    ]
    kmer2_names = [f"dimer_{km}" for km in ALL_2MERS]
    kmer3_names = [f"trimer_{km}" for km in ALL_3MERS]
    return base_names + kmer2_names + kmer3_names
