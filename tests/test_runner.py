#!/usr/bin/env python3
import sys
import subprocess
import os

def run_tests():
    print("Initializing offline E2E Test Suite...")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, project_root)
    
    # Enforce mock environment variable
    os.environ["YOUTUBE_FRAME_EXTRACTOR_MOCK"] = "1"
    
    # Target specific test file: tests/test_e2e.py
    cmd = [sys.executable, "-m", "pytest", "tests/test_e2e.py", "-v"]
    
    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)

if __name__ == "__main__":
    run_tests()
