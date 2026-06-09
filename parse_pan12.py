import os
import xml.etree.ElementTree as ET
import random

def parse_pan12_corpus(xml_path, gt_messages_path, max_safe_samples=30000):
    print(f"Parsing PAN12 file: {xml_path}")
    print(f"Using ground truth file: {gt_messages_path}")
    
    # Load predatory messages into a set of (conversation_id, line_number)
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
    
    # For reservoir sampling of safe messages
    safe_count = 0
    
    # We use iterparse to save memory
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
                    text = text.strip()
                    is_predatory = (current_conv_id, line_num) in predatory_msgs
                    
                    if is_predatory:
                        grooming_texts.append(text)
                    else:
                        safe_count += 1
                        # Reservoir sampling
                        if len(safe_texts) < max_safe_samples:
                            safe_texts.append(text)
                        else:
                            r = random.randint(0, safe_count - 1)
                            if r < max_safe_samples:
                                safe_texts[r] = text
                                
            # Clear element to free memory
            elem.clear()
            
        elif event == 'end' and elem.tag == 'conversation':
            root.clear() # Clear conversation from root to free memory
            
    print(f"Finished parsing. Found {len(grooming_texts)} grooming messages and sampled {len(safe_texts)} safe messages out of {safe_count} total safe messages.")
    return grooming_texts, safe_texts

if __name__ == "__main__":
    base_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet\extracted\pan12-sexual-predator-identification-test-and-training"
    train_xml = os.path.join(base_dir, "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-training-corpus-2012-05-01.xml")
    train_diff = os.path.join(base_dir, "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-diff.txt")
    
    grooming_train, safe_train = parse_pan12_corpus(train_xml, train_diff, max_safe_samples=1000)
    print("Sample Grooming:", grooming_train[:3])
    print("Sample Safe:", safe_train[:3])
