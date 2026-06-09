import pandas as pd
import os

base_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet\extracted"

# 1. Cyberbullying dataset
cb_path = os.path.join(base_dir, "archive (1)", "cyberbullying-dataset.csv")
if os.path.exists(cb_path):
    df_cb = pd.read_csv(cb_path)
    print("=== Cyberbullying Dataset ===")
    print("Shape:", df_cb.shape)
    print(df_cb['TOXICITY'].value_counts())
else:
    print("Cyberbullying not found")

# 2. Aggression dataset
agg_path = os.path.join(base_dir, "aggression_parsed_dataset.csv", "aggression_parsed_dataset.csv")
if os.path.exists(agg_path):
    df_agg = pd.read_csv(agg_path)
    print("\n=== Aggression Dataset ===")
    print("Shape:", df_agg.shape)
    print("oh_label value counts:\n", df_agg['oh_label'].value_counts())
else:
    print("Aggression not found")

# 3. HateXplain dataset
hate_path = os.path.join(base_dir, "archive", "hateXplain.csv")
if os.path.exists(hate_path):
    df_hate = pd.read_csv(hate_path)
    print("\n=== HateXplain Dataset ===")
    print("Shape:", df_hate.shape)
    print("Columns:", df_hate.columns.tolist())
    print("Label value counts:\n", df_hate['label'].value_counts() if 'label' in df_hate.columns else "No label col")
else:
    print("HateXplain not found")
