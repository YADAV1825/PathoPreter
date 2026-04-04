import pandas as pd
from pyfaidx import Fasta
from joblib import Parallel, delayed
import numpy as np
import os

# --- CONFIGURATION ---
PARQUET_FILE = "train_enriched.parquet"
FASTA_FILE = os.path.join("grch38", "GCA_000001405.29_GRCh38.p14_genomic.fna") 
REPORT_FILE = os.path.join("grch38", "GCA_000001405.29_GRCh38.p14_assembly_report.txt")
OUTPUT_FILE = "train_enriched_SEQUENCE.parquet"

# Context: How many bases before/after?
FLANK_SIZE = 500 

# Performance Settings
N_JOBS = 10  # Leaving 2 cores free for OS/Background tasks
CHUNK_SIZE = 10000 # Process rows in batches to keep RAM usage steady

def load_chrom_mapping(report_path):
    """Maps simple names (1, 2, X) to GenBank Accessions (CM000663.2)."""
    mapping = {}
    print(f"Loading chromosome mapping from {report_path}...")
    try:
        with open(report_path, 'r') as f:
            for line in f:
                if line.startswith('#'): continue
                parts = line.strip().split('\t')
                # NCBI Report format: 
                # Col 0: Sequence-Name (1), Col 4: GenBank-Accn (CM000663.2)
                if len(parts) >= 5:
                    common_name = parts[0]
                    genbank_accn = parts[4]
                    mapping[common_name] = genbank_accn
                    mapping[f"chr{common_name}"] = genbank_accn # Handle 'chr1' variant
    except Exception as e:
        print(f"Warning: Could not read report file: {e}")
    return mapping

def process_batch(df_batch, fasta_path, chrom_map, flank):
    """
    Worker function: Opens its own handle to the FASTA file (thread-safe)
    and processes a batch of rows.
    """
    # Open FASTA inside the worker to avoid pickling issues on Windows
    # pyfaidx is smart; it won't load the whole file, it just seeks.
    genes = Fasta(fasta_path)
    
    sequences = []
    
    for idx, row in df_batch.iterrows():
        try:
            chrom = str(row['chrom'])
            fasta_chrom = chrom_map.get(chrom)
            
            if not fasta_chrom:
                sequences.append(None)
                continue
                
            pos = int(row['pos'])
            
            # VCF is 1-based. Python is 0-based.
            # We want: [pos-1-flank : pos-1+flank+1]
            # Center base is at index (pos - 1)
            start = (pos - 1) - flank
            end = (pos - 1) + flank + 1 
            
            if start < 0: start = 0
            
            # Extract
            seq_obj = genes[fasta_chrom][start:end]
            sequences.append(seq_obj.seq.upper())
            
        except Exception:
            sequences.append(None)
            
    return sequences

def main():
    # 1. Load Data
    print(f"Reading {PARQUET_FILE}...")
    df = pd.read_parquet(PARQUET_FILE)
    print(f"Loaded {len(df)} rows.")

    # 2. Load Mapping
    chrom_map = load_chrom_mapping(REPORT_FILE)
    
    # 3. Validation Check (Important!)
    # We check if the 'ref' allele in your parquet matches the genome at that position.
    # If this fails, the coordinate math is wrong (0-based vs 1-based).
    print("Performing sanity check on first row...")
    try:
        check_row = df.iloc[0]
        check_genes = Fasta(FASTA_FILE)
        mapped_chrom = chrom_map.get(str(check_row['chrom']))
        if mapped_chrom:
            # Check just the center base
            center_idx = int(check_row['pos']) - 1
            ref_base = check_genes[mapped_chrom][center_idx].seq.upper()
            print(f"Pos: {check_row['pos']}, Parquet Ref: {check_row['ref']}, Genome Base: {ref_base}")
            if ref_base != check_row['ref']:
                print("⚠️ WARNING: Genome base does not match Parquet Ref! Check coordinate system.")
            else:
                print("✅ Sanity check passed: Ref matches Genome.")
    except Exception as e:
        print(f"Sanity check skipped: {e}")

    # 4. Prepare Batches for Parallel Processing
    # We split the dataframe into chunks
    batches = np.array_split(df, max(1, len(df) // CHUNK_SIZE))
    
    print(f"Starting parallel processing on {N_JOBS} cores...")
    
    # Run in parallel
    # n_jobs=N_JOBS uses your multiple cores
    # backend='loky' is robust for Windows
    results = Parallel(n_jobs=N_JOBS, backend='loky', verbose=5)(
        delayed(process_batch)(batch, FASTA_FILE, chrom_map, FLANK_SIZE) 
        for batch in batches
    )
    
    # 5. Assemble and Save
    print("Combining results...")
    # Flatten the list of lists
    flat_results = [item for sublist in results for item in sublist]
    
    df['raw_sequence'] = flat_results
    
    print(f"Saving to {OUTPUT_FILE}...")
    df.to_parquet(OUTPUT_FILE)
    print("Done!")

if __name__ == "__main__":
    main()
