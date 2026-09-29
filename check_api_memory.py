import os
import time
import psutil


process = psutil.Process(os.getpid())


def memory_mb():
    return process.memory_info().rss / (1024 * 1024)


print("=" * 60)
print("PLEIONE FASTAPI MEMORY TEST")
print("=" * 60)

print("\nInitial memory:")
print(round(memory_mb(), 2), "MB")


print("\nImporting FastAPI application...")

start = time.perf_counter()

from api.main import app

end = time.perf_counter()

print("FastAPI application imported successfully.")

print("\nImport time:")
print(round(end - start, 2), "seconds")

print("\nMemory after importing FastAPI:")
print(round(memory_mb(), 2), "MB")


print("\n" + "=" * 60)
print("ROUTES")
print("=" * 60)

for route in app.routes:
    path = getattr(route, "path", None)
    methods = getattr(route, "methods", None)

    if path is None:
        print(f"{'':10} [included router]")
        continue

    if methods:
        print(f"{','.join(sorted(methods)):10} {path}")
    else:
        print(f"{'':10} {path}")


print("\n" + "=" * 60)
print("FINAL MEMORY")
print("=" * 60)

print(round(memory_mb(), 2), "MB")

print("\nKeeping process alive for 60 seconds...")
print("Check whether memory stays stable.")

time.sleep(60)

