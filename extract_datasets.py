import zipfile
import os

data_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet"
extract_dir = os.path.join(data_dir, "extracted")

if not os.path.exists(extract_dir):
    os.makedirs(extract_dir)

for filename in os.listdir(data_dir):
    if filename.endswith(".zip"):
        filepath = os.path.join(data_dir, filename)
        # Create a subfolder for each zip to avoid file name collisions
        folder_name = filename.replace('.zip', '')
        specific_extract_dir = os.path.join(extract_dir, folder_name)
        if not os.path.exists(specific_extract_dir):
            os.makedirs(specific_extract_dir)
            print(f"Extracting {filename} into {folder_name}...")
            try:
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(specific_extract_dir)
            except Exception as e:
                print(f"Failed to extract {filename}: {e}")
        else:
            print(f"Skipping {filename}, already extracted.")

print("Extraction complete.")
