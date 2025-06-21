# Django PDF Generator App

A standalone, reusable Django app for generating high-quality PDFs using Playwright. This app renders web pages exactly as they appear in a browser and converts them to PDFs, preserving all CSS styling, layouts, and visual elements.

## 🎯 **Core Concept**

Create a Django app called `pdf_generator` that can be:
1. **Copied** to any Django project
2. **Installed** as a dependency
3. **Called** from any other app to generate PDFs
4. **Configured** for different use cases

## 📁 **App Structure**

```
pdf_generator/
├── __init__.py
├── apps.py
├── settings.py          # App-specific settings
├── core/
│   ├── __init__.py
│   ├── generator.py     # Main PDF generation logic
│   ├── templates.py     # Template management
│   └── utils.py         # Utility functions
├── templates/
│   └── pdf_generator/
│       ├── base.html    # Base template for PDFs
│       └── default.html # Default PDF template
├── management/
│   └── commands/
│       └── generate_pdf.py
├── static/
│   └── pdf_generator/
│       └── css/
│           └── pdf-styles.css
└── views.py             # Optional web interface
```

## 🚀 **Key Features**

### 1. **Flexible Input Methods**
```python
# Method 1: From HTML content
pdf_bytes = PDFGenerator.generate_from_html(html_content, options)

# Method 2: From Django template
pdf_bytes = PDFGenerator.generate_from_template('my_template.html', context, options)

# Method 3: From URL
pdf_bytes = PDFGenerator.generate_from_url('http://example.com/page', options)

# Method 4: From Django view
pdf_bytes = PDFGenerator.generate_from_view('myapp.views.my_view', request_data, options)
```

### 2. **Configurable Options**
```python
options = {
    'format': 'A4',                    # Page format
    'orientation': 'portrait',         # Page orientation
    'margins': {                       # Custom margins
        'top': '0.5in',
        'right': '0.5in',
        'bottom': '0.5in',
        'left': '0.5in'
    },
    'css_file': 'custom-styles.css',   # Custom CSS file
    'template': 'professional',        # Template to use
    'wait_for': '.content-loaded',     # Wait for element
    'timeout': 5000,                   # Timeout in ms
    'print_background': True,          # Include backgrounds
    'prefer_css_page_size': True,      # Use CSS page size
}
```

### 3. **Template System**
```python
# Base template that other apps can extend
{% extends "pdf_generator/base.html" %}

{% block pdf_content %}
    <!-- Your content here -->
{% endblock %}

{% block pdf_styles %}
    <!-- Custom styles for this PDF -->
{% endblock %}
```

### 4. **Settings Configuration**
```python
# settings.py
PDF_GENERATOR = {
    'DEFAULT_FORMAT': 'A4',
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
    ],
    'TIMEOUT': 30000,
    'RETRY_ATTEMPTS': 3,
}
```

## 💻 **Usage Examples**

### **In Resume Builder App**
```python
from pdf_generator.core.generator import PDFGenerator

def download_resume_pdf(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    context = {
        'resume_data': resume.get_data(),
        'template_id': resume.template_id
    }
    
    pdf_bytes = PDFGenerator.generate_from_template(
        'resume_templates/professional.html',
        context,
        options={
            'filename': f'resume_{resume_id}.pdf',
            'format': 'A4',
            'print_background': True
        }
    )
    
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="resume_{resume_id}.pdf"'
    return response
```

### **In Blog App**
```python
from pdf_generator.core.generator import PDFGenerator

def download_article_pdf(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    
    context = {
        'article': article,
        'user': request.user
    }
    
    pdf_bytes = PDFGenerator.generate_from_template(
        'blog/pdf_template.html',
        context,
        options={
            'format': 'A4',
            'orientation': 'portrait',
            'css_file': 'blog-pdf-styles.css'
        }
    )
    
    return HttpResponse(pdf_bytes, content_type='application/pdf')
```

### **In E-commerce App**
```python
from pdf_generator.core.generator import PDFGenerator

def download_invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
        'items': order.items.all(),
        'company_info': get_company_info()
    }
    
    pdf_bytes = PDFGenerator.generate_from_template(
        'shop/invoice_template.html',
        context,
        options={
            'format': 'Letter',
            'orientation': 'portrait',
            'margins': {'top': '0.25in', 'right': '0.25in', 'bottom': '0.25in', 'left': '0.25in'}
        }
    )
    
    return HttpResponse(pdf_bytes, content_type='application/pdf')
```

## 🔧 **Advanced Features**

### 1. **Async Support**
```python
# For long-running PDF generation
pdf_bytes = await PDFGenerator.generate_async_from_template(template, context, options)
```

### 2. **Caching**
```python
# Cache generated PDFs
pdf_bytes = PDFGenerator.generate_with_cache(
    cache_key=f'resume_{resume_id}',
    template='resume_template.html',
    context=context,
    options=options
)
```

### 3. **Batch Processing**
```python
# Generate multiple PDFs
pdf_files = PDFGenerator.generate_batch([
    {'template': 'template1.html', 'context': context1, 'filename': 'file1.pdf'},
    {'template': 'template2.html', 'context': context2, 'filename': 'file2.pdf'},
])
```

### 4. **Web Interface**
```python
# Optional admin interface for testing
@admin.register(PDFTemplate)
class PDFTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_path', 'created_at']
    actions = ['generate_test_pdf']
```

## 📦 **Installation Process**

### **Method 1: Copy App**
```bash
# Copy the entire app to your project
cp -r pdf_generator/ your_project/apps/

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'apps.pdf_generator',
]
```

