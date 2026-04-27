import subprocess
import os
import sys
import re
from pathlib import Path

def run_tests():
    unit_tests_dir = Path("tests/unit")
    test_files = sorted(list(unit_tests_dir.glob("test_*.py")))
    
    log_file = Path("scratch/test_results_detailed.log")
    with open(log_file, "w", encoding="utf-8") as log:
        for test_file in test_files:
            msg = f"--- Running {test_file} ---"
            print(msg)
            log.write(msg + "\n")
            
            try:
                result = subprocess.run(
                    ["pytest", str(test_file), "-v", "--tb=no"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                output = result.stdout + result.stderr
                log.write(output + "\n")
                
                # Check for hidden errors in logs
                errors_in_logs = re.findall(r"ERROR - (.*)", output)
                if errors_in_logs:
                    status = f"PASSED WITH {len(errors_in_logs)} INTERNAL ERRORS: {test_file}"
                elif result.returncode != 0:
                    status = f"FAILED: {test_file}"
                else:
                    status = f"CLEAN PASS: {test_file}"
                
                print(status)
                log.write(f"STATUS: {status}\n\n")
                log.flush()
                
            except subprocess.TimeoutExpired:
                print(f"TIMEOUT: {test_file}")
            except Exception as e:
                print(f"CRASH: {test_file} - {e}")

if __name__ == "__main__":
    run_tests()
