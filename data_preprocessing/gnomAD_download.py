import os
import subprocess
import gzip
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import multiprocessing as mp

BASE_DIR = Path.cwd()
GNOMAD_DIR = BASE_DIR / "gnomad_exomes_v4"
OUT_DIR = BASE_DIR / "tmp_gnomad"

GNOMAD_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

CHROMS = [f"chr{i}" for i in range(1, 23)] + ["chrX", "chrY"]
BASE_VCF_URL = "https://storage.googleapis.com/gcp-public-data--gnomad/release/4.1/vcf/exomes/"

def download_file(url, out_path):
    if not out_path.exists():
        subprocess.run(["wget", "-c", "-O", str(out_path), url], check=True)

def parse_info_column(info_str):
    info = {}
    for item in info_str.split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            info[k] = v
    return info.get("AF"), info.get("AC"), info.get("AN")

def process_chromosome(chrom):
    chrom_dir = GNOMAD_DIR / chrom
    chrom_dir.mkdir(exist_ok=True)
    
    vcf_path = chrom_dir / f"{chrom}.vcf.bgz"
    tbi_path = chrom_dir / f"{chrom}.vcf.bgz.tbi"
    out_path = OUT_DIR / f"gnomad_{chrom}.parquet"
    
    if out_path.exists():
        return f"{chrom} skipped"

    download_file(f"{BASE_VCF_URL}gnomad.exomes.v4.1.sites.{chrom}.vcf.bgz", vcf_path)
    download_file(f"{BASE_VCF_URL}gnomad.exomes.v4.1.sites.{chrom}.vcf.bgz.tbi", tbi_path)

    records = []

    with gzip.open(vcf_path, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue

            fields = line.strip().split("\t")
            chrom_val, pos, _, ref, alt, _, _, info = fields[:8]

            if len(ref) != 1 or len(alt) != 1:
                continue

            af, ac, an = parse_info_column(info)

            records.append((
                chrom_val.replace("chr", ""),
                pos,
                ref,
                alt,
                float(af) if af else 0.0,
                int(ac) if ac else 0,
                int(an) if an else 0
            ))

    df = pd.DataFrame(records, columns=[
        "chrom", "pos", "ref", "alt", "gnomad_af", "AC", "AN"
    ])

    df["variant_id"] = df["chrom"] + "_" + df["pos"] + "_" + df["ref"] + "_" + df["alt"]

    df.to_parquet(out_path, index=False)

    return f"{chrom} done"

if __name__ == "__main__":
    cores = int(os.cpu_count()) 
    print(f"🚀 Using {cores} cores")

    with mp.Pool(cores) as pool:
        results = list(tqdm(pool.imap(process_chromosome, CHROMS), total=len(CHROMS)))

    print(results)
    print("\n✅ All chromosomes processed")
