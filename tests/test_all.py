#!/usr/bin/env python3
"""Run all tests for Obsidian MCP server."""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run all test files."""
    test_dir = Path(__file__).parent
    
    print("Running Obsidian MCP Tests")
    print("=" * 50)
    print()
    
    # Find all test files
    test_files = list(test_dir.glob("test_*.py"))
    test_files = [f for f in test_files if f.name != "test_all.py"]
    
    if not test_files:
        print("No test files found!")
        return 1
    
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    print()
    
    # Run pytest on all test files
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"] + [str(f) for f in test_files]
    
    print("Running tests with pytest...")
    print("-" * 50)
    
    result = subprocess.run(cmd, cwd=test_dir.parent)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())