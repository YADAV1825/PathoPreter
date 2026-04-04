import requests
import os

url = 'https://usf.box.com/shared/static/ohjs9p90r0fgt3u3pwt10o6m249i0j12'
output_filename = 'dbNSFP4.9a.zip'

print(f"🚀 Starting download of {output_filename}...")
print("This file is large (10GB+), so please wait.")

try:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(output_filename, 'wb') as f:
            downloaded = 0
            chunk_size = 1024 * 1024 * 10  # 10 MB chunks
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if downloaded % (1024 * 1024 * 1024) < chunk_size:
                        print(f"Downloaded: {downloaded / (1024*1024*1024):.2f} GB...")
                        
    print(f"\n✅ Download Complete! Saved as: {output_filename}")
    print(f"File size: {os.path.getsize(output_filename) / (1024*1024*1024):.2f} GB")

except Exception as e:
    print(f"\n Error downloading: {e}")

print("Extracting files...")
os.system("unzip dbNSFP4.9a.zip -d dbnsfp_data")
print("Extraction finished.")
