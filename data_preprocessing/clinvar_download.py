import os
import urllib.request
import gzip
import shutil

# Define the target directory and file paths
clinvar_dir = "clinvar"
url = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz"
gz_path = os.path.join(clinvar_dir, "variant_summary.txt.gz")
txt_path = os.path.join(clinvar_dir, "variant_summary.txt")

# Create the clinvar directory if it does not already exist
if not os.path.exists(clinvar_dir):
    os.makedirs(clinvar_dir)

# Download the compressed file from the NCBI FTP server
if not os.path.exists(gz_path):
    print("Downloading ClinVar variant_summary.txt.gz. This may take a few minutes...")
    urllib.request.urlretrieve(url, gz_path)
    print("Download complete.")
else:
    print("Compressed file already exists. Skipping download.")

# Extract the .gz file into a standard text file
if not os.path.exists(txt_path):
    print("Extracting the compressed file...")
    with gzip.open(gz_path, 'rb') as f_in:
        with open(txt_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("Extraction complete. File saved to:", txt_path)
else:
    print("Extracted text file already exists. Ready for the next step.")
