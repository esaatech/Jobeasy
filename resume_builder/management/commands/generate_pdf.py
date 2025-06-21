from django.core.management.base import BaseCommand
from resume_builder.pdf_generator import generate_resume_pdf
import os

class Command(BaseCommand):
    help = 'Generate a test PDF using Playwright'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='test_resume.pdf',
            help='Output filename for the PDF'
        )
        parser.add_argument(
            '--template',
            type=str,
            default='professional',
            help='Template to use for the resume'
        )

    def handle(self, *args, **options):
        # Sample resume data
        sample_resume_data = {
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
                    'description': 'Led development of web applications using Python and Django.'
                },
                {
                    'company': 'Startup Inc',
                    'position': 'Full Stack Developer',
                    'startDate': '2020-03',
                    'endDate': '2021-12',
                    'description': 'Built and maintained React applications with Node.js backend.'
                }
            ],
            'education': [
                {
                    'institution': 'University of Technology',
                    'degree': 'Bachelor of Computer Science',
                    'startDate': '2016-09',
                    'endDate': '2020-05',
                    'description': 'Graduated with honors. Specialized in software engineering.'
                }
            ],
            'skills': {
                'technical': ['Python', 'Django', 'JavaScript', 'React', 'Node.js', 'PostgreSQL'],
                'soft': ['Leadership', 'Problem Solving', 'Team Collaboration'],
                'languages': ['English', 'Spanish']
            },
            'additional': {
                'certifications': 'AWS Certified Developer, Google Cloud Professional',
                'projects': 'Built personal finance tracker app, Open source contributor'
            }
        }

        try:
            self.stdout.write("Generating PDF with Playwright...")
            
            # Generate PDF
            pdf_bytes = generate_resume_pdf(
                resume_data=sample_resume_data,
                template_id=options['template'],
                filename=options['output']
            )
            
            # Save the PDF to a file
            with open(options['output'], 'wb') as f:
                f.write(pdf_bytes)
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ PDF generated successfully!")
            )
            self.stdout.write(f"📄 File saved as: {options['output']}")
            self.stdout.write(f"📊 File size: {len(pdf_bytes)} bytes")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error generating PDF: {e}")
            ) 