"""
Django management command to set up the Interview Coach assistant

Usage:
    python manage.py setup_interview_coach

This command creates the shared Interview Coach assistant and provides
the assistant ID to be used as an environment variable.
"""

from django.core.management.base import BaseCommand
from ai_service.interview_coach_manager import InterviewCoachManager


class Command(BaseCommand):
    help = 'Setup Interview Coach assistant'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up Interview Coach assistant...')
        )
        
        try:
            # Create the interview coach manager
            coach_manager = InterviewCoachManager()
            
            # Create the assistant
            assistant_id = coach_manager.create_interview_assistant()
            
            if assistant_id:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Interview Coach Assistant created successfully!')
                )
                self.stdout.write('')
                self.stdout.write('📋 NEXT STEPS:')
                self.stdout.write('')
                self.stdout.write('1. Add this assistant ID to your environment variables:')
                self.stdout.write(f'   INTERVIEW_COACH_ASSISTANT_ID={assistant_id}')
                self.stdout.write('')
                self.stdout.write('2. If using a .env file, add this line:')
                self.stdout.write(f'   INTERVIEW_COACH_ASSISTANT_ID={assistant_id}')
                self.stdout.write('')
                self.stdout.write('3. Restart your Django server')
                self.stdout.write('')
                self.stdout.write('🎉 Interview Coach is ready to use!')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Failed to create Interview Coach Assistant')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error setting up Interview Coach: {e}')
            )
            self.stdout.write('')
            self.stdout.write('Make sure your OPENAI_API_KEY is set correctly.') 