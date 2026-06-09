import pandas as pd
import os
import json

base_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet\extracted"
hate_path = os.path.join(base_dir, "archive", "hateXplain.csv")

if os.path.exists(hate_path):
    df = pd.read_csv(hate_path, nrows=5)
    for idx, row in df.iterrows():
        print(f"Row {idx}:")
        print("  repr(post_tokens):", repr(row['post_tokens']))
        print("  label:", row['label'])
else:
    print("Not found")
