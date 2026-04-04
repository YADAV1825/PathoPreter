import pandas as pd
import glob
import os
import re

# ================= CONFIGURATION =================
TEST_SET_PATH = "test_unseen_variant_level.parquet"
RAW_CLINVAR_PATH = "data/variant_summary.txt" 
DBNSFP_FOLDER = "dbnsfp_data"
OUTPUT_FILE = "pathopreter_vs_sota.csv"
# =================================================

def extract_variant_nm(text):
    try:
        match = re.search(r"Variant:\s+([^\n\s]+)", text)
        if match:
            return match.group(1).strip()
    except:
        pass
    return None

print("🚀 STARTING BENCHMARK EXTRACTION")

# --- STEP 1: Load Test Set & Extract Names ---
print(f"\n[1/4] Loading Test Set from {TEST_SET_PATH}...")
df_test = pd.read_parquet(TEST_SET_PATH)
df_test['Name'] = df_test['text'].apply(extract_variant_nm)

print(f"Loaded {len(df_test)} rows.")

# --- STEP 2: Load ClinVar Summary to get Coordinates ---
print(f"\n[2/4] Loading ClinVar Summary (Mapping Name -> Chrom/Pos)...")
df_raw = pd.read_csv(
    RAW_CLINVAR_PATH, 
    sep='\t',
    usecols=['Name', 'Chromosome', 'PositionVCF', 'ReferenceAlleleVCF', 'AlternateAlleleVCF'],
    dtype={'Chromosome': str, 'PositionVCF': str}, 
    low_memory=False
)

test_names = set(df_test['Name'].unique())
df_raw = df_raw[df_raw['Name'].isin(test_names)]

df_mapped = df_test.merge(df_raw, on='Name', how='left')
df_ready = df_mapped.dropna(subset=['Chromosome', 'PositionVCF'])

df_ready['Chromosome'] = df_ready['Chromosome'].str.replace("chr", "", case=False)

df_ready['lookup_key'] = (
    df_ready['Chromosome'] + ":" + 
    df_ready['PositionVCF'] + ":" + 
    df_ready['ReferenceAlleleVCF'] + ":" + 
    df_ready['AlternateAlleleVCF']
)

lookup_set = set(df_ready['lookup_key'])
print(f"Successfully mapped {len(df_ready)} variants to genomic coordinates.")


# --- STEP 3: Scan dbNSFP for Scores ---
print(f"\n[3/4] Scanning dbNSFP database for CADD & REVEL scores...")

found_scores = []
dbnsfp_files = glob.glob(os.path.join(DBNSFP_FOLDER, "*variant.chr*"))
cols_to_use = ['#chr', 'pos(1-based)', 'ref', 'alt', 'CADD_phred', 'REVEL_score']

for f_path in sorted(dbnsfp_files):
    chr_name = os.path.basename(f_path).split('.')[-1]
    print(f"  > Scanning {chr_name}...", end="\r")
    
    try:
        chunk_iter = pd.read_csv(
            f_path, 
            sep='\t', 
            usecols=lambda c: c in cols_to_use, 
            chunksize=100000, 
            low_memory=False,
            dtype={'#chr': str, 'pos(1-based)': str}
        )
        
        for chunk in chunk_iter:
            chunk['lookup_key'] = (
                chunk['#chr'] + ":" + 
                chunk['pos(1-based)'] + ":" + 
                chunk['ref'] + ":" + 
                chunk['alt']
            )
            
            matches = chunk[chunk['lookup_key'].isin(lookup_set)]
            if not matches.empty:
                found_scores.append(matches[['lookup_key', 'CADD_phred', 'REVEL_score']])
                
    except Exception as e:
        print(f"\n    Skipping {chr_name}: {e}")

print(f"\n  > Finished scanning.")

# --- STEP 4: Merge & Save ---
print(f"\n[4/4] Merging and Saving...")

if found_scores:
    df_scores = pd.concat(found_scores)
    final_df = df_ready.merge(df_scores, on='lookup_key', how='left')
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ SUCCESS! Results saved to: {OUTPUT_FILE}")
else:
    print("\n❌ CRITICAL: No matching scores found.")
