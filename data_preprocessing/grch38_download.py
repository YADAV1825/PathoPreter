import os
import requests

target_dir = "grch38"
fna_url = "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.29_GRCh38.p14/GCA_000001405.29_GRCh38.p14_genomic.fna.gz"
report_url = "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.29_GRCh38.p14/GCA_000001405.29_GRCh38.p14_assembly_report.txt"

fna_path = os.path.join(target_dir, "GCA_000001405.29_GRCh38.p14_genomic.fna.gz")
report_path = os.path.join(target_dir, "GCA_000001405.29_GRCh38.p14_assembly_report.txt")

if not os.path.exists(target_dir):
    os.makedirs(target_dir)

def download_file(url, dest_path, is_large=False):
    if os.path.exists(dest_path):
        print(f"File already exists, skipping download: {dest_path}")
        return
        
    print(f"Starting download of: {dest_path}")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                downloaded = 0
                chunk_size = 1024 * 1024 * 10  # 10 MB chunks
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Print status update every 50 MB for large files
                        if is_large and downloaded % (1024 * 1024 * 50) < chunk_size:
                            print(f"Downloaded: {downloaded / (1024 * 1024):.0f} MB...")
                            
        print(f"Download complete! Saved as: {dest_path}\n")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Download both the FASTA sequence and the Assembly Report mapping
download_file(fna_url, fna_path, is_large=True)
download_file(report_url, report_path, is_large=False)

print("Make sure to extract the .gz file before running the merge script!")
