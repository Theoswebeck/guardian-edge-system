import os

base_dir = r"e:\Java Project\UK Project\2026\Benson\AI-DRIVEN CHILD ONLINE PROTECTION SYSTEM\DataSet\extracted\pan12-sexual-predator-identification-test-and-training"

train_pred_file = os.path.join(base_dir, "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-training-corpus-2012-05-01", "pan12-sexual-predator-identification-training-corpus-predators-2012-05-01.txt")
test_gt1_file = os.path.join(base_dir, "pan12-sexual-predator-identification-test-corpus-2012-05-21", "pan12-sexual-predator-identification-test-corpus-2012-05-21", "pan12-sexual-predator-identification-groundtruth-problem1.txt")
test_gt2_file = os.path.join(base_dir, "pan12-sexual-predator-identification-test-corpus-2012-05-21", "pan12-sexual-predator-identification-test-corpus-2012-05-21", "pan12-sexual-predator-identification-groundtruth-problem2.txt")

print("=== Train Predators (first 5 lines) ===")
if os.path.exists(train_pred_file):
    with open(train_pred_file, "r") as f:
        for _ in range(5):
            print(f.readline().strip())
else:
    print("Train predator file not found at", train_pred_file)

print("\n=== Test GT 1 (first 5 lines) ===")
if os.path.exists(test_gt1_file):
    with open(test_gt1_file, "r") as f:
        for _ in range(5):
            print(f.readline().strip())
else:
    print("Test GT 1 file not found")

print("\n=== Test GT 2 (first 5 lines) ===")
if os.path.exists(test_gt2_file):
    with open(test_gt2_file, "r") as f:
        for _ in range(5):
            print(f.readline().strip())
else:
    print("Test GT 2 file not found")
