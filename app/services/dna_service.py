import re
from typing import Dict, Any, Tuple, Optional

VALID_NUCLEOTIDES = set("ATGC")

# Benchmark clinical & research genomic sequences for all 5 disease categories
SAMPLE_SEQUENCES = {
    "healthy_normal": {
        "name": "Healthy Normal Genomic Allele (Wildtype)",
        "description": "Standard healthy wildtype human genomic coding sequence without pathogenic variants",
        "disease_target": "Healthy",
        "sequence": "ACTCCTGAGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGGCTGCTGGTGGTCTACCCTTGGACCCAGAGGTTCTTTGAGTCCTTTGGGGATCTGTCCACTCCTGATGCTGTTATGGGCAACCCTAAGGTGAAGGCTCATGGCAAGAAAGTGCTCGGTGCCTTTAGTGATGGCCTGGCT"
    },
    "cancer_tp53": {
        "name": "Cancer Associated Pathogenic Locus (TP53/BRCA1)",
        "description": "Human tumor suppressor pathogenic hotspot with somatic mutation signatures",
        "disease_target": "Cancer",
        "sequence": "ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAAGCAATGGATGATTTGATGCTGTCCCCGGACGATATTGAACAATGGTTCACTGAAGACCCAGGTCCAGATGAAGCTCCCAGAATGCCAGAGGCTGCTCCCCGCGTGGCCCCTGCACCAGCAGCTCCT"
    },
    "sickle_cell_hbb": {
        "name": "Sickle Cell Disease (HBB Codon 6 E6V Mutation)",
        "description": "Human Beta-Globin coding sequence carrying the classic GAG -> GTG (Glu -> Val) point mutation",
        "disease_target": "Sickle Cell Disease",
        "sequence": "ATGGTGCACCTGACTCCTGTGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGGCTGCTGGTGGTCTACCCTTGGACCCAGAGGTTCTTTGAGTCCTTTGGGGATCTGTCCACTCCTGATGCTGTTATGGGCAACCCTAAGGTGAAGGCTCATGGCAAGAAAGTGCTCGGTGCCTTTAGTGATGGCCTGGCT"
    },
    "cystic_fibrosis_cftr": {
        "name": "Cystic Fibrosis (CFTR Delta-F508 Hotspot)",
        "description": "Human CFTR gene transmembrane domain featuring the canonical CTT codon deletion",
        "disease_target": "Cystic Fibrosis",
        "sequence": "ATGCAGAGGTCGCCTCTGGAAAAGGCCAGCGTTGTCTCCAAACTTTTTTTCAGCTGGACCAGACCAATTTTGAGGAAAGGATACAGACAGCGCCTGGAATTGTCAGACATATACCAAATCCCTTCTGTTGATTCTGCTGACAATCTATCTGAAAAATTGGAAAGAGAATGGGATAGAGAGCTGGCTTCAAAGAAAAATCCTAAACTCATTAATGCCCTTCGGCGATGTTTTTTCTGG"
    },
    "huntingtons_disease_htt": {
        "name": "Huntington's Disease (HTT Polyglutamine CAG Expansion)",
        "description": "Human Huntingtin gene exon 1 carrying expanded pathogenic (CAG)n trinucleotide repeats",
        "disease_target": "Huntington's Disease",
        "sequence": "ATGGCGACCCTGGAAAAGCTGATGAAGGCCTTCGAGTCCCTCAAGTCCTTCCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAGCAACAGCCGCCGCCGCCGCCGCCTCAACCTCCTCAG"
    },
    # Backward compatible aliases for all templates
    "human_tp53": {
        "name": "Human TP53 Tumor Suppressor Exon 4",
        "description": "Standard wildtype sequence of human tumor protein p53 exon 4 (Homo sapiens)",
        "disease_target": "Cancer",
        "sequence": "ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAAGCAATGGATGATTTGATGCTGTCCCCGGACGATATTGAACAATGGTTCACTGAAGACCCAGGTCCAGATGAAGCTCCCAGAATGCCAGAGGCTGCTCCCCGCGTGGCCCCTGCACCAGCAGCTCCT"
    },
    "brca1_exon11": {
        "name": "BRCA1 Hereditary Breast/Ovarian Cancer Gene Exon 11",
        "description": "Human Breast Cancer type 1 susceptibility protein exon 11 reference segment",
        "disease_target": "Cancer",
        "sequence": "ATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGAGTGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAATTTTGCATGCTGAAACTTCTCAACCAGAAGAAAGGGCCTTCACAGTGTCCTTTATGTAAGAATGATATAACCAAAAGGAGCCTACAAGAAAGTACGAGATTTAGTCA"
    },
    "hbb_sickle_cell": {
        "name": "Human Beta-Globin (HBB) Wildtype Reference",
        "description": "Human hemoglobin subunit beta (HBB) wildtype sequence at codon 6",
        "disease_target": "Sickle Cell Disease",
        "sequence": "ATGGTGCACCTGACTCCTGAGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGGCTGCTGGTGGTCTACCCTTGGACCCAGAGGTTCTTTGAGTCCTTTGGGGATCTGTCCACTCCTGATGCTGTTATGGGCAACCCTAAGGTGAAGGCTCATGGCAAGAAAGTGCTCGGTGCCTTTAGTGATGGCCTGGCT"
    },
    "cftr_delta_f508": {
        "name": "CFTR Cystic Fibrosis Transmembrane Conductance Exon 10",
        "description": "Human CFTR reference locus containing Phe508 codon region",
        "disease_target": "Cystic Fibrosis",
        "sequence": "ATGCAGAGGTCGCCTCTGGAAAAGGCCAGCGTTGTCTCCAAACTTTTTTTCAGCTGGACCAGACCAATTTTGAGGAAAGGATACAGACAGCGCCTGGAATTGTCAGACATATACCAAATCCCTTCTGTTGATTCTGCTGACAATCTATCTGAAAAATTGGAAAGAGAATGGGATAGAGAGCTGGCTTCAAAGAAAAATCCTAAACTCATTAATGCCCTTCGGCGATGTTTTTTCTGG"
    }
}


