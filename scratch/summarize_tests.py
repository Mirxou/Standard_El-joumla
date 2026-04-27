import re
from pathlib import Path

def summarize_results():
    log_file = Path("scratch/test_results_detailed.log")
    if not log_file.exists():
        print("Log file not found.")
        return
    
    content = log_file.read_text(encoding="utf-8")
    
    clean_passes = re.findall(r"STATUS: CLEAN PASS: (.*)", content)
    internal_errors = re.findall(r"STATUS: PASSED WITH (\d+) INTERNAL ERRORS: (.*)", content)
    failures = re.findall(r"STATUS: FAILED: (.*)", content)
    timeouts = re.findall(r"TIMEOUT: (.*)", content)
    
    print(f"Summary of tests so far:")
    print(f"✅ Clean Passes: {len(clean_passes)}")
    print(f"⚠️ Passed with Internal Errors: {len(internal_errors)}")
    print(f"❌ Failures: {len(failures)}")
    print(f"🕒 Timeouts: {len(timeouts)}")
    
    if internal_errors:
        print("\nInternal Error Details:")
        for count, file in internal_errors:
            print(f"- {file}: {count} errors")
            
    if failures:
        print("\nFailures:")
        for file in failures:
            print(f"- {file}")

if __name__ == "__main__":
    summarize_results()
