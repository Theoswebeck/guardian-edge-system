import pandas as pd
import numpy as np
import tensorflow as tf
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
from sklearn.preprocessing import label_binarize
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model

# Config
np.random.seed(42)
tf.random.set_seed(42)
VOCAB_SIZE = 15000
MAX_LEN = 50
dataset_path = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\unified_dataset.csv"
model_path = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\threat_model.h5"
output_dir = r"C:\Users\RWB\.gemini\antigravity-ide\brain\066fe532-a5fe-4d81-bc64-4ea53543e99c\scratch"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("Loading dataset...")
df = pd.read_csv(dataset_path)
df['text'] = df['text'].fillna("")

texts = df['text'].astype(str).tolist()
labels = df['label'].tolist()
target_names = ['Safe', 'Cyberbullying', 'Grooming']

# 1. Class Distribution Plot
print("Generating Class Distribution...")
plt.figure(figsize=(8, 6))
sns.countplot(x='label', data=df, palette='viridis')
plt.title('Dataset Class Distribution')
plt.xticks(ticks=[0, 1, 2], labels=target_names)
plt.xlabel('Threat Class')
plt.ylabel('Number of Messages')
plt.savefig(os.path.join(output_dir, 'class_distribution.png'))
plt.close()

# Tokenize and Split
print("Tokenizing texts...")
tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
padded = pad_sequences(sequences, maxlen=MAX_LEN, padding='post', truncating='post')
labels = np.array(labels)

X_train, X_val, y_train, y_val = train_test_split(
    padded, labels, test_size=0.2, random_state=42, stratify=labels
)

# Load Model
print("Loading model for evaluation...")
model = load_model(model_path)

# Predict
print("Predicting...")
y_pred_probs = model.predict(X_val)
y_pred = np.argmax(y_pred_probs, axis=1)

# 2. Confusion Matrix Plot
print("Generating Confusion Matrix...")
cm = confusion_matrix(y_val, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=target_names, yticklabels=target_names)
plt.title('Confusion Matrix on Validation Set')
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.savefig(os.path.join(output_dir, 'confusion_matrix.png'))
plt.close()

# 3. ROC Curve Plot
print("Generating ROC Curve...")
y_val_bin = label_binarize(y_val, classes=[0, 1, 2])
n_classes = y_val_bin.shape[1]

fpr = dict()
tpr = dict()
roc_auc = dict()

for i in range(n_classes):
    fpr[i], tpr[i], _ = roc_curve(y_val_bin[:, i], y_pred_probs[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])

colors = ['green', 'red', 'darkorange']
plt.figure(figsize=(8, 6))
for i, color in zip(range(n_classes), colors):
    plt.plot(fpr[i], tpr[i], color=color, lw=2,
             label=f'ROC curve of class {target_names[i]} (area = {roc_auc[i]:0.2f})')

plt.plot([0, 1], [0, 1], 'k--', lw=2)
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Multi-class Receiver Operating Characteristic (ROC)')
plt.legend(loc="lower right")
plt.savefig(os.path.join(output_dir, 'roc_curve.png'))
plt.close()

# Save classification report as markdown
report = classification_report(y_val, y_pred, target_names=target_names)
with open(os.path.join(output_dir, 'metrics.txt'), 'w') as f:
    f.write(report)

print("All graphs generated successfully!")
