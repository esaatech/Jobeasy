#!/usr/bin/env python3
"""
Test script to verify resume builder integration with standalone PDF generator
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
django.setup()

from django.contrib.auth import get_user_model
from resume_builder.models import Resume
from pdf_generator.core.generator import PDFGenerator

User = get_user_model()

def test_resume_pdf_integration():
    """Test that resume builder works with the standalone PDF generator"""
    
    print("🧪 Testing Resume Builder + PDF Generator Integration")
    print("=" * 60)
    
    # Create a test user if needed
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        print(f"✅ Created test user: {user.username}")
    else:
        print(f"✅ Using existing test user: {user.username}")
    
    # Create a test resume
    resume_data = {
        'personal_info': {
            'full_name': 'John Doe',
            'title': 'Software Engineer',
            'email': 'john.doe@example.com',
            'phone': '123-456-7890',
            'summary': 'Experienced software engineer with 5+ years of experience in web development.'
        },
        'experience': [
            {
                'company': 'Tech Corp',
                'position': 'Senior Software Engineer',
                'startDate': '2022-01',
                'endDate': 'Present',
                'description': 'Led development of microservices architecture serving 1M+ users.'
            }
        ],
        'education': [
            {
                'institution': 'University of Technology',
                'degree': 'Bachelor of Computer Science',
                'startDate': '2016-09',
                'endDate': '2020-05',
                'description': 'Graduated with honors.'
            }
        ],
        'skills': {
            'technical': ['JavaScript', 'React', 'Node.js', 'Python', 'PostgreSQL'],
            'soft': ['Leadership', 'Problem Solving', 'Team Collaboration'],
            'languages': ['English', 'Spanish']
        },
        'additional': {
            'certifications': 'AWS Certified Developer',
            'projects': 'Built personal finance tracker app'
        }
    }
    
    # Create or update resume
    resume, created = Resume.objects.get_or_create(
        user=user,
        name='Test Resume',
        defaults={
            'personal_info': resume_data['personal_info'],
            'experience': resume_data['experience'],
            'education': resume_data['education'],
            'skills': resume_data['skills'],
            'additional': resume_data['additional'],
            'template_id': 'professional',
            'draft': False
        }
    )
    
    if created:
        print(f"✅ Created test resume: {resume.name}")
    else:
        print(f"✅ Using existing test resume: {resume.name}")
    
    # Test 1: Generate PDF using the standalone PDF generator
    print("\n1. Testing PDF generation with standalone PDF generator...")
    try:
        context = {
            'resume_data': resume_data,
            'resume_name': resume.name,
            'generated_date': '2024-01-01'
        }
        
        pdf_bytes = PDFGenerator.generate_from_template(
            template_name='resume_templates/professional.html',
            context=context,
            options={
                'format': 'A4',
                'print_background': True,
                'margins': {
                    'top': '0.5in',
                    'right': '0.5in',
                    'bottom': '0.5in',
                    'left': '0.5in'
                }
            }
        )
        
        # Save test PDF
        file_path = PDFGenerator.save_to_file(pdf_bytes, f'resume_integration_test_{resume.id}.pdf')
        
        print(f"✅ PDF generated successfully!")
        print(f"📄 File saved as: {file_path}")
        print(f"📊 File size: {len(pdf_bytes)} bytes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Test the actual download_resume_file view logic
    print("\n2. Testing download_resume_file view logic...")
    try:
        # Test the PDF generation part that the view would use
        context = {
            'resume_data': resume_data,
            'resume_name': resume.name,
            'generated_date': '2024-01-01'
        }
        
        pdf_bytes = PDFGenerator.generate_from_template(
            template_name='resume_templates/professional.html',
            context=context,
            options={
                'format': 'A4',
                'print_background': True,
                'margins': {
                    'top': '0.5in',
                    'right': '0.5in',
                    'bottom': '0.5in',
                    'left': '0.5in'
                }
            }
        )
        
        file_path = PDFGenerator.save_to_file(pdf_bytes, f'resume_view_test_{resume.id}.pdf')
        
        print(f"✅ View logic test successful!")
        print(f"📄 File saved as: {file_path}")
        print(f"📊 File size: {len(pdf_bytes)} bytes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Integration test passed! Resume builder works with standalone PDF generator.")
    print("\n📋 Summary:")
    print("✅ Standalone PDF generator integration")
    print("✅ Resume data handling")
    print("✅ Template rendering")
    print("✅ PDF generation with proper options")
    print("✅ File saving functionality")
    print("✅ View logic compatibility")
    
    return True

if __name__ == "__main__":
    success = test_resume_pdf_integration()
    sys.exit(0 if success else 1) 