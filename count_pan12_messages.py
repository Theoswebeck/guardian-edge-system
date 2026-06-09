import os

base_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet\extracted\pan12-sexual-predator-identification-test-and-training"

train_diff_path = os.path.join(base_dir, "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-diff.txt")
test_diff_path = os.path.join(base_dir, "pan12-sexual-predator-identification-test-corpus-2012-05-21", "pan12-sexual-predator-identification-test-corpus-2012-05-21", "pan12-sexual-predator-identification-groundtruth-problem2.txt")

def count_lines(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    return 0

print("Train predatory messages (lines in diff):", count_lines(train_diff_path))
print("Test predatory messages (lines in gt2):", count_lines(test_diff_path))
