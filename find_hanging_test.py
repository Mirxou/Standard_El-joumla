import os
import subprocess
import sys
import time

def main():
    root_dir = r"c:\Users\aboun\Desktop\Logical Version trae\tests\unit"
    results = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, start=r"c:\Users\aboun\Desktop\Logical Version trae")
                mod_path = rel_path.replace(os.sep, '.')[:-3]
                
                print(f"Checking {mod_path}...", end=" ", flush=True)
                start = time.time()
                try:
                    result = subprocess.run(
                        [sys.executable, "-c", f"import {mod_path}"],
                        timeout=30,  # Increased timeout
                        capture_output=True,
                        text=True
                    )
                    duration = time.time() - start
                    if result.returncode != 0:
                        print(f"FAILED ({duration:.2f}s): {result.stderr.strip()}")
                    else:
                        print(f"OK ({duration:.2f}s)")
                        results.append((mod_path, duration))
                except subprocess.TimeoutExpired:
                    print(f"!!! HANG DETECTED (>30s) !!!")
                    results.append((mod_path, 999))

    print("\nSlowest imports:")
    results.sort(key=lambda x: x[1], reverse=True)
    for mod, dur in results[:20]:
        print(f"{dur:.2f}s - {mod}")

if __name__ == "__main__":
    main()
