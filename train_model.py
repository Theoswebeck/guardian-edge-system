import pandas as pd
import numpy as np
import tensorflow as tf
import os
import json
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Conv1D, GlobalAveragePooling1D, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Configurations
VOCAB_SIZE = 15000
MAX_LEN = 50
EMBEDDING_DIM = 64
EPOCHS = 50
BATCH_SIZE = 64

dataset_path = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\unified_dataset.csv"

def main():
    print("Loading dataset...")
    df = pd.read_csv(dataset_path)
    
    # Fill any NaNs
    df['text'] = df['text'].fillna("")
    
    texts = df['text'].astype(str).tolist()
    labels = df['label'].tolist()
    
    # Fit Tokenizer
    print("Tokenizing texts...")
    tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
    tokenizer.fit_on_texts(texts)
    
    # Save vocabulary for mobile client
    word_index = tokenizer.word_index
    vocab_dict = {word: idx for word, idx in word_index.items() if idx < VOCAB_SIZE}
    
    vocab_path = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\vocabulary.json"
    with open(vocab_path, 'w', encoding='utf-8') as f:
        json.dump(vocab_dict, f, ensure_ascii=False, indent=2)
    print(f"Saved vocabulary to: {vocab_path}")

    # Convert texts to sequences and pad
    sequences = tokenizer.texts_to_sequences(texts)
    padded = pad_sequences(sequences, maxlen=MAX_LEN, padding='post', truncating='post')
    
    # Convert labels to numpy array
    labels = np.array(labels)
    
    # Train/Test split
    X_train, X_val, y_train, y_val = train_test_split(
        padded, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"Train size: {X_train.shape[0]}, Validation size: {X_val.shape[0]}")
    
    # Build Model (Conv1D + GlobalAveragePooling1D)
    print("Building lightweight CNN model...")
    model = Sequential([
        Embedding(input_dim=VOCAB_SIZE, output_dim=EMBEDDING_DIM, input_length=MAX_LEN),
        Conv1D(filters=128, kernel_size=5, padding='same', activation='relu'),
        GlobalAveragePooling1D(),
        Dropout(0.5),
        Dense(128, activation='relu'),
        Dropout(0.3),
        Dense(3, activation='softmax')
    ])
    
    model.compile(
        loss='sparse_categorical_crossentropy',
        optimizer='adam',
        metrics=['accuracy']
    )
    
    model.summary()
    
    # Train
    print("Training model with EarlyStopping...")
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=1e-5)
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        verbose=1,
        callbacks=[early_stop, reduce_lr]
    )
    
    # Save training history graphs immediately
    import matplotlib.pyplot as plt
    import os
    output_dir = r"C:\Users\RWB\.gemini\antigravity-ide\brain\066fe532-a5fe-4d81-bc64-4ea53543e99c\scratch"
    
    plt.figure(figsize=(10, 5))
    plt.plot(history.history['accuracy'], label='Train Accuracy', color='blue', marker='o')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy', color='orange', marker='o')
    plt.title('Model Accuracy (Train vs Validation)')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(loc='lower right')
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, 'training_accuracy.png'))
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(history.history['loss'], label='Train Loss', color='red', marker='o')
    plt.plot(history.history['val_loss'], label='Validation Loss', color='green', marker='o')
    plt.title('Model Loss (Train vs Validation)')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(loc='upper right')
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, 'training_loss.png'))
    plt.close()
    
    # Evaluate
    print("\nEvaluating model...")
    y_pred_probs = model.predict(X_val)
    y_pred = np.argmax(y_pred_probs, axis=1)
    
    target_names = ['Safe', 'Cyberbullying', 'Grooming']
    print("\n=== Classification Report ===")
    print(classification_report(y_val, y_pred, target_names=target_names))
    
    print("\n=== Confusion Matrix ===")
    print(confusion_matrix(y_val, y_pred))
    
    # Save Keras Model
    keras_model_path = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\threat_model.h5"
    model.save(keras_model_path)
    print(f"Saved Keras model to: {keras_model_path}")
    
    # Convert to TFLite
    print("\nConverting model to TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    # Since this architecture only uses Embedding, Conv1D, GlobalAveragePooling1D, and Dense,
    # it is fully compatible with standard builtins without needing SELECT_TF_OPS.
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS
    ]
    
    tflite_model = converter.convert()
    
    tflite_path = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\threat_model.tflite"
    with open(tflite_path, 'wb') as f:
        f.write(tflite_model)
    print(f"Saved TFLite model to: {tflite_path}")

if __name__ == "__main__":
    main()