### **Method 2: Install as Package**
```bash
# Install via pip
pip install django-pdf-generator

# Or via Poetry
poetry add django-pdf-generator
```

## ⚙️ **Configuration**
```python
# settings.py
INSTALLED_APPS = [
    ...
    'pdf_generator',
]

# Configure the app
PDF_GENERATOR = {
    'DEFAULT_FORMAT': 'A4',
    'TEMPLATE_DIR': 'pdf_templates',
    'BROWSER_ARGS': ['--no-sandbox', '--disable-setuid-sandbox'],
}
```

## 🎨 **Template System**

### **Base Template**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}PDF Document{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    {% block extra_css %}{% endblock %}
    <style>
        /* PDF-specific styles */
        @media print {
            body {
                margin: 0;
                padding: 0;
                font-size: 12pt;
                line-height: 1.4;
            }
            
            .no-print {
                display: none !important;
            }
            
            * {
                color: black !important;
                background: white !important;
            }
        }
        
        /* General styles for better PDF rendering */
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        
        h1, h2, h3, h4, h5, h6 {
            margin-top: 0;
            margin-bottom: 0.5em;
            font-weight: 600;
        }
        
        p {
            margin-bottom: 0.5em;
        }
        
        ul, ol {
            margin-bottom: 0.5em;
            padding-left: 1.5em;
        }
        
        li {
            margin-bottom: 0.25em;
        }
    </style>
    {% block pdf_styles %}{% endblock %}
</head>
<body class="bg-white">
    {% block pdf_content %}
        <!-- Default content -->
    {% endblock %}
</body>
</html>
```

### **Custom Template Example**
```html
{% extends "pdf_generator/base.html" %}

{% block title %}{{ article.title }} - PDF{% endblock %}

{% block pdf_styles %}
<style>
    .article-header {
        border-bottom: 2px solid #333;
        margin-bottom: 20px;
        padding-bottom: 10px;
    }
    
    .article-content {
        font-size: 14pt;
        line-height: 1.8;
    }
</style>
{% endblock %}

{% block pdf_content %}
<div class="article-header">
    <h1>{{ article.title }}</h1>
    <p class="text-gray-600">By {{ article.author }} | {{ article.published_date|date:"F j, Y" }}</p>
</div>

<div class="article-content">
    {{ article.content|safe }}
</div>
{% endblock %}
```

## 🔍 **Technical Implementation Details**

### **Context Manager Pattern**
```python
class PlaywrightPDFGenerator:
    def __enter__(self):
        """Context manager entry"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not installed")
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-zygote',
                '--single-process'
            ]
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
```

### **PDF Generation Parameters**
```python
pdf_bytes = self.page.pdf(
    format='A4',                    # Page format
    print_background=True,          # Include background colors/images
    margin={                        # Page margins
        'top': '0.5in',
        'right': '0.5in',
        'bottom': '0.5in',
        'left': '0.5in'
    },
    prefer_css_page_size=True       # Use CSS page size settings
)
```

### **Headless Browser Configuration**
```python
args=[
    '--no-sandbox',           # Required for containerized environments
    '--disable-setuid-sandbox', # Security bypass for containers
    '--disable-dev-shm-usage',  # Memory optimization
    '--disable-gpu',           # Disable GPU for headless mode
    '--no-first-run',          # Skip first-run setup
    '--no-zygote',            # Disable zygote process
    '--single-process'         # Single process mode
]
```

## 🧪 **Testing**

### **Management Command**
```bash
# Generate test PDF
python manage.py generate_pdf --output=test.pdf --template=professional

# Generate with custom options
python manage.py generate_pdf --output=invoice.pdf --template=invoice --format=Letter
```

### **Unit Tests**
```python
from django.test import TestCase
from pdf_generator.core.generator import PDFGenerator

class PDFGeneratorTestCase(TestCase):
    def test_generate_from_template(self):
        context = {'name': 'John Doe', 'title': 'Software Engineer'}
        pdf_bytes = PDFGenerator.generate_from_template(
            'test_template.html',
            context,
            options={'format': 'A4'}
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)
```

## 🚀 **Benefits Over Traditional PDF Libraries**

1. **Perfect Visual Fidelity**: Renders exactly as seen in browser
2. **Full CSS Support**: All modern CSS features work
3. **Responsive Design**: Maintains layout integrity
4. **JavaScript Rendering**: Can handle dynamic content
5. **Modern Web Features**: Supports all contemporary web standards
6. **No Layout Issues**: Eliminates common PDF formatting problems

## 🔧 **Error Handling and Fallbacks**

1. **Import Error Handling**: Graceful fallback if Playwright unavailable
2. **Resource Cleanup**: Context manager ensures proper cleanup
3. **Browser Launch Errors**: Proper error messages for debugging
4. **Template Rendering**: Handles missing templates gracefully

## 📚 **Migration Path**

1. **Extract** current PDF logic from resume_builder
2. **Generalize** the code to work with any template/context
3. **Create** the standalone app structure
4. **Update** resume_builder to use the new app
5. **Test** thoroughly with different scenarios
6. **Document** usage patterns and examples

## 🎯 **Future Enhancements**

1. **WebSocket Support**: Real-time PDF generation progress
2. **Queue System**: Background PDF generation for large files
3. **Template Editor**: Web-based template creation interface
4. **PDF Merging**: Combine multiple PDFs into one
5. **Watermarking**: Add watermarks to generated PDFs
6. **Digital Signatures**: Sign PDFs digitally
7. **Form Filling**: Fill PDF forms programmatically

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 **Support**

For support and questions, please open an issue on GitHub or contact the maintainers. 