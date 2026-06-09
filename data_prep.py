import os
import xml.etree.ElementTree as ET
import random
import pandas as pd
import numpy as np
import html
import re

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

base_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet\extracted"

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = html.unescape(text)
    text = re.sub(r"\r", "", text)
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def parse_pan12_corpus(xml_path, gt_messages_path, max_safe_samples=25000):
    print(f"Parsing PAN12 file: {xml_path}")
    predatory_msgs = set()
    if os.path.exists(gt_messages_path):
        with open(gt_messages_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    conv_id = parts[0]
                    try:
                        line_num = int(parts[1])
                        predatory_msgs.add((conv_id, line_num))
                    except ValueError:
                        pass
    print(f"Loaded {len(predatory_msgs)} predatory message references.")

    grooming_texts = []
    safe_texts = []
    safe_count = 0
    
    context = ET.iterparse(xml_path, events=('start', 'end'))
    context = iter(context)
    event, root = next(context)
    current_conv_id = None
    
    for event, elem in context:
        if event == 'start' and elem.tag == 'conversation':
            current_conv_id = elem.get('id')
        elif event == 'end' and elem.tag == 'message':
            line_num_str = elem.get('line')
            if line_num_str is not None:
                try:
                    line_num = int(line_num_str)
                except ValueError:
                    line_num = -1
                
                text_elem = elem.find('text')
                text = text_elem.text if text_elem is not None else ""
                
                if text and text.strip():
                    text = clean_text(text)
                    if text:
                        is_predatory = (current_conv_id, line_num) in predatory_msgs
                        if is_predatory:
                            grooming_texts.append(text)
                        else:
                            safe_count += 1
                            if len(safe_texts) < max_safe_samples:
                                safe_texts.append(text)
                            else:
                                r = random.randint(0, safe_count - 1)
                                if r < max_safe_samples:
                                    safe_texts[r] = text
            elem.clear()
        elif event == 'end' and elem.tag == 'conversation':
            root.clear()
            
    print(f"Finished parsing. Grooming: {len(grooming_texts)}, Sampled Safe: {len(safe_texts)}")
    return grooming_texts, safe_texts

def main():
    print("--- STEP 1: PARSING PAN12 DATASET ---")
    pan12_base = os.path.join(base_dir, "pan12-sexual-predator-identification-test-and-training")
    
    # Train
    train_xml = os.path.join(pan12_base, "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-training-corpus-2012-05-01.xml")
    train_diff = os.path.join(pan12_base, "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-diff.txt")
    grooming_train, safe_train = parse_pan12_corpus(train_xml, train_diff, max_safe_samples=15000)
    
    # Test
    test_xml = os.path.join(pan12_base, "pan12-sexual-predator-identification-test-corpus-2012-05-21", "pan12-sexual-predator-identification-test-corpus-2012-05-21", "pan12-sexual-predator-identification-test-corpus-2012-05-17.xml")
    test_gt2 = os.path.join(pan12_base, "pan12-sexual-predator-identification-test-corpus-2012-05-21", "pan12-sexual-predator-identification-test-corpus-2012-05-21", "pan12-sexual-predator-identification-groundtruth-problem2.txt")
    grooming_test, safe_test = parse_pan12_corpus(test_xml, test_gt2, max_safe_samples=10000)
    
    all_grooming = grooming_train + grooming_test
    all_pan_safe = safe_train + safe_test
    print(f"Total PAN12 Grooming (Class 2): {len(all_grooming)}")
    print(f"Total PAN12 Safe: {len(all_pan_safe)}")

    print("\n--- STEP 2: PROCESSING CYBERBULLYING DATASET ---")
    cb_path = os.path.join(base_dir, "archive (1)", "cyberbullying-dataset.csv")
    cb_cyber = []
    cb_safe = []
    if os.path.exists(cb_path):
        df_cb = pd.read_csv(cb_path)
        df_cb['cleaned'] = df_cb['TEXT'].apply(clean_text)
        df_cb = df_cb[df_cb['cleaned'] != ""]
        
        # Labels >= 1 are cyberbullying
        df_cb_cyber = df_cb[df_cb['TOXICITY'] >= 1]
        df_cb_safe = df_cb[df_cb['TOXICITY'] == 0]
        
        cb_cyber = df_cb_cyber['cleaned'].tolist()
        cb_safe = df_cb_safe['cleaned'].tolist()
        print(f"Cyberbullying dataset - Cyberbullying: {len(cb_cyber)}, Safe: {len(cb_safe)}")

    print("\n--- STEP 3: PROCESSING AGGRESSION DATASET ---")
    agg_path = os.path.join(base_dir, "aggression_parsed_dataset.csv", "aggression_parsed_dataset.csv")
    agg_cyber = []
    agg_safe = []
    if os.path.exists(agg_path):
        df_agg = pd.read_csv(agg_path)
        df_agg['cleaned'] = df_agg['Text'].apply(clean_text)
        df_agg = df_agg[df_agg['cleaned'] != ""]
        
        # oh_label == 1 is aggression (cyberbullying)
        df_agg_cyber = df_agg[df_agg['oh_label'] == 1]
        df_agg_safe = df_agg[df_agg['oh_label'] == 0]
        
        agg_cyber = df_agg_cyber['cleaned'].tolist()
        agg_safe = df_agg_safe['cleaned'].tolist()
        print(f"Aggression dataset - Cyberbullying: {len(agg_cyber)}, Safe: {len(agg_safe)}")

    print("\n--- STEP 4: PROCESSING HATEXPLAIN DATASET ---")
    hate_path = os.path.join(base_dir, "archive", "hateXplain.csv")
    hate_cyber = []
    hate_safe = []
    if os.path.exists(hate_path):
        df_hate = pd.read_csv(hate_path)
        # Group by post_id and compute majority label
        grouped = df_hate.groupby('post_id').agg({
            'post_tokens': 'first',
            'label': lambda x: x.mode().iloc[0] if not x.mode().empty else 'normal'
        }).reset_index()
        
        grouped['cleaned'] = grouped['post_tokens'].apply(clean_text)
        grouped = grouped[grouped['cleaned'] != ""]
        
        df_hate_cyber = grouped[grouped['label'].isin(['hatespeech', 'offensive'])]
        df_hate_safe = grouped[grouped['label'] == 'normal']
        
        hate_cyber = df_hate_cyber['cleaned'].tolist()
        hate_safe = df_hate_safe['cleaned'].tolist()
        print(f"HateXplain dataset - Cyberbullying: {len(hate_cyber)}, Safe: {len(hate_safe)}")

    print("\n--- STEP 5: MERGING AND BALANCING DATA ---")
    # Target counts per class to achieve balanced dataset
    # We have around 23,425 Grooming samples (Class 2)
    # We will sample 23,000 for Class 1 (Cyberbullying) and 23,000 for Class 0 (Safe)
    
    # Class 2: Grooming
    class2_texts = all_grooming
    class2_labels = [2] * len(class2_texts)
    
    # Class 1: Cyberbullying (combine from cb, agg, hateXplain)
    combined_cyber = cb_cyber + agg_cyber + hate_cyber
    combined_cyber = list(set(combined_cyber)) # Remove duplicate strings
    print(f"Unique combined cyberbullying messages: {len(combined_cyber)}")
    
    # Sample 23,000
    if len(combined_cyber) > 23000:
        class1_texts = random.sample(combined_cyber, 23000)
    else:
        class1_texts = combined_cyber
    class1_labels = [1] * len(class1_texts)
    
    # Class 0: Safe (combine PAN12 sampled safe, cb_safe, agg_safe, hate_safe)
    # Let's pool them all
    combined_safe = all_pan_safe + cb_safe + agg_safe + hate_safe
    combined_safe = list(set(combined_safe)) # Remove duplicate strings
    print(f"Unique combined safe messages: {len(combined_safe)}")
    
    # Sample 23,000
    if len(combined_safe) > 23000:
        class0_texts = random.sample(combined_safe, 23000)
    else:
        class0_texts = combined_safe
    class0_labels = [0] * len(class0_texts)
    
    # Unify
    final_texts = class0_texts + class1_texts + class2_texts
    final_labels = class0_labels + class1_labels + class2_labels
    
    df_unified = pd.DataFrame({
        'text': final_texts,
        'label': final_labels
    })
    
    # Shuffle
    df_unified = df_unified.sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    print("\n--- FINAL DATASET DISTRIBUTION ---")
    print(df_unified['label'].value_counts())
    
    out_path = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\unified_dataset.csv"
    df_unified.to_csv(out_path, index=False, encoding='utf-8')
    print(f"Saved unified dataset ({len(df_unified)} rows) to: {out_path}")

if __name__ == "__main__":
    main()
