"""
PDF Generator App Settings

This module contains default settings for the PDF Generator app.
These can be overridden in the main Django settings.py file.
"""

from django.conf import settings

# Default settings for PDF Generator
DEFAULT_PDF_GENERATOR_SETTINGS = {
    'DEFAULT_FORMAT': 'A4',
    'DEFAULT_ORIENTATION': 'portrait',
    'DEFAULT_MARGINS': {
        'top': '0.5in',
        'right': '0.5in',
        'bottom': '0.5in',
        'left': '0.5in'
    },
    'TEMPLATE_DIR': 'pdf_templates',
    'CSS_DIR': 'pdf_styles',
    'BROWSER_ARGS': [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--no-first-run',
        '--no-zygote',
        '--single-process'
    ],
    'TIMEOUT': 30000,
    'RETRY_ATTEMPTS': 3,
    'PRINT_BACKGROUND': True,
    'PREFER_CSS_PAGE_SIZE': True,
    'WAIT_FOR_NETWORK_IDLE': True,
    'ENABLE_CACHING': False,
    'CACHE_TIMEOUT': 3600,  # 1 hour
}

def get_pdf_generator_setting(key, default=None):
    """
    Get a PDF Generator setting from Django settings.
    Falls back to default if not found.
    """
    pdf_settings = getattr(settings, 'PDF_GENERATOR', {})
    return pdf_settings.get(key, DEFAULT_PDF_GENERATOR_SETTINGS.get(key, default))

# Export commonly used settings
PDF_FORMAT = get_pdf_generator_setting('DEFAULT_FORMAT')
PDF_ORIENTATION = get_pdf_generator_setting('DEFAULT_ORIENTATION')
PDF_MARGINS = get_pdf_generator_setting('DEFAULT_MARGINS')
BROWSER_ARGS = get_pdf_generator_setting('BROWSER_ARGS')
TIMEOUT = get_pdf_generator_setting('TIMEOUT')
RETRY_ATTEMPTS = get_pdf_generator_setting('RETRY_ATTEMPTS')
PRINT_BACKGROUND = get_pdf_generator_setting('PRINT_BACKGROUND')
PREFER_CSS_PAGE_SIZE = get_pdf_generator_setting('PREFER_CSS_PAGE_SIZE')
WAIT_FOR_NETWORK_IDLE = get_pdf_generator_setting('WAIT_FOR_NETWORK_IDLE')
ENABLE_CACHING = get_pdf_generator_setting('ENABLE_CACHING')
CACHE_TIMEOUT = get_pdf_generator_setting('CACHE_TIMEOUT') 