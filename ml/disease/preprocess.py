import os
import sys
import random
import re
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from ml.disease.feature_extraction import extract_disease_feature_vector


# Biological sequence blueprints and motifs for the 5 target classes
DISEASE_PROFILES = {
    "Healthy": {
        "description": "Wildtype Normal Human Genomic Alleles",
        "motifs": [
            "ACTCCTGAGGAG",  # HBB Normal Codon 6 (GAG)
            "CCTGTGGGGCAAG", "GTGGATGAAGTTG", "TGTTATGGGCAAC", "GTGCTCGGTGCC", # Normal HBB backbone
            "ACAAAGTGTGAC",  # BRCA1 Normal Exon 11
            "ATCATCTTTGGT",  # CFTR Normal Exon 10 (contains CTT)
            "CAGCAGCAGCAACAG", # HTT Normal Short Repeats (<20 CAGs)
            "ATGGAGGAGCCG"   # TP53 Normal N-terminal Exon
        ],
        "base_bias": [0.26, 0.24, 0.25, 0.25]
    },
    "Cancer": {
        "description": "Oncogene & Tumor Suppressor Pathogenic Mutation Sequences (TP53, BRCA1, KRAS)",
        "motifs": [
            "TCCCATCTG", "TGTGACCAC", "AAAAGGAGCCTA", "TGTAAGAATG", "CGTCCCCCTTGCCG", "GTAGTTGGAGCT"
        ],
        "base_bias": [0.30, 0.22, 0.22, 0.26]
    },
    "Sickle Cell Disease": {
        "description": "Human Beta-Globin (HBB) Codon 6 Pathogenic E6V Mutation (GAG -> GTG)",
        "motifs": [
            "ACTCCTGTGGAG",  # Canonical Sickle Cell Codon 6 (GTG)
            "CCTGTGGGGCAAG", "GTGGATGAAGTTG", "TGTTATGGGCAAC", "GTGCTCGGTGCC"
        ],
        "base_bias": [0.20, 0.24, 0.33, 0.23]
    },
    "Cystic Fibrosis": {
        "description": "Human CFTR Gene Delta-F508 CTT Deletion & Transmembrane Hotspots",
        "motifs": [
            "ATCATCGGTGTT",  # CFTR delta-F508 deletion (CTT deleted between ATC & GGT)
            "TTTTTTTCAGCTGG", "AGAAAGGATACAGA", "CCTTCGGCGATG", "GTTTTTTCTGGA"
        ],
        "base_bias": [0.23, 0.35, 0.21, 0.21]
    },
    "Huntington's Disease": {
        "description": "Human Huntingtin (HTT) Gene Exon 1 Expanded Pathogenic Polyglutamine (CAG)n Repeats",
        "motifs": [
            "CAGCAGCAGCAGCAGCAGCAGCAGCAGCAG",  # Expanded pathogenic polyglutamine tract (30+ bp CAG)
            "CAGCAGCAGCAGCAGCAG", "GCAGCAGCAGCAGCAGC", "CCGCCGCCGCCG"
        ],
        "base_bias": [0.28, 0.08, 0.38, 0.26]  # High CAG composition
    }
}


def sanitize_sequence(seq: str) -> str:
    """Remove headers, whitespaces, and convert to uppercase."""
    lines = [line.strip() for line in str(seq).splitlines() if not line.strip().startswith(">") and not line.strip().startswith(";")]
    cleaned = "".join(lines)
    return re.sub(r"\s+", "", cleaned).upper()


def is_valid_dna(seq: str) -> bool:
    """Validate that string contains only A, T, G, C and minimum length."""
    if not seq or len(seq) < 30:
        return False
    return set(seq).issubset(set("ATGC"))


def generate_sample_for_class(cls_name: str, length: int = 180) -> str:
    """Generate realistic genomic sequence representative of the class."""
    profile = DISEASE_PROFILES[cls_name]
    bases = ["A", "C", "G", "T"]
    seq_list = random.choices(bases, weights=profile["base_bias"], k=length)

    motifs = profile["motifs"]
    num_motifs = random.randint(2, 4) if cls_name != "Huntington's Disease" else random.randint(3, 5)

    for _ in range(num_motifs):
        motif = random.choice(motifs)
        pos = random.randint(0, max(0, length - len(motif)))
        for i, char in enumerate(motif):
            if char in "ACGT":
                seq_list[pos + i] = char

    return "".join(seq_list)


def create_and_preprocess_dataset(samples_per_class: int = 300) -> pd.DataFrame:
    """
    Generate raw dataset, clean and validate sequences, save raw and processed CSVs.
    """
    raw_dir = BASE_DIR / "dataset" / "disease_prediction" / "raw"
    proc_dir = BASE_DIR / "dataset" / "disease_prediction" / "processed"
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(proc_dir, exist_ok=True)

    data = []
    classes = list(DISEASE_PROFILES.keys())

    random.seed(42)
    np.random.seed(42)

    for cls in classes:
        for i in range(samples_per_class):
            length = random.randint(140, 260)
            seq = generate_sample_for_class(cls, length)
            data.append({
                "sequence_id": f"GENOMIX_{cls[:3].upper()}_{i+1:04d}",
                "sequence": seq,
                "disease_category": cls,
                "sequence_length": len(seq),
                "source_locus": DISEASE_PROFILES[cls]["description"]
            })

    raw_df = pd.DataFrame(data)
    # Shuffle
    raw_df = raw_df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    raw_path = raw_dir / "original_dataset.csv"
    raw_df.to_csv(raw_path, index=False)
    print(f"Raw dataset written to: {raw_path} ({len(raw_df)} records)")

    # Preprocessing & Validation
    cleaned_rows = []
    for _, row in raw_df.iterrows():
        clean_seq = sanitize_sequence(row["sequence"])
        if is_valid_dna(clean_seq):
            cleaned_rows.append({
                "sequence_id": row["sequence_id"],
                "sequence": clean_seq,
                "disease_category": row["disease_category"],
                "sequence_length": len(clean_seq),
                "gc_content": round(((clean_seq.count("G") + clean_seq.count("C")) / len(clean_seq)) * 100, 2),
                "source_locus": row["source_locus"]
            })

    proc_df = pd.DataFrame(cleaned_rows)
    proc_path = proc_dir / "processed_dataset.csv"
    proc_df.to_csv(proc_path, index=False)
    print(f"Processed dataset written to: {proc_path} ({len(proc_df)} verified records)")

    return proc_df


if __name__ == "__main__":
    create_and_preprocess_dataset(samples_per_class=300)
