import pandas as pd
import os

base_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet\extracted"
cb_path = os.path.join(base_dir, "archive (1)", "cyberbullying-dataset.csv")

if os.path.exists(cb_path):
    df = pd.read_csv(cb_path)
    for label in sorted(df['TOXICITY'].unique()):
        print(f"=== Label {label} ===")
        sample = df[df['TOXICITY'] == label]['TEXT'].head(3).tolist()
        for i, s in enumerate(sample):
            print(f" {i+1}: {s[:150]}...")
else:
    print("Not found")
