import os
import time
import joblib
import psutil

process = psutil.Process(os.getpid())


def memory_mb():
    return process.memory_info().rss / (1024 * 1024)


print("Initial memory:", round(memory_mb(), 2), "MB")

models = {}

model_paths = [
    "models/module_A_0h_isolation_forest.joblib",
    "models/module_A_0h_peer_anomaly.joblib",
    "models/module_B_0h_24h_to_168h.joblib",
    "models/module_B_early_failure_classifier.joblib",
]

for path in model_paths:
    print("\nLoading:", path)

    before = memory_mb()

    models[path] = joblib.load(path)

    after = memory_mb()

    print("Memory before:", round(before, 2), "MB")
    print("Memory after :", round(after, 2), "MB")
    print("Increase     :", round(after - before, 2), "MB")


print("\n================================")
print("Final memory:", round(memory_mb(), 2), "MB")
print("================================")

print("\nKeeping models loaded for 60 seconds...")
time.sleep(60)