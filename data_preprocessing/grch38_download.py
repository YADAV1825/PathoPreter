<<<<<<< HEAD
import os
import requests

target_dir = "grch38"
url = "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.29_GRCh38.p14/GCA_000001405.29_GRCh38.p14_genomic.fna.gz"
gz_path = os.path.join(target_dir, "GRCh38_genomic.fna.gz")

if not os.path.exists(target_dir):
    os.makedirs(target_dir)

print("Starting download of the GRCh38 reference genome...")
print("This is a large file (~1GB), so it might take a few minutes.")

try:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(gz_path, 'wb') as f:
            downloaded = 0
            chunk_size = 1024 * 1024 * 10  # 10 MB chunks
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Print status update every 50 MB
                    if downloaded % (1024 * 1024 * 50) < chunk_size:
                        print(f"Downloaded: {downloaded / (1024 * 1024):.0f} MB...")
                        
    print(f"\nDownload complete! Saved as: {gz_path}")

except Exception as e:
=======
import os
import requests

target_dir = "grch38"
url = "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.29_GRCh38.p14/GCA_000001405.29_GRCh38.p14_genomic.fna.gz"
gz_path = os.path.join(target_dir, "GRCh38_genomic.fna.gz")

if not os.path.exists(target_dir):
    os.makedirs(target_dir)

print("Starting download of the GRCh38 reference genome...")
print("This is a large file (~1GB), so it might take a few minutes.")

try:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(gz_path, 'wb') as f:
            downloaded = 0
            chunk_size = 1024 * 1024 * 10  # 10 MB chunks
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Print status update every 50 MB
                    if downloaded % (1024 * 1024 * 50) < chunk_size:
                        print(f"Downloaded: {downloaded / (1024 * 1024):.0f} MB...")
                        
    print(f"\nDownload complete! Saved as: {gz_path}")

except Exception as e:
>>>>>>> 871859b092f2a08a39212afc4f30f3e718defcd6
    print(f"\nError downloading: {e}")