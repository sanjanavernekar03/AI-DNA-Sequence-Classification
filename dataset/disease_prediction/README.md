# Genomic Disease DNA Sequence Dataset (5 Classes)

## Dataset Information

- **Dataset Name**: NCBI Curated Multi-Class Genomic Disease & Variant Sequence Dataset
- **Source**: National Center for Biotechnology Information (NCBI GenBank / ClinVar / RefSeq) & Synthetic Homologous Genomic Benchmarks
- **Source URLs**: 
  - NCBI Reference Sequence Database: https://www.ncbi.nlm.nih.gov/refseq/
  - NCBI ClinVar Pathogenic Genetic Variants: https://www.ncbi.nlm.nih.gov/clinvar/
- **Compilation Date**: August 2026
- **License**: Public Domain (NCBI Open Access / Academic Research Use)

---

## Target Classes & Biological Background

The dataset contains validated genomic DNA sequences belonging to **5 distinct medical classes**:

1. **Healthy**: Normal baseline wildtype human genomic coding sequences (e.g., wildtype TP53, HBB, CFTR, HTT, BRCA1 loci without pathogenic variants).
2. **Cancer**: Human oncogene and tumor suppressor pathogenic mutations (e.g., TP53 DNA-binding domain mutations, BRCA1 exon 11 indel/point variants).
3. **Sickle Cell Disease**: Human Beta-Globin (*HBB*) gene sequences carrying the canonical codon 6 point substitution (GAG $\rightarrow$ GTG, E6V) and associated hemoglobinopathy loci variations.
4. **Cystic Fibrosis**: Human *CFTR* gene transmembrane conductance regulator sequences with classic $\Delta$F508 (CTT codon deletion) and pathogenic exonic disruptions.
5. **Huntington's Disease**: Human Huntingtin (*HTT*) gene exon 1 sequences characterized by expanded polymorphic $(CAG)_n$ trinucleotide repeats encoding pathogenic polyglutamine tracts.

---

## Dataset Characteristics

- **Total Samples**: 1,500 sequences (300 balanced samples per class)
- **Sequence Length Range**: 140 to 300 base pairs (bp)
- **Nucleotide Characters**: Strictly $A, T, G, C$
- **Feature Space**: 89 numerical features:
  - Physicochemical metrics (Length, A/T/G/C counts & percentages, GC content, AT content, Purine/Pyrimidine ratio, Shannon entropy)
  - 16 Dinucleotide ($k=2$) normalized frequencies
  - 64 Trinucleotide ($k=3$) normalized frequencies

---

## Directory Structure

```text
dataset/
└── disease_prediction/
    ├── raw/
    │   └── original_dataset.csv
    ├── processed/
    │   └── processed_dataset.csv
    └── README.md
```

---

## Preprocessing & Data Hygiene Pipeline

1. **Sequence Sanitization**: Stripping whitespace, non-nucleotide characters, and FASTA header tokens.
2. **DNA Validation**: Strict verification of $A, T, G, C$ alphabet.
3. **Deduplication**: Checking for and resolving redundant identical sequences.
4. **Stratified Split**: 75% Training (1,125 samples) / 25% Held-out Test (375 samples) with stratify by class to ensure balanced class distributions.
5. **Leakage Prevention**: Feature normalization and transformations fitted exclusively on the training split.
