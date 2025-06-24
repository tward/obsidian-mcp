#!/usr/bin/env python
"""Simple test runner for Obsidian MCP server.

Run all tests:
    python tests/run_tests.py

This will run all filesystem-based integration tests.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path


def run_filesystem_tests():
    """Run filesystem integration tests."""
    print("\n" + "="*60)
    print("Running Filesystem Integration Tests")
    print("="*60)
    
    # Create a temporary vault for testing
    with tempfile.TemporaryDirectory(prefix="obsidian_test_") as temp_dir:
        # Set the vault path
        os.environ["OBSIDIAN_VAULT_PATH"] = temp_dir
        print(f"Using temporary vault: {temp_dir}\n")
        
        try:
            # Check if pytest is available
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--version"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("⚠️  pytest not installed")
                print("Install with: pip install pytest pytest-asyncio")
                return None
            
            # Run the filesystem integration tests
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/test_filesystem_integration.py", "-v", "--tb=short"],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
                
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error running tests: {e}")
            return False


def main():
    """Run the test suite."""
    # Ensure we're in the right directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("Obsidian MCP Server - Test Suite")
    print("================================")
    print("Filesystem-based implementation tests\n")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print(f"⚠️  Python {sys.version_info.major}.{sys.version_info.minor} detected")
        print("Python 3.10+ is recommended for best compatibility")
        print()
    
    # Run the filesystem tests
    result = run_filesystem_tests()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if result is None:
        print("⚠️  Tests skipped - missing dependencies")
        print("\nInstall test dependencies with:")
        print("  pip install pytest pytest-asyncio")
        return 1
    elif result:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())