def sanitize_dna(raw_sequence: str) -> str:
    """Strip whitespace, newlines, tabs, and convert to uppercase."""
    if not raw_sequence:
        return ""
    lines = raw_sequence.strip().splitlines()
    cleaned_lines = []
    for line in lines:
        line_str = line.strip()
        if line_str.startswith(">") or line_str.startswith(";"):
            continue
        cleaned_lines.append(line_str)
    combined = "".join(cleaned_lines)
    return re.sub(r"\s+", "", combined).upper()


def validate_dna(sequence: str) -> Tuple[bool, Optional[str]]:
    """Validate that the cleaned sequence contains strictly A, T, G, C nucleotides."""
    cleaned = sanitize_dna(sequence)
    if not cleaned:
        return False, "DNA sequence cannot be empty. Please enter or upload a valid sequence."

    invalid_chars = set(cleaned) - VALID_NUCLEOTIDES
    if invalid_chars:
        chars_display = ", ".join(f"'{c}'" for c in sorted(invalid_chars))
        return False, f"Invalid DNA sequence. Detected invalid character(s): {chars_display}. Only A, T, G, and C are permitted."

    return True, None


def parse_fasta(file_content: str) -> Tuple[str, str, Optional[str]]:
    """Parse a FASTA formatted string or plain text file content."""
    if not file_content:
        return "", "", "Uploaded file is empty."

    lines = file_content.strip().splitlines()
    header = "Uploaded_DNA_Sequence"
    seq_parts = []

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        if line_str.startswith(">"):
            header = line_str[1:].strip()
        elif not line_str.startswith(";"):
            seq_parts.append(line_str)

    raw_seq = "".join(seq_parts)
    cleaned = sanitize_dna(raw_seq)

    is_valid, error = validate_dna(cleaned)
    if not is_valid:
        return header, "", error

    return header, cleaned, None


def calculate_sequence_metrics(sequence: str) -> Dict[str, Any]:
    """Calculate comprehensive nucleotide composition and physicochemical statistics."""
    cleaned = sanitize_dna(sequence)
    length = len(cleaned)
    if length == 0:
        return {
            "length": 0, "a_count": 0, "t_count": 0, "g_count": 0, "c_count": 0,
            "a_percentage": 0.0, "t_percentage": 0.0, "g_percentage": 0.0, "c_percentage": 0.0,
            "gc_content": 0.0, "at_content": 0.0, "purine_count": 0, "pyrimidine_count": 0,
            "purine_percentage": 0.0, "pyrimidine_percentage": 0.0, "molecular_weight": 0.0,
            "cleaned_sequence": ""
        }

    a_count = cleaned.count("A")
    t_count = cleaned.count("T")
    g_count = cleaned.count("G")
    c_count = cleaned.count("C")

    a_pct = round((a_count / length) * 100.0, 2)
    t_pct = round((t_count / length) * 100.0, 2)
    g_pct = round((g_count / length) * 100.0, 2)
    c_pct = round((c_count / length) * 100.0, 2)

    gc_content = round(((g_count + c_count) / length) * 100.0, 2)
    at_content = round(((a_count + t_count) / length) * 100.0, 2)

    purines = a_count + g_count
    pyrimidines = t_count + c_count
    purine_pct = round((purines / length) * 100.0, 2)
    pyrimidine_pct = round((pyrimidines / length) * 100.0, 2)

    molecular_weight = round((a_count * 313.21) + (t_count * 304.20) + (g_count * 329.21) + (c_count * 289.18) - 61.96, 2)
    if molecular_weight < 0:
        molecular_weight = 0.0

    return {
        "length": length,
        "a_count": a_count,
        "t_count": t_count,
        "g_count": g_count,
        "c_count": c_count,
        "a_percentage": a_pct,
        "t_percentage": t_pct,
        "g_percentage": g_pct,
        "c_percentage": c_pct,
        "gc_content": gc_content,
        "at_content": at_content,
        "purine_count": purines,
        "pyrimidine_count": pyrimidines,
        "purine_percentage": purine_pct,
        "pyrimidine_percentage": pyrimidine_pct,
        "molecular_weight": molecular_weight,
        "cleaned_sequence": cleaned
    }
