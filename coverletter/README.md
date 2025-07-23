# Cover Letter App Documentation

## 📋 Overview

The Cover Letter app provides a comprehensive system for creating, managing, and generating professional cover letters. It integrates with the AI Resume Assistant to create structured cover letters and generates high-quality PDFs using the PDF Generator app.

## 🏗️ Architecture

### Core Components

1. **Cover Letter Model** (`models.py`)
   - Stores cover letter data in structured format
   - Uses TextField for flexible content storage
   - Supports user-specific cover letters

2. **PDF Generation** (`views.py`)
   - Generates professional PDFs using Playwright
   - Uses structured templates for consistent formatting
   - Supports both download and print functionality

3. **AI Integration** (`function_handlers.py`)
   - Integrates with OpenAI Assistant for content creation
   - Saves data in structured format for PDF generation
   - Emits real-time events to frontend

## 📊 Data Structure

### Cover Letter Content Format

Cover letters are stored using Python dictionary strings (not JSON) with the following structure:

```python
{
    'user_info': {
        'full_name': 'John Doe',
        'address': '123 Main St, City, State',
        'email': 'john@example.com',
        'phone': '555-1234'
    },
    'employer_info': {
        'company_name': 'Tech Company',
        'position_title': 'Software Developer',
        'hiring_manager': 'Jane Smith',
        'company_address': '456 Business Ave, City, State'
    },
    'greeting': {
        'text': 'Dear Jane Smith,'
    },
    'introduction': {
        'text': 'I am writing to express my interest...'
    },
    'body': {
        'text': 'With my experience in web development...'
    }
}
```

### Database Schema

```python
class CoverLetter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default='Cover Letter')
    content = models.TextField(blank=True, null=True)  # Structured data as string
    job_description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[...])
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## 🎨 PDF Generation

### Template System

The PDF generation uses a dedicated template (`pdf_template.html`) with:

- **Professional Formatting**: Times New Roman font, proper margins
- **Compact Layout**: Optimized spacing to fit on one page
- **Structured Sections**: Header, content, closing, signature
- **Print-Ready**: Proper page breaks and formatting

### Key Features

```css
@page {
    margin: 0.75in;  /* Compact margins */
    size: letter;
}

body {
    font-family: 'Times New Roman', serif;
    line-height: 1.4;  /* Optimized line spacing */
    font-size: 12pt;
}
```

### Usage Example

```python
from coverletter.views import download_cover_letter_pdf

# Generate PDF
response = download_cover_letter_pdf(request, cover_letter_id)

# Response includes:
# - Content-Type: application/pdf
# - Content-Disposition: attachment; filename="cover_letter_{id}.pdf"
# - PDF bytes for download
```

## 🔧 API Endpoints

### Download PDF
```
GET /coverletter/download/{cover_letter_id}/
```
- Generates and serves PDF version of cover letter
- Requires authentication
- Returns PDF file for download

### Edit Cover Letter
```
POST /coverletter/edit/{cover_letter_id}/
```
- Updates cover letter content
- Accepts JSON with new content
- Returns success/error status

### View Cover Letter
```
GET /coverletter/view/{cover_letter_id}/
```
- Displays cover letter in web interface
- Supports edit mode
- Includes print and download buttons

## 🤖 AI Integration

### Function Handlers

The AI assistant uses these functions to create cover letters:

1. **`create_cover_letter`**: Initializes new cover letter
2. **`save_cover_letter_user_info`**: Saves personal information
3. **`save_cover_letter_employer_info`**: Saves company details
4. **`save_cover_letter_greeting`**: Saves salutation
5. **`save_cover_letter_introduction`**: Saves opening paragraph
6. **`save_cover_letter_body`**: Saves main content
7. **`finalize_cover_letter`**: Marks cover letter as complete

### Data Flow

```
AI Assistant → Function Handler → Database → PDF Generator → Download
     ↓              ↓                ↓            ↓           ↓
