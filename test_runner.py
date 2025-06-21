#!/usr/bin/env python3
"""
Simple test runner for Playwright tests
"""
import subprocess
import sys
import os

def main():
    """Run Playwright tests"""
    try:
        # Run Playwright tests using the built-in test runner
        result = subprocess.run([
            sys.executable, "-m", "playwright", "test",
            "--headed",  # Run in headed mode to see the browser
            "--project=chromium"  # Only run in Chromium for faster testing
        ], capture_output=False)  # Don't capture output to see real-time results
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 