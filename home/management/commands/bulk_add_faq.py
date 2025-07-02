from django.core.management.base import BaseCommand
from home.models import FAQ

class Command(BaseCommand):
    help = 'Bulk add English and Spanish FAQs to the FAQ model.'

    def handle(self, *args, **options):
        faqs = [
            # English FAQs
            {'question': 'Is my data secure and private?', 'answer': 'Yes, your data is encrypted and never shared with third parties. You have full control over your information.', 'order': 1, 'published': True, 'language': 'en'},
            {'question': 'Can I use the app for free?', 'answer': 'Absolutely! You can start for free and upgrade for advanced features when you are ready.', 'order': 2, 'published': True, 'language': 'en'},
            {'question': 'How does the AI generate my resume and cover letter?', 'answer': 'Our AI analyzes your input and job description to craft tailored, professional documents that match your target role.', 'order': 3, 'published': True, 'language': 'en'},
            {'question': 'Can I edit my documents after generation?', 'answer': 'Yes, you can fully edit and customize your resume and cover letter before downloading or applying.', 'order': 4, 'published': True, 'language': 'en'},
            {'question': 'What formats can I download my resume in?', 'answer': 'You can download your resume and cover letter in PDF and Word formats.', 'order': 5, 'published': True, 'language': 'en'},
            # Spanish FAQs
            {'question': '¿Mis datos son seguros y privados?', 'answer': 'Sí, tus datos están encriptados y nunca se comparten con terceros. Tienes control total sobre tu información.', 'order': 1, 'published': True, 'language': 'es'},
            {'question': '¿Puedo usar la aplicación gratis?', 'answer': '¡Por supuesto! Puedes comenzar gratis y actualizar para funciones avanzadas cuando lo desees.', 'order': 2, 'published': True, 'language': 'es'},
            {'question': '¿Cómo genera la IA mi currículum y carta de presentación?', 'answer': 'Nuestra IA analiza tu información y la descripción del trabajo para crear documentos profesionales adaptados a tu puesto objetivo.', 'order': 3, 'published': True, 'language': 'es'},
            {'question': '¿Puedo editar mis documentos después de generarlos?', 'answer': 'Sí, puedes editar y personalizar completamente tu currículum y carta de presentación antes de descargarlos o postularte.', 'order': 4, 'published': True, 'language': 'es'},
            {'question': '¿En qué formatos puedo descargar mi currículum?', 'answer': 'Puedes descargar tu currículum y carta de presentación en formatos PDF y Word.', 'order': 5, 'published': True, 'language': 'es'},
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