User Input → Structured Data → Content String → Template → PDF File
```

## 🎯 Frontend Integration

### Cover Letter Tab

The cover letter tab (`cover_letter_tab.html`) provides:

- **Progress Tracking**: Visual progress through creation steps
- **Section Management**: Individual sections for each part
- **Real-time Updates**: Live updates from AI assistant
- **Copy/Download**: Direct access to generated content

### Key JavaScript Functions

```javascript
// Copy cover letter to clipboard
window.copyCoverLetter()

// Download cover letter as PDF
window.downloadCoverLetter()

// Update section from backend
window.updateCoverLetterSection(section, data)
```

## 📱 User Interface

### Cover Letter View Page

The view page (`cover_letter_view.html`) provides:

- **Display Mode**: Shows formatted cover letter
- **Edit Mode**: In-place editing capability
- **Print Function**: Browser print functionality
- **Download PDF**: Direct PDF download
- **Responsive Design**: Works on all devices

### Action Buttons

- **Edit**: Switch to edit mode
- **Save**: Save changes to database
- **Print**: Print using browser
- **Download PDF**: Download as PDF file
- **Back to Dashboard**: Return to main dashboard

## 🔍 Error Handling

### Common Issues

1. **PDF Generation Failures**
   - Check PDF Generator app installation
   - Verify Playwright dependencies
   - Check template file existence

2. **Data Parsing Errors**
   - Content stored as Python dict string, not JSON
   - Use `eval()` for parsing, not `json.loads()`
   - Handle NameError, SyntaxError exceptions

3. **Template Rendering Issues**
   - Verify template context variables
   - Check for missing data fields
   - Ensure proper data structure

### Debugging

```python
# Test PDF generation
poetry run python manage.py shell -c "
from coverletter.views import download_cover_letter_pdf
from django.test import RequestFactory
# ... test code
"
```

## 🚀 Deployment

### Requirements

- Django 4.0+
- PDF Generator app
- Playwright for PDF generation
- Poetry for dependency management

### Configuration

```python
# settings.py
INSTALLED_APPS = [
    'coverletter',
    'pdf_generator',
]

# PDF Generator settings
PDF_GENERATOR = {
    'DEFAULT_FORMAT': 'Letter',
    'DEFAULT_MARGINS': {
        'top': '0.75in',
        'right': '0.75in',
        'bottom': '0.75in',
        'left': '0.75in'
    }
}
```

## 📈 Performance

### Optimization Tips

1. **Template Caching**: PDF templates are cached for performance
2. **Async Processing**: Consider async PDF generation for large volumes
3. **Content Validation**: Validate data before PDF generation
4. **Error Logging**: Comprehensive error logging for debugging

### File Sizes

- **Typical PDF**: ~60KB for standard cover letter
- **Template Size**: ~2KB HTML template
- **Memory Usage**: ~10MB per PDF generation

## 🔒 Security

### Authentication

- All endpoints require user authentication
- Users can only access their own cover letters
- CSRF protection on all forms

### Data Validation

- Input validation on all user data
- SQL injection protection via Django ORM
- XSS protection via template escaping

## 📚 Examples

### Creating a Cover Letter

```python
# Via AI Assistant
user_input = "Create a cover letter for Software Developer at TechCorp"
# AI processes and calls function handlers
# Results in structured cover letter data
```

### Downloading PDF

```python
# Direct download
response = download_cover_letter_pdf(request, cover_letter_id)
# Returns PDF file for download
```

### Editing Content

```python
# Update cover letter
cover_letter.content = str(new_content_data)
cover_letter.save()
```

## 🤝 Contributing

### Development Setup

1. Clone repository
2. Install dependencies: `poetry install`
3. Run migrations: `python manage.py migrate`
4. Start development server: `python manage.py runserver`

### Testing

```bash
# Test PDF generation
poetry run python manage.py test coverletter.tests

# Test specific functionality
poetry run python manage.py shell -c "from coverletter.views import download_cover_letter_pdf; ..."
```

## 📞 Support

For issues and questions:
- Check error logs in Django admin
- Verify PDF Generator app installation
- Test with sample data
- Review template syntax

---

**Last Updated**: July 2024
**Version**: 1.0.0
**Dependencies**: Django, PDF Generator, Playwright 