import numpy as np
import pandas as pd
from typing import List, Tuple
from app.services.dna_service import sanitize_dna, validate_dna
from app.ml.feature_extraction import extract_dna_feature_vector, get_feature_names


def build_feature_matrix(sequences: List[str]) -> np.ndarray:
    """Transform a list of raw DNA strings into a 2D numpy feature matrix."""
    matrix = []
    for seq in sequences:
        cleaned = sanitize_dna(seq)
        if not cleaned:
            cleaned = "ATGC"
        vec = extract_dna_feature_vector(cleaned)
        matrix.append(vec)
    return np.vstack(matrix)
