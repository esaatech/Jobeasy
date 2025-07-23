# Cover Letter Browser Simulation Tests

This directory contains automated browser simulation tests for the cover letter generation functionality using Playwright.

## 📁 Directory Structure

```
tests/coverletter/browsersimulation/
├── __init__.py                    # Package initialization
├── README.md                      # This documentation
├── test_config.py                 # Test configuration and sample data
├── base_test.py                   # Base test class with common functionality
├── test_cover_letter_simple.py    # Simple server/API tests (no browser)
├── test_cover_letter_frontend.py  # Full browser simulation tests
└── run_tests.py                   # Test runner script
```

## 🚀 Quick Start

### Prerequisites

1. **Install Playwright** (if not already installed):
   ```bash
   poetry run playwright install
   ```

2. **Start the Django server**:
   ```bash
   poetry run python manage.py runserver 8009
   ```

### Running Tests

#### Option 1: Using the Test Runner (Recommended)

```bash
# Run all tests
cd tests/coverletter/browsersimulation
python run_tests.py all

# Run only simple tests (no browser)
python run_tests.py simple

# Run only frontend tests (with browser)
python run_tests.py frontend

# Run in headless mode
python run_tests.py frontend --headless

# Show help
python run_tests.py --help
```

#### Option 2: Running Individual Tests

```bash
# Simple tests
python test_cover_letter_simple.py

# Frontend tests
python test_cover_letter_frontend.py
```

## 🧪 Test Types

### 1. Simple Tests (`test_cover_letter_simple.py`)

**Purpose**: Quick server and API validation without browser automation.

**What it tests**:
- ✅ Server connectivity
- ✅ Page accessibility
- ✅ Backend API endpoints
- 📋 Provides manual testing steps
- 📝 Provides sample data for testing

**When to use**: 
- Quick validation that the server is running
- CI/CD pipeline integration
- No browser dependencies

### 2. Frontend Tests (`test_cover_letter_frontend.py`)

**Purpose**: Full browser simulation of user interactions.

**What it tests**:
- 🔐 Authentication handling
- 📋 Resume selection
- 📁 File upload functionality
- 💼 Job description input
- 🚀 Form submission
- 📄 Results display
- 🔘 Action buttons (Copy, Edit, Download, Email)
- ❌ Error handling

**When to use**:
- Complete end-to-end testing
- UI/UX validation
- Manual testing assistance

## ⚙️ Configuration

### Test Configuration (`test_config.py`)

```python
TEST_CONFIG = {
    'base_url': 'http://127.0.0.1:8009',
    'timeout': 30000,  # 30 seconds
    'headless': False,  # Set to True for headless mode
    'screenshot_on_error': True,
    'wait_timeout': 10000,  # 10 seconds for AI processing
}
```

### Element Selectors

The tests use multiple selectors to find page elements, making them more robust:

```python
SELECTORS = {
    'login': {
        'username': 'input[name="username"]',
        'password': 'input[name="password"]',
        'submit': 'button[type="submit"]'
    },
    'resume_selection': {
        'cards': '.resume-card',
        'selected': 'input[name="selected_resume"]:checked'
    },
    # ... more selectors
}
```

## 🔧 Customization

### Adding New Tests

1. **Create a new test class** extending `BaseBrowserTest`:
   ```python
   from .base_test import BaseBrowserTest
   
   class MyCustomTest(BaseBrowserTest):
       async def test_method(self):
           # Your test logic here
           pass
   ```

2. **Add to the test runner** in `run_tests.py`

### Modifying Selectors

Update the `SELECTORS` dictionary in `test_config.py` to match your page structure.

### Sample Data

Modify `SAMPLE_JOB_DESCRIPTION` and `SAMPLE_RESUME_TEXT` in `test_config.py` for different test scenarios.

## 📸 Screenshots and Debugging

Tests automatically take screenshots on errors when `screenshot_on_error` is enabled:

- `test_error.png` - General test errors
- `job_description_not_found.png` - When job description field is not found
- `submit_button_not_found.png` - When submit button is not found
- `no_results_found.png` - When results section is not visible

## 🔐 Authentication

The frontend tests handle authentication by:

1. **Detecting login requirement** - Checks for login form
2. **Waiting for manual login** - Pauses for user to login manually
3. **Auto-continuing** - Resumes automatically after successful login

## 🎯 Test Scenarios

### Scenario 1: User with Existing Resumes
1. User logs in
2. Selects an existing resume from the carousel
3. Enters job description
4. Submits form
5. Views generated cover letter
6. Tests action buttons

### Scenario 2: User without Resumes
1. User logs in
2. Uploads a resume file
3. Enters job description
4. Submits form
5. Views generated cover letter
6. Tests action buttons

### Scenario 3: Error Handling
1. Submit without resume selection/upload
2. Submit without job description
3. Verify appropriate error messages

## 🚨 Troubleshooting

### Common Issues

1. **"Server is not running"**
   - Start the Django server: `poetry run python manage.py runserver 8009`

2. **"Login required"**
   - Login manually when the browser opens
   - The test will continue automatically

3. **"Element not found"**
   - Check if the page structure has changed
   - Update selectors in `test_config.py`
   - Check screenshots for visual debugging

4. **"Playwright not installed"**
   - Install Playwright: `poetry run playwright install`

### Debug Mode

Run tests with additional debugging:

```bash
# Enable headless mode for faster execution
python run_tests.py frontend --headless

# Force screenshots
python run_tests.py frontend --screenshot
```

## 📊 Test Results

### Success Indicators

- ✅ Server is running
- ✅ Cover letter page is accessible
- ✅ Login successful
- ✅ Form elements found and interacted with
- ✅ Cover letter generated successfully
- ✅ Action buttons functional

### Failure Indicators

- ❌ Server not running
- ❌ Page not accessible (404, 403, etc.)
- ❌ Login failed
- ❌ Form elements not found
- ❌ Cover letter generation failed
- ❌ Action buttons not functional

## 🔄 Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Browser Tests
  run: |
    cd tests/coverletter/browsersimulation
    python run_tests.py frontend --headless
```

## 📚 Related Documentation

- [Playwright Documentation](https://playwright.dev/python/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Cover Letter Generation System](../README.md) 