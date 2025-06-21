import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# Playwright configuration
def config():
    return {
        'testDir': './tests',
        'timeout': 30000,
        'expect': {
            'timeout': 5000
        },
        'fullyParallel': True,
        'forbidOnly': False,
        'retries': 0,
        'workers': 1,
        'reporter': 'html',
        'use': {
            'actionTimeout': 0,
            'baseURL': 'http://localhost:8000',
            'trace': 'on-first-retry',
            'screenshot': 'only-on-failure',
        },
        'projects': [
            {
                'name': 'chromium',
                'use': {
                    'browserName': 'chromium',
                },
            },
            {
                'name': 'firefox',
                'use': {
                    'browserName': 'firefox',
                },
            },
            {
                'name': 'webkit',
                'use': {
                    'browserName': 'webkit',
                },
            },
        ],
        'webServer': {
            'command': 'python manage.py runserver',
            'url': 'http://localhost:8000',
            'reuseExistingServer': not os.getenv('CI'),
            'timeout': 120 * 1000,
        },
    }

# Export the configuration
config = config() 