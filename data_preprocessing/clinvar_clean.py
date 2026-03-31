import polars as pl
import os

def build_cleaned_parquet():
    txt_path = os.path.join("clinvar", "variant_summary.txt")
    output_path = os.path.join("clinvar", "clinvar_snvs_cleaned.parquet")
    
    print("Initializing Polars pipeline for filtering and binary classification...")
    
    query = (
        pl.scan_csv(
            txt_path,
            separator='\t',
            infer_schema_length=0,
            ignore_errors=True
        )
        # Filter for Single Nucleotide Variants and GRCh38 assembly
        .filter(pl.col("Type").str.to_lowercase() == "single nucleotide variant")
        .filter(pl.col("Assembly")  == "GRCh38")
        
        # Keep only the 4 target classifications
        .filter(
            pl.col("ClinicalSignificance").is_in([
                "Pathogenic",
                "Likely pathogenic",
                "Benign",
                "Likely benign"
            ])
        )
        
        # Remove rows with missing or placeholder VCF values
        .filter(
            pl.col("ReferenceAlleleVCF").is_not_null() &
            ~pl.col("ReferenceAlleleVCF").is_in(["na", "-"]) &
            pl.col("AlternateAlleleVCF").is_not_null() &
            ~pl.col("AlternateAlleleVCF").is_in(["na", "-"])
        )
        
        # Merge classifications into strict binary labels
        .with_columns(
            pl.when(pl.col("ClinicalSignificance").is_in(["Pathogenic", "Likely pathogenic"]))
            .then(pl.lit("Pathogenic"))
            .otherwise(pl.lit("Benign"))
            .alias("clean_label")
        )
        
        # Select and rename columns to match the target schema
        .select([
            pl.col("clean_label"),
            pl.col("Chromosome").alias("chrom"),
            pl.col("PositionVCF").alias("pos"),
            pl.col("ReferenceAlleleVCF").alias("ref"),
            pl.col("AlternateAlleleVCF").alias("alt")
        ])
        
        # Construct the unique variant_id
        .with_columns(
            variant_id=pl.concat_str(
                [pl.col("chrom"), pl.col("pos"), pl.col("ref"), pl.col("alt")],
                separator="_"
            )
        )
        
        # Deduplicate to prevent positional leakage
        .unique(subset=["variant_id"])
    )
    
    # Execute the lazy query across all CPU cores
    df = query.collect()
    
    # Save the final dataset to a Parquet file
    df.write_parquet(output_path)
    
    print("Processing complete.")
    print(f"Data saved to: {output_path}")
    print(f"Total unique rows in final curated dataset: {df.height}")
    
    # Print the final class distribution to verify the merge
    print("\nClass distribution in final Parquet:")
    print(df["clean_label"].value_counts())

if __name__ == '__main__':
    build_cleaned_parquet()