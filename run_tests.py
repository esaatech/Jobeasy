#!/usr/bin/env python3
"""
Script to run Playwright tests with Django development server
"""
import subprocess
import time
import sys
import os
from pathlib import Path

def run_django_server():
    """Start Django development server"""
    print("Starting Django development server...")
    server_process = subprocess.Popen([
        sys.executable, "manage.py", "runserver", "8000"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    return server_process

def run_playwright_tests():
    """Run Playwright tests"""
    print("Running Playwright tests...")
    
    # Run the test script
    result = subprocess.run([
        sys.executable, "-m", "playwright", "test"
    ], capture_output=True, text=True)
    
    return result

def main():
    """Main function to orchestrate test execution"""
    server_process = None
    
    try:
        # Start Django server
        server_process = run_django_server()
        
        # Run Playwright tests
        test_result = run_playwright_tests()
        
        # Print test results
        print("Test Output:")
        print(test_result.stdout)
        
        if test_result.stderr:
            print("Test Errors:")
            print(test_result.stderr)
        
        # Return exit code
        sys.exit(test_result.returncode)
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)
    finally:
        # Clean up server process
        if server_process:
            print("Stopping Django server...")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    main() 