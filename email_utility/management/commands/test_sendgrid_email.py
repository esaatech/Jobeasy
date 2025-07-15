from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Test SendGrid email sending with detailed debugging'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            default='engrjoelivon@yahoo.com',
            help='Recipient email address'
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='Test Email from Django SendGrid',
            help='Email subject'
        )

    def handle(self, *args, **options):
        recipient = options['to']
        subject = options['subject']
        
        self.stdout.write(self.style.SUCCESS('=== SendGrid Email Test ==='))
        
        # Print configuration
        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"EMAIL_HOST_PASSWORD: {'SET' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"FROM_EMAIL env: {os.environ.get('FROM_EMAIL', 'NOT SET')}")
        self.stdout.write(f"SENDGRID_MAIL_ACCESS: {'SET' if os.environ.get('SENDGRID_MAIL_ACCESS') else 'NOT SET'}")
        
        # Test simple email
        self.stdout.write('\n--- Testing Simple Email ---')
        try:
            result = send_mail(
                subject=subject,
                message='This is a test email from Django using SendGrid.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Simple email sent successfully! Result: {result}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Simple email failed: {str(e)}'))
        
        # Test HTML email
        self.stdout.write('\n--- Testing HTML Email ---')
        try:
            html_message = """
            <html>
            <body>
                <h2>Test Email from Django SendGrid</h2>
                <p>This is a test email sent from Django using SendGrid.</p>
                <p>If you receive this, the configuration is working!</p>
            </body>
            </html>
            """
            
            email = EmailMultiAlternatives(
                subject=f"{subject} (HTML)",
                body='This is the plain text version.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            self.stdout.write(self.style.SUCCESS('HTML email sent successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'HTML email failed: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Test Complete ===')) 