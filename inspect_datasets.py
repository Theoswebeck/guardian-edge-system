import pandas as pd
import os
import xml.etree.ElementTree as ET

base_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet\extracted"

# 1. Cyberbullying dataset
cb_path = os.path.join(base_dir, "archive (1)", "cyberbullying-dataset.csv")
print("=== Cyberbullying Dataset ===")
if os.path.exists(cb_path):
    try:
        df_cb = pd.read_csv(cb_path, nrows=5)
        print("Columns:", df_cb.columns.tolist())
        print(df_cb.head(2))
    except Exception as e:
        print("Error:", e)
else:
    print("Not found")

# 2. Aggression parsed dataset
agg_path = os.path.join(base_dir, "aggression_parsed_dataset.csv", "aggression_parsed_dataset.csv")
print("\n=== Aggression Parsed Dataset ===")
if os.path.exists(agg_path):
    try:
        df_agg = pd.read_csv(agg_path, nrows=5)
        print("Columns:", df_agg.columns.tolist())
        print(df_agg.head(2))
    except Exception as e:
        print("Error:", e)
else:
    print("Not found")

# 3. HateXplain dataset
hate_path = os.path.join(base_dir, "archive", "hateXplain.csv")
print("\n=== HateXplain Dataset ===")
if os.path.exists(hate_path):
    try:
        df_hate = pd.read_csv(hate_path, nrows=5)
        print("Columns:", df_hate.columns.tolist())
        print(df_hate.head(2))
    except Exception as e:
        print("Error:", e)
else:
    print("Not found")

# 4. PAN12 Sexual Predator Dataset (Training xml structure)
pan_xml_path = os.path.join(
    base_dir, 
    "pan12-sexual-predator-identification-test-and-training",
    "pan12-sexual-predator-identification-training-corpus-2012-05-01",
    "pan12-sexual-predator-identification-training-corpus-2012-05-01",
    "pan12-sexual-predator-identification-training-corpus-2012-05-01.xml"
)
print("\n=== PAN12 XML Structure ===")
if os.path.exists(pan_xml_path):
    try:
        # Read first 5000 bytes
        with open(pan_xml_path, 'r', encoding='utf-8') as f:
            print(f.read(1500))
    except Exception as e:
        print("Error:", e)
else:
    print("Not found")
