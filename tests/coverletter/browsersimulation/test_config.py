"""
Configuration file for Cover Letter Browser Simulation Tests
Contains test settings, sample data, and utility functions.
"""

import os

# Test Configuration
TEST_CONFIG = {
    'base_url': 'http://127.0.0.1:8009',
    'timeout': 30000,  # 30 seconds
    'headless': False,  # Set to True for headless mode
    'screenshot_on_error': True,
    'wait_timeout': 10000,  # 10 seconds for AI processing
}

# Sample Test Data
SAMPLE_JOB_DESCRIPTION = """
Senior Software Engineer - Full Stack Development

Company: TechCorp Solutions
Location: Remote (US-based)
Type: Full-time

About Us:
TechCorp Solutions is a rapidly growing technology company specializing in cloud-based solutions for enterprise clients. We're looking for a passionate Senior Software Engineer to join our dynamic team and help build innovative products that transform how businesses operate.

Job Description:
We are seeking a Senior Software Engineer with strong full-stack development skills to join our engineering team. You will be responsible for designing, developing, and maintaining scalable web applications and services.

Key Responsibilities:
• Design and implement scalable, high-performance web applications using modern technologies
• Collaborate with cross-functional teams including product managers, designers, and other engineers
• Write clean, maintainable, and well-documented code
• Participate in code reviews and contribute to technical architecture decisions
• Mentor junior developers and share best practices
• Troubleshoot and debug complex issues across the full stack
• Optimize application performance and ensure high availability
• Stay current with emerging technologies and industry trends

Required Qualifications:
• 5+ years of experience in software development
• Strong proficiency in JavaScript/TypeScript, Python, or Java
• Experience with modern frontend frameworks (React, Vue.js, or Angular)
• Knowledge of backend development and API design
• Experience with cloud platforms (AWS, Azure, or GCP)
• Familiarity with database technologies (SQL and NoSQL)
• Understanding of DevOps practices and CI/CD pipelines
• Strong problem-solving skills and attention to detail
• Excellent communication and collaboration abilities

What We Offer:
• Competitive salary and equity package
• Comprehensive health, dental, and vision insurance
• Flexible work arrangements and remote work options
• Professional development opportunities
• Collaborative and inclusive work environment
• Modern tech stack and tools
• Regular team events and activities

Join our team and help us build the future of enterprise technology!
"""

SAMPLE_RESUME_TEXT = """
John Doe
Senior Software Engineer
john.doe@email.com
(555) 123-4567
San Francisco, CA

EXPERIENCE:
Senior Software Engineer | TechStart Inc. | 2020-2023
• Led development of scalable web applications using React, Node.js, and Python
• Implemented microservices architecture improving system performance by 40%
• Mentored 3 junior developers and conducted code reviews
• Collaborated with cross-functional teams to deliver features on time

Software Engineer | WebCorp | 2018-2020
• Developed full-stack applications using JavaScript, Python, and PostgreSQL
• Optimized database queries reducing load times by 60%
• Participated in agile development processes and sprint planning

SKILLS:
• Programming Languages: JavaScript, TypeScript, Python, Java, SQL
• Frontend: React, Vue.js, HTML5, CSS3, Tailwind CSS
• Backend: Node.js, Django, Flask, Express.js
• Databases: PostgreSQL, MongoDB, Redis
• Cloud: AWS, Docker, Kubernetes, CI/CD
• Tools: Git, VS Code, Postman, Jira

EDUCATION:
Bachelor of Science in Computer Science
University of Technology | 2018
"""

# Element Selectors for different page elements
SELECTORS = {
    'login': {
        'username': 'input[name="username"]',
        'password': 'input[name="password"]',
        'submit': 'button[type="submit"]'
    },
    'navigation': {
        'cover_letter_link': [
            'a[href*="coverletter/job-cover-letter"]',
            'a:has-text("Cover Letter")',
            'a[href*="coverletter"]'
        ]
    },
    'resume_selection': {
        'cards': '.resume-card',
        'selected': 'input[name="selected_resume"]:checked'
    },
    'file_upload': {
        'input': [
            'input[type="file"]',
            'input[accept*=".pdf"]',
            'input[accept*=".txt"]',
            'input[accept*=".doc"]',
            'input[accept*=".docx"]',
            '#resume',
            'input[name="resume"]'
        ]
    },
    'job_description': {
        'textarea': [
            'textarea[name="job_posting"]',
            'textarea[name="job_description"]',
            'textarea[placeholder*="job"]',
            '#job-description',
            '.job-description textarea'
        ]
    },
    'form_submission': {
        'submit_button': [
            'button[type="submit"]',
            'button:has-text("Generate")',
            'button:has-text("Submit")',
            'button:has-text("Create Cover Letter")',
            '.submit-btn',
            '#generate-btn',
            '#coverLetterForm button[type="submit"]'
        ]
    },
    'results': {
        'section': [
            '#results',
            '.results',
            '.cover-letter-result',
            '.generated-content',
            '.success-message',
            '.alert-success'
        ],
        'content': [
            '#coverLetterContent',
            '.cover-letter-content',
            '.generated-text',
            'p, div'  # Fallback to any text content
        ]
    },
    'action_buttons': {
        'copy': [
            '#copyButton',
            '.copy-btn',
            'button:has-text("Copy")',
            'button:has-text("Copy to Clipboard")'
        ],
        'edit': [
            '#editButton',
            '.edit-btn',
            'button:has-text("Edit")',
            'button:has-text("Edit Letter")'
        ],
        'download': [
            '#downloadButton',
            '.download-btn',
            'button:has-text("Download")',
            'button:has-text("Download PDF")',
            'a[href*="download"]'
        ],
        'email': [
            '#emailButton',
            '.email-btn',
            'button:has-text("Email")',
            'button:has-text("Send Email")'
        ]
    },
    'error_messages': [
        '.bg-red-50',
        '.error-message',
        '.alert-error',
        '.text-red-600',
        '.alert-danger'
    ]
}

# Test URLs
URLS = {
    'cover_letter_page': '/coverletter/job-cover-letter/',
    'dashboard': '/dashboard/',
    'login': '/auth/login/'
}

def get_full_url(path):
    """Get full URL for a given path."""
    return f"{TEST_CONFIG['base_url']}{path}"

def create_temp_resume_file(content, filename='temp_resume.txt'):
    """Create a temporary resume file for testing."""
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, 'w') as f:
        f.write(content)
    return filepath

def cleanup_temp_file(filepath):
    """Clean up temporary file."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception:
        pass
    return False 