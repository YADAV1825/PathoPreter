import polars as pl
from pathlib import Path

BASE_DIR = Path.cwd()
OUT_DIR = BASE_DIR / "tmp_gnomad"

print("Consolidating parallelized gnomAD Parquet files...")

# Polars can lazily scan and concatenate all parquet files matching the pattern instantly
gnomad_lazy = pl.scan_parquet(OUT_DIR / "gnomad_chr*.parquet")

# Execute the collection
gnomad_all = gnomad_lazy.collect()

print(f"Total SNVs extracted from gnomAD: {gnomad_all.height}")

# Save the consolidated gnomAD dataset
FINAL_GNOMAD = BASE_DIR / "gnomad_snv_af.parquet"
gnomad_all.write_parquet(FINAL_GNOMAD)
print(f"Consolidated gnomAD signal saved to: {FINAL_GNOMAD}")

# --- MERGE WITH CLINVAR ---

print("\nLoading cleaned ClinVar dataset...")
clinvar_path = BASE_DIR / "clinvar" / "clinvar_snvs_cleaned.parquet"
clinvar = pl.read_parquet(clinvar_path)

print("Merging ClinVar with gnomAD frequencies...")
# Perform a left join to keep all ClinVar rows intact
merged = clinvar.join(
    gnomad_all.select(["variant_id", "gnomad_af"]),
    on="variant_id",
    how="left"
)

# Variants absent from gnomAD get a default allele frequency of 0.0
merged = merged.with_columns(
    pl.col("gnomad_af").fill_null(0.0)
)

# Save the final merged dataset
OUT_MERGED = BASE_DIR / "clinvar" / "clinvar_gnomad_merged.parquet"
merged.write_parquet(OUT_MERGED)

print(f"Merge complete. Final dataset saved to: {OUT_MERGED}")
print(f"Total rows in final dataset: {merged.height}")
