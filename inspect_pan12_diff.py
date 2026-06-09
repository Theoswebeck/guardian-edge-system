import os

base_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet\extracted\pan12-sexual-predator-identification-test-and-training"
diff_file = os.path.join(base_dir, "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-diff.txt")

print("=== Diff File (first 10 lines) ===")
if os.path.exists(diff_file):
    with open(diff_file, "r") as f:
        for _ in range(10):
            print(f.readline().strip())
else:
    print("Diff file not found")
