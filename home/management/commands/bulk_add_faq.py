from django.core.management.base import BaseCommand
from home.models import FAQ

class Command(BaseCommand):
    help = 'Bulk add English FAQs to the FAQ model.'

    def handle(self, *args, **options):
        faqs = [
            {'question': 'Is my data secure and private?', 'answer': 'Yes, your data is encrypted and never shared with third parties. You have full control over your information.', 'order': 1, 'published': True, 'language': 'en'},
            {'question': 'Can I use the app for free?', 'answer': 'Absolutely! You can start for free and upgrade for advanced features when you are ready.', 'order': 2, 'published': True, 'language': 'en'},
            {'question': 'How does the AI generate my resume and cover letter?', 'answer': 'Our AI analyzes your input and job description to craft tailored, professional documents that match your target role.', 'order': 3, 'published': True, 'language': 'en'},
            {'question': 'Can I edit my documents after generation?', 'answer': 'Yes, you can fully edit and customize your resume and cover letter before downloading or applying.', 'order': 4, 'published': True, 'language': 'en'},
            {'question': 'What formats can I download my resume in?', 'answer': 'You can download your resume and cover letter in PDF format.', 'order': 5, 'published': True, 'language': 'en'},
            {'question': 'Can I create multiple resumes for different jobs?', 'answer': 'Yes, you can create and manage multiple resumes tailored to different roles or industries.', 'order': 6, 'published': True, 'language': 'en'},
            {'question': 'How do I get job recommendations?', 'answer': 'Our platform suggests jobs based on your profile, skills, and preferences. You can also search and filter jobs manually.', 'order': 7, 'published': True, 'language': 'en'},
            {'question': 'Is there support if I need help?', 'answer': 'Yes, our support team is available via chat and email to assist you with any questions or issues.', 'order': 8, 'published': True, 'language': 'en'},
            {'question': 'Can I use the platform on mobile devices?', 'answer': 'Absolutely! Our platform is fully responsive and works on smartphones, tablets, and desktops.', 'order': 9, 'published': True, 'language': 'en'},
            {'question': 'How do I update or delete my account?', 'answer': 'You can update your profile or delete your account at any time from your account settings.', 'order': 10, 'published': True, 'language': 'en'},
        ]
        created = 0
        for faq in faqs:
            obj, was_created = FAQ.objects.get_or_create(
                question=faq['question'],
                defaults={
                    'answer': faq['answer'],
                    'order': faq['order'],
                    'published': faq['published'],
                    'language': faq['language'],
                }
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully added {created} FAQs.')) 