from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import JobApplication
from coverletter.models import CoverLetter

class Command(BaseCommand):
    help = 'Creates a test JobApplication with a CoverLetter for development purposes.'

    def handle(self, *args, **kwargs):
        # 1. Find or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'password': 'password', 'email': 'test@example.com'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created test user "testuser"'))
        else:
            self.stdout.write(self.style.SUCCESS('Found existing test user "testuser"'))

        # 2. Create a CoverLetter with dummy content
        cover_letter_content = """
Dear Hiring Manager,

I am writing to express my keen interest in the position advertised on your company website. With a proven track record of success and a passion for innovation, I am confident that I possess the skills, qualifications, and dedication necessary to excel in this role.

My experience has prepared me to contribute significantly to your team. I am particularly drawn to your company's commitment to excellence.

Thank you for considering my application. I look forward to the possibility of discussing this exciting opportunity with you.

Sincerely,
A. Tester
        """.strip()

        cover_letter = CoverLetter.objects.create(
            user=user,
            title="Test Cover Letter for Shelter Cook",
            content=cover_letter_content,
            job_description="Job Posting: Shelter Cook H...",
            status='completed'
        )
        self.stdout.write(self.style.SUCCESS(f'Successfully created CoverLetter: "{cover_letter.title}"'))

        # 3. Create a JobApplication linked to the CoverLetter (no resume)
        job_application = JobApplication.objects.create(
            user=user,
            job_name="Full job description Job Posting: Shelter Cook H...",
            cover_letter=cover_letter,
            status='completed',
            resume_link=None  # Explicitly set to None
        )
        self.stdout.write(self.style.SUCCESS(f'Successfully created JobApplication: "{job_application.job_name}"'))

        self.stdout.write(self.style.SUCCESS('\nTest data created successfully! Run this command again to create more.')) 