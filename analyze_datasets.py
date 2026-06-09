import zipfile
import os

data_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet"

for filename in os.listdir(data_dir):
    if filename.endswith(".zip"):
        filepath = os.path.join(data_dir, filename)
        print(f"--- Contents of {filename} ---")
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                for info in zip_ref.infolist():
                    print(f"  {info.filename} ({info.file_size} bytes)")
        except Exception as e:
            print(f"  Error reading {filename}: {e}")
        print()
