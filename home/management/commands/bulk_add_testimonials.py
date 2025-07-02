from django.core.management.base import BaseCommand
from home.models import Testimonial

class Command(BaseCommand):
    help = 'Bulk add 3 sample testimonials to the Testimonial model.'

    def handle(self, *args, **options):
        testimonials = [
            {
                'name': 'Jamie D.',
                'quote': 'This app made my job search so much easier. The AI-generated resume landed me interviews within days!',
                'published': True,
            },
            {
                'name': 'Alex S.',
                'quote': 'I loved how fast and easy it was to create a tailored cover letter. Highly recommend!',
                'published': True,
            },
            {
                'name': 'Morgan R.',
                'quote': 'The daily job matches and interview prep features are game changers. I feel so much more confident!',
                'published': True,
            },
        ]
        created = 0
        for t in testimonials:
            obj, was_created = Testimonial.objects.get_or_create(
                name=t['name'],
                quote=t['quote'],
                defaults={'published': t['published']}
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully added {created} testimonials.')) 