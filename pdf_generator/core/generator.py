"""
PDF Generator Core

Main PDF generation functionality using Playwright.
"""

import os
import tempfile
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpRequest
from django.test import RequestFactory

from .utils import PDFOptions, validate_options, get_cache_key, get_cached_pdf, cache_pdf, sanitize_filename
from ..settings import BROWSER_ARGS, RETRY_ATTEMPTS

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. PDF generation will not work.")

class PlaywrightPDFGenerator:
    """Generate PDFs using Playwright browser automation"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
    
    def __enter__(self):
        """Context manager entry"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not installed")
        
        self.playwright = sync_playwright().start()
        # Launch browser in headless mode for PDF generation
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=BROWSER_ARGS
        )
        self.page = self.browser.new_page()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def generate_pdf_from_html(self, html_content: str, options: PDFOptions) -> bytes:
        """
        Generate PDF from HTML content.
        
        Args:
            html_content: HTML content to convert
            options: PDF generation options
            
        Returns:
            PDF content as bytes
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not available")
        
        # Create full HTML document with proper styling for PDF
        full_html = self._create_pdf_html_document(html_content, options)
        
        # Set content and generate PDF
        self.page.set_content(full_html)
        
        # Wait for any dynamic content to load
        if options.wait_for_network_idle:
            self.page.wait_for_load_state('networkidle')
        
        # Wait for specific selector if provided
        if options.wait_for_selector:
            self.page.wait_for_selector(options.wait_for_selector, timeout=options.timeout)
        
        # Generate PDF with proper settings
        pdf_bytes = self.page.pdf(**options.to_dict())
        
        return pdf_bytes
    
    def generate_pdf_from_url(self, url: str, options: PDFOptions) -> bytes:
        """
        Generate PDF from a URL.
        
        Args:
            url: URL to render and convert to PDF
            options: PDF generation options
            
        Returns:
            PDF content as bytes
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not available")
        
        # Navigate to the URL
        self.page.goto(url, wait_until='networkidle' if options.wait_for_network_idle else 'domcontentloaded')
        
        # Wait for specific selector if provided
        if options.wait_for_selector:
            self.page.wait_for_selector(options.wait_for_selector, timeout=options.timeout)
        
        # Generate PDF
        pdf_bytes = self.page.pdf(**options.to_dict())
        
        return pdf_bytes
    
    def _create_pdf_html_document(self, html_content: str, options: PDFOptions) -> str:
        """Create a complete HTML document optimized for PDF generation"""
        
        # Get custom CSS if provided
        custom_css = ""
        if options.css_file:
            css_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], options.css_file)
            if os.path.exists(css_path):
                with open(css_path, 'r') as f:
                    custom_css = f.read()
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Document</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* PDF-specific styles */
        @media print {{
            body {{
                margin: 0;
                padding: 0;
                font-size: 12pt;
                line-height: 1.4;
            }}
            
            .no-print {{
                display: none !important;
            }}
            
            * {{
                color: black !important;
                background: white !important;
            }}
        }}
        
        /* General styles for better PDF rendering */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 0;
            margin-bottom: 0.5em;
            font-weight: 600;
        }}
        
        p {{
            margin-bottom: 0.5em;
        }}
        
        ul, ol {{
            margin-bottom: 0.5em;
            padding-left: 1.5em;
        }}
        
        li {{
            margin-bottom: 0.25em;
        }}
        
        /* Custom CSS */
        {custom_css}
    </style>
</head>
<body class="bg-white">
    {html_content}
