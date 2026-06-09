import zipfile
import os

pan12_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet\extracted\pan12-sexual-predator-identification-test-and-training"

for filename in os.listdir(pan12_dir):
    if filename.endswith(".zip"):
        filepath = os.path.join(pan12_dir, filename)
        folder_name = filename.replace('.zip', '')
        extract_dir = os.path.join(pan12_dir, folder_name)
        if not os.path.exists(extract_dir):
            print(f"Extracting inner zip {filename}...")
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        else:
            print(f"Already extracted inner zip {filename}")
