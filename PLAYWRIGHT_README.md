# Playwright Testing Setup

This project includes Playwright for end-to-end tests **and** for **server-side resume PDF generation** (`pdf_generator` uses headless Chromium). The Python package is installed via Poetry, but **browser binaries are a separate install** and must be present on each machine or container.

## Installation

```bash
# After `poetry install`, install Chromium (required for downloading resumes as PDF in the app)
poetry run playwright install chromium

# Optional: install all browsers (mostly for broader E2E runs)
poetry run playwright install
```

In Docker/production images, browsers are installed in the image build (see `Dockerfile`). Locally, if PDF download fails with `Executable doesn't exist` under `~/Library/Caches/ms-playwright/` (or similar), run the command above in the **same Poetry environment** the app uses.

## Quick Start

### 1. Run the Django Development Server

```bash
poetry run python manage.py runserver
```

### 2. Run Playwright Tests

#### Option A: Using Poetry Scripts
```bash
# Run tests in headless mode
poetry run test

# Run tests with browser visible
poetry run test-headed

# Run tests with UI (includes Django server management)
poetry run test-ui
```

#### Option B: Direct Playwright Commands
```bash
# Run all tests
poetry run playwright test

# Run tests in headed mode (see browser)
poetry run playwright test --headed

# Run tests only in Chromium
poetry run playwright test --project=chromium

# Run tests with UI mode
poetry run playwright test --ui
```

### 3. Run Example Script

```bash
# Make sure Django server is running first
poetry run python example_playwright.py
```

## Test Structure

- `tests/` - Contains all Playwright test files
- `tests/test_homepage.py` - Basic homepage tests
- `tests/test_resume_builder.py` - Resume builder functionality tests
- `playwright.config.py` - Playwright configuration
- `test_runner.py` - Simple test runner script
- `run_tests.py` - Test runner with Django server management
- `example_playwright.py` - Example automation script

## Writing Tests

### Basic Test Structure

```python
from playwright.sync_api import Page, expect

def test_example(page: Page):
    """Example test function"""
    page.goto("/")
    expect(page).to_have_title("JobEas")
    
    # Find and click elements
    button = page.locator("button:has-text('Click Me')")
    button.click()
    
    # Assert expectations
    expect(page.locator(".result")).to_contain_text("Success")
```

### Common Patterns

#### Form Filling
```python
# Fill text inputs
page.fill("input[name='username']", "testuser")
page.fill("input[name='password']", "password123")

# Select dropdown options
page.select_option("select[name='country']", "US")

# Check checkboxes
page.check("input[type='checkbox']")

# Click submit
page.click("button[type='submit']")
```

#### File Uploads
```python
# Upload a file
page.set_input_files("input[type='file']", "path/to/file.pdf")
```

#### Waiting for Elements
```python
# Wait for element to be visible
page.wait_for_selector(".loading", state="hidden")

# Wait for network requests to complete
page.wait_for_load_state("networkidle")
```

#### Screenshots
```python
# Take screenshot
page.screenshot(path="screenshot.png")

# Take full page screenshot
page.screenshot(path="fullpage.png", full_page=True)
```

## Configuration

The Playwright configuration is in `playwright.config.py`. Key settings:

- **Base URL**: `http://localhost:8000`
- **Browsers**: Chromium, Firefox, WebKit
- **Timeout**: 30 seconds
- **Screenshots**: Only on failure
- **Web Server**: Automatically starts Django server

## Useful Commands

### Generate Tests
```bash
# Generate tests from user actions
poetry run playwright codegen http://localhost:8000
```

### Install Browsers
```bash
# Reinstall browsers if needed
poetry run playwright install
```

### Show Test Report
```bash
# Show HTML report after tests
poetry run playwright show-report
```

### Debug Tests
```bash
# Run tests in debug mode
poetry run playwright test --debug
```

## Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Keep tests independent** - each test should be able to run alone
3. **Use page objects** for complex applications
4. **Take screenshots on failure** for debugging
5. **Test responsive design** with different viewport sizes
6. **Use data attributes** for reliable element selection

## Troubleshooting

### Common Issues

1. **Server not running**: Make sure Django server is running on port 8000
2. **Element not found**: Check if the element exists and is visible
3. **Timeout errors**: Increase timeout in configuration or add explicit waits
4. **Browser issues**: Reinstall browsers with `poetry run playwright install`

### Debug Mode

Run tests in debug mode to step through them:
```bash
poetry run playwright test --debug
```

This will open the browser in headed mode and pause execution, allowing you to inspect the page state. 