</body>
</html>
"""

class PDFGenerator:
    """Main PDF Generator class with static methods for easy use"""
    
    @staticmethod
    def generate_from_html(html_content: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Generate PDF from HTML content.
        
        Args:
            html_content: HTML content to convert
            options: PDF generation options
            
        Returns:
            PDF content as bytes
        """
        pdf_options = validate_options(options)
        
        with PlaywrightPDFGenerator() as pdf_gen:
            return pdf_gen.generate_pdf_from_html(html_content, pdf_options)
    
    @staticmethod
    def generate_from_template(template_name: str, context: Dict[str, Any], 
                             options: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Generate PDF from Django template.
        
        Args:
            template_name: Django template name
            context: Template context
            options: PDF generation options
            
        Returns:
            PDF content as bytes
        """
        pdf_options = validate_options(options)
        
        # Check cache first
        if pdf_options.enable_caching:
            cache_key = get_cache_key(template_name, context, pdf_options)
            cached_pdf = get_cached_pdf(cache_key)
            if cached_pdf:
                logger.info(f"Returning cached PDF for template: {template_name}")
                return cached_pdf
        
        # Render template
        html_content = render_to_string(template_name, context)
        
        # Generate PDF
        with PlaywrightPDFGenerator() as pdf_gen:
            pdf_bytes = pdf_gen.generate_pdf_from_html(html_content, pdf_options)
        
        # Cache the result
        if pdf_options.enable_caching:
            cache_key = get_cache_key(template_name, context, pdf_options)
            cache_pdf(cache_key, pdf_bytes)
        
        return pdf_bytes
    
    @staticmethod
    def generate_from_url(url: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Generate PDF from URL.
        
        Args:
            url: URL to render and convert to PDF
            options: PDF generation options
            
        Returns:
            PDF content as bytes
        """
        pdf_options = validate_options(options)
        
        with PlaywrightPDFGenerator() as pdf_gen:
            return pdf_gen.generate_pdf_from_url(url, pdf_options)
    
    @staticmethod
    def generate_from_view(view_name: str, request_data: Optional[Dict[str, Any]] = None,
                          options: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Generate PDF from Django view.
        
        Args:
            view_name: Django view name (e.g., 'myapp.views.my_view')
            request_data: Request data for the view
            options: PDF generation options
            
        Returns:
            PDF content as bytes
        """
        pdf_options = validate_options(options)
        
        # Import the view
        module_name, view_name = view_name.rsplit('.', 1)
        module = __import__(module_name, fromlist=[view_name])
        view_func = getattr(module, view_name)
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/')
        
        # Call the view
        response = view_func(request, **request_data or {})
        
        # Get the HTML content
        if hasattr(response, 'content'):
            html_content = response.content.decode('utf-8')
        else:
            html_content = str(response)
        
        # Generate PDF
        with PlaywrightPDFGenerator() as pdf_gen:
            return pdf_gen.generate_pdf_from_html(html_content, pdf_options)
    
    @staticmethod
    def generate_with_cache(cache_key: str, template_name: str, context: Dict[str, Any],
                           options: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Generate PDF with caching.
        
        Args:
            cache_key: Custom cache key
            template_name: Django template name
            context: Template context
            options: PDF generation options
            
        Returns:
            PDF content as bytes
        """
        pdf_options = validate_options(options)
        
        # Check cache first
        cached_pdf = get_cached_pdf(cache_key)
        if cached_pdf:
            logger.info(f"Returning cached PDF for key: {cache_key}")
            return cached_pdf
        
        # Generate PDF
        pdf_bytes = PDFGenerator.generate_from_template(template_name, context, options)
        
        # Cache the result
        cache_pdf(cache_key, pdf_bytes)
        
        return pdf_bytes
    
    @staticmethod
    def generate_batch(pdf_tasks: list) -> list:
        """
        Generate multiple PDFs in batch.
        
        Args:
            pdf_tasks: List of dictionaries with PDF generation tasks
                Each task should have: template, context, options, filename
            
        Returns:
            List of generated PDF bytes
        """
        results = []
        
        with PlaywrightPDFGenerator() as pdf_gen:
            for task in pdf_tasks:
                try:
                    template = task.get('template')
                    context = task.get('context', {})
                    options = validate_options(task.get('options', {}))
                    
                    # Render template
                    html_content = render_to_string(template, context)
                    
                    # Generate PDF
                    pdf_bytes = pdf_gen.generate_pdf_from_html(html_content, options)
                    
                    results.append({
                        'success': True,
                        'filename': task.get('filename', 'generated.pdf'),
                        'pdf_bytes': pdf_bytes,
                        'size': len(pdf_bytes)
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to generate PDF for task: {task}")
                    results.append({
                        'success': False,
                        'filename': task.get('filename', 'unknown.pdf'),
                        'error': str(e)
                    })
        
        return results
    
    @staticmethod
    def save_to_file(pdf_bytes: bytes, filename: str, directory: Optional[str] = None) -> str:
        """
        Save PDF bytes to a file.
        
        Args:
            pdf_bytes: PDF content as bytes
            filename: Filename to save as
            directory: Directory to save in (optional)
            
        Returns:
            Full path to saved file
        """
        # Sanitize filename
        filename = sanitize_filename(filename)
        
        # Determine save directory
        if directory:
            save_dir = Path(directory)
        else:
            save_dir = Path(tempfile.gettempdir()) / 'pdf_generator'
        
        # Create directory if it doesn't exist
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = save_dir / filename
        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)
        
        logger.info(f"PDF saved to: {file_path}")
        return str(file_path) 