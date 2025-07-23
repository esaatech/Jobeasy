#!/usr/bin/env python3
"""
Test Runner for Cover Letter Browser Simulation Tests
Provides a command-line interface to run different types of tests.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.coverletter.browsersimulation.test_cover_letter_simple import main as run_simple_test
from tests.coverletter.browsersimulation.test_cover_letter_frontend import main as run_frontend_test

def print_usage():
    """Print usage information."""
    print("""
🧪 Cover Letter Browser Simulation Test Runner

Usage:
    python run_tests.py [test_type]

Available test types:
    simple      - Run simple server and API tests (no browser)
    frontend    - Run full browser simulation tests with Playwright
    all         - Run all tests (default)

Examples:
    python run_tests.py simple
    python run_tests.py frontend
    python run_tests.py all
    python run_tests.py

Options:
    --help, -h  - Show this help message
    --headless  - Run browser tests in headless mode
    --screenshot - Take screenshots on errors (default: True)
""")

def main():
    """Main test runner function."""
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h']:
        print_usage()
        return
    
    test_type = sys.argv[1].lower()
    
    # Check for options
    headless = '--headless' in sys.argv
    screenshot = '--screenshot' in sys.argv
    
    if headless:
        print("🔧 Running in headless mode")
        # Update config for headless mode
        from tests.coverletter.browsersimulation.test_config import TEST_CONFIG
        TEST_CONFIG['headless'] = True
    
    if screenshot:
        print("📸 Screenshots enabled")
        from tests.coverletter.browsersimulation.test_config import TEST_CONFIG
        TEST_CONFIG['screenshot_on_error'] = True
    
    print("🧪 Cover Letter Browser Simulation Test Runner")
    print("="*60)
    
    if test_type == 'simple':
        print("📋 Running simple tests...")
        run_simple_test()
        
    elif test_type == 'frontend':
        print("🌐 Running frontend browser tests...")
        asyncio.run(run_frontend_test())
        
    elif test_type == 'all':
        print("🚀 Running all tests...")
        
        print("\n1️⃣ Running simple tests...")
        run_simple_test()
        
        print("\n2️⃣ Running frontend browser tests...")
        asyncio.run(run_frontend_test())
        
    else:
        print(f"❌ Unknown test type: {test_type}")
        print_usage()
        return
    
    print("\n✨ Test runner completed!")

if __name__ == "__main__":
    main() 