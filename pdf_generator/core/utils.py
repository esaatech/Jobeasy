"""
PDF Generator Utilities

Utility functions and classes for the PDF Generator app.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from django.conf import settings
from ..settings import (
    PDF_FORMAT, PDF_ORIENTATION, PDF_MARGINS, BROWSER_ARGS,
    TIMEOUT, RETRY_ATTEMPTS, PRINT_BACKGROUND, PREFER_CSS_PAGE_SIZE,
    WAIT_FOR_NETWORK_IDLE, ENABLE_CACHING, CACHE_TIMEOUT
)

logger = logging.getLogger(__name__)

@dataclass
class PDFOptions:
    """
    Configuration options for PDF generation.
    """
    format: str = field(default_factory=lambda: PDF_FORMAT)
    orientation: str = field(default_factory=lambda: PDF_ORIENTATION)
    margins: Dict[str, str] = field(default_factory=lambda: PDF_MARGINS.copy())
    print_background: bool = field(default_factory=lambda: PRINT_BACKGROUND)
    prefer_css_page_size: bool = field(default_factory=lambda: PREFER_CSS_PAGE_SIZE)
    timeout: int = field(default_factory=lambda: TIMEOUT)
    wait_for_network_idle: bool = field(default_factory=lambda: WAIT_FOR_NETWORK_IDLE)
    wait_for_selector: Optional[str] = None
    css_file: Optional[str] = None
    template: Optional[str] = None
    filename: Optional[str] = None
    enable_caching: bool = field(default_factory=lambda: ENABLE_CACHING)
    cache_timeout: int = field(default_factory=lambda: CACHE_TIMEOUT)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert options to dictionary for Playwright."""
        return {
            'format': self.format,
            'print_background': self.print_background,
            'margin': self.margins,
            'prefer_css_page_size': self.prefer_css_page_size,
        }
    
    def merge(self, other_options: Dict[str, Any]) -> 'PDFOptions':
        """Merge with other options, other options take precedence."""
        if not other_options:
            return self
        
        # Create a copy of current options
        merged = PDFOptions(
            format=other_options.get('format', self.format),
            orientation=other_options.get('orientation', self.orientation),
            margins=other_options.get('margins', self.margins.copy()),
            print_background=other_options.get('print_background', self.print_background),
            prefer_css_page_size=other_options.get('prefer_css_page_size', self.prefer_css_page_size),
            timeout=other_options.get('timeout', self.timeout),
            wait_for_network_idle=other_options.get('wait_for_network_idle', self.wait_for_network_idle),
            wait_for_selector=other_options.get('wait_for_selector', self.wait_for_selector),
            css_file=other_options.get('css_file', self.css_file),
            template=other_options.get('template', self.template),
            filename=other_options.get('filename', self.filename),
            enable_caching=other_options.get('enable_caching', self.enable_caching),
            cache_timeout=other_options.get('cache_timeout', self.cache_timeout),
        )
        
        return merged

def validate_options(options: Optional[Dict[str, Any]] = None) -> PDFOptions:
    """
    Validate and create PDFOptions from a dictionary.
    
    Args:
        options: Dictionary of options to validate
        
    Returns:
        PDFOptions instance with validated options
        
    Raises:
        ValueError: If options are invalid
    """
    if options is None:
        return PDFOptions()
    
    # Validate format
    valid_formats = ['A4', 'A3', 'A5', 'Letter', 'Legal', 'Tabloid']
    if 'format' in options and options['format'] not in valid_formats:
        raise ValueError(f"Invalid format: {options['format']}. Must be one of {valid_formats}")
    
    # Validate orientation
    valid_orientations = ['portrait', 'landscape']
    if 'orientation' in options and options['orientation'] not in valid_orientations:
        raise ValueError(f"Invalid orientation: {options['orientation']}. Must be one of {valid_orientations}")
    
    # Validate margins
    if 'margins' in options:
        margins = options['margins']
        if not isinstance(margins, dict):
            raise ValueError("Margins must be a dictionary")
        
        required_margin_keys = ['top', 'right', 'bottom', 'left']
        for key in required_margin_keys:
            if key not in margins:
                raise ValueError(f"Missing required margin key: {key}")
    
    # Validate timeout
    if 'timeout' in options:
        timeout = options['timeout']
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("Timeout must be a positive number")
    
    return PDFOptions().merge(options)

def get_cache_key(template: str, context: Dict[str, Any], options: PDFOptions) -> str:
    """
    Generate a cache key for PDF generation.
    
    Args:
        template: Template name
        context: Template context
        options: PDF options
        
    Returns:
        Cache key string
    """
    import hashlib
    import json
    
    # Create a hash of the template, context, and options
    cache_data = {
        'template': template,
        'context': context,
        'options': options.to_dict()
    }
    
    cache_string = json.dumps(cache_data, sort_keys=True)
    return f"pdf_generator:{hashlib.md5(cache_string.encode()).hexdigest()}"

def get_cached_pdf(cache_key: str) -> Optional[bytes]:
    """
    Get cached PDF if available.
    
    Args:
        cache_key: Cache key for the PDF
        
    Returns:
        PDF bytes if cached, None otherwise
    """
    if not ENABLE_CACHING:
        return None
    
    try:
        from django.core.cache import cache
        return cache.get(cache_key)
    except Exception as e:
        logger.warning(f"Failed to get cached PDF: {e}")
        return None

def cache_pdf(cache_key: str, pdf_bytes: bytes) -> bool:
    """
    Cache PDF bytes.
    
    Args:
        cache_key: Cache key for the PDF
        pdf_bytes: PDF bytes to cache
        
    Returns:
        True if cached successfully, False otherwise
    """
    if not ENABLE_CACHING:
        return False
    
    try:
        from django.core.cache import cache
        cache.set(cache_key, pdf_bytes, CACHE_TIMEOUT)
        return True
    except Exception as e:
        logger.warning(f"Failed to cache PDF: {e}")
        return False

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    import os
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Ensure it has a .pdf extension
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename 