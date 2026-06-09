import sys
import os
import json
import numpy as np
import tensorflow as tf

# Suppress tensorflow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

VOCAB_SIZE = 15000
MAX_LEN = 50

# Load vocabulary
vocab_path = os.path.join(os.path.dirname(__file__), "vocabulary.json")
if not os.path.exists(vocab_path):
    print(json.dumps({"error": "vocabulary.json not found"}))
    sys.exit(1)

with open(vocab_path, "r", encoding="utf-8") as f:
    vocab = json.load(f)

# Load TFLite model
tflite_path = os.path.join(os.path.dirname(__file__), "threat_model.tflite")
if not os.path.exists(tflite_path):
    print(json.dumps({"error": "threat_model.tflite not found"}))
    sys.exit(1)

try:
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
except Exception as e:
    print(json.dumps({"error": f"Failed to load TFLite model: {e}"}))
    sys.exit(1)

# Get input and output tensors
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def preprocess_text(text):
    # Match Keras Tokenizer filters
    filters = '!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n'
    text = text.lower()
    translate_dict = dict((c, " ") for c in filters)
    translate_map = str.maketrans(translate_dict)
    text = text.translate(translate_map)
    words = text.split()
    
    # Map words to indices
    seq = []
    for word in words:
        # Check OOV (1 is standard index for OOV in Keras Tokenizer)
        idx = vocab.get(word, 1)
        seq.append(idx)
        
    # Pad or truncate to MAX_LEN
    if len(seq) < MAX_LEN:
        seq = seq + [0] * (MAX_LEN - len(seq))
    else:
        seq = seq[:MAX_LEN]
        
    return np.array([seq], dtype=np.float32)

from deep_translator import GoogleTranslator

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No input text provided"}))
        sys.exit(1)
        
    original_text = sys.argv[1]
    
    try:
        translated_text = GoogleTranslator(source='auto', target='en').translate(original_text)
        if not translated_text:
            translated_text = original_text
    except Exception:
        translated_text = original_text
        
    # Preprocess
    input_data = preprocess_text(translated_text)
    
    # Run inference
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    
    # Get prediction
    output_data = interpreter.get_tensor(output_details[0]['index'])[0]
    
    # Find argmax and confidence
    label = int(np.argmax(output_data))
    confidence = float(output_data[label])
    
    classes = ["Safe", "Cyberbullying", "Grooming"]
    result = {
        "text": original_text,
        "translated_text": translated_text,
        "label": label,
        "confidence": confidence,
        "class": classes[label]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
