from django.core.management.base import BaseCommand
from django.db import transaction
from ai_service.models import AIService, AIPromptConfiguration


class Command(BaseCommand):
    help = 'Setup default AI services and prompts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing prompts',
        )

    def handle(self, *args, **options):
        force_update = options['force']
        
        self.stdout.write(self.style.SUCCESS('Setting up AI services and prompts...'))
        
        with transaction.atomic():
            # Create default services
            services_data = [
                {
                    'name': 'Cover Letter Generation',
                    'slug': 'cover_letter',
                    'description': 'AI-powered cover letter generation from resume and job posting'
                },
                {
                    'name': 'Resume Optimization',
                    'slug': 'resume_optimization',
                    'description': 'AI-powered resume optimization and enhancement'
                },
                {
                    'name': 'Interview Coach',
                    'slug': 'interview_coach',
                    'description': 'AI-powered interview preparation and coaching'
                }
            ]
            
            created_services = []
            for service_data in services_data:
                service, created = AIService.objects.get_or_create(
                    slug=service_data['slug'],
                    defaults=service_data
                )
                if created:
                    self.stdout.write(f"  ✓ Created service: {service.name}")
                else:
                    self.stdout.write(f"  - Service already exists: {service.name}")
                created_services.append(service)
            
            # Create default prompts for each service
            prompts_data = [
                # Cover Letter Prompts
                {
                    'service_slug': 'cover_letter',
                    'name': 'Default Cover Letter',
                    'slug': 'default',
                    'is_default': True,
                    'system_prompt': """You are a professional cover letter writer who creates compelling, tailored cover letters.

Generate the cover letter content AND a professional title.

Your response should be structured as follows:
TITLE: [A professional title for the cover letter, 3-6 words, include company name like "Full Stack Developer Application at Company Name"]

COVER_LETTER: [The full cover letter content]

Do not include any additional formatting, headers, extra text, or appendices beyond these two sections."""
                },
                {
                    'service_slug': 'cover_letter',
                    'name': 'Cover Letter with Email Subject',
                    'slug': 'with_email_subject',
                    'is_default': False,
                    'system_prompt': """You are a professional cover letter writer who creates compelling, tailored cover letters and email subjects.

Generate the cover letter content AND a professional email subject line.

Your response should be structured as follows:
TITLE: [A professional title for the cover letter, 3-6 words, include company name like "Full Stack Developer Application at Company Name"]

EMAIL_SUBJECT: [A compelling email subject line, 5-10 words]
COVER_LETTER: [The full cover letter content]

Do not include any additional formatting, headers, extra text, or appendices beyond these three sections."""
                },
                # Resume Optimization Prompts
                {
                    'service_slug': 'resume_optimization',
                    'name': 'Default Resume Optimization',
                    'slug': 'default',
                    'is_default': True,
                    'system_prompt': """You are a professional resume optimization expert who creates compelling, tailored resumes.

Generate the optimized resume content AND a professional title.

Your response should be structured as follows:
TITLE: [A professional title for the resume, 3-6 words]
RESUME: [The full optimized resume content]

Do not include any additional formatting, headers, extra text, or appendices beyond these two sections."""
                },
                {
                    'service_slug': 'resume_optimization',
                    'name': 'Resume Optimization with Email Subject',
                    'slug': 'with_email_subject',
                    'is_default': False,
                    'system_prompt': """You are a professional resume optimization expert who creates compelling, tailored resumes and email subjects.

Generate the optimized resume content AND a professional email subject line.

Your response should be structured as follows:
TITLE: [A professional title for the resume, 3-6 words]
EMAIL_SUBJECT: [A compelling email subject line, 5-10 words]
RESUME: [The full optimized resume content]

Do not include any additional formatting, headers, extra text, or appendices beyond these three sections."""
                },
                # Interview Coach Prompts
                {
                    'service_slug': 'interview_coach',
                    'name': 'Default Interview Coach',
                    'slug': 'default',
                    'is_default': True,
                    'system_prompt': """You are a professional interview coach who helps candidates prepare for job interviews.

Provide comprehensive interview preparation guidance including common questions, best practices, and tips.

Your response should be structured as follows:
TITLE: [A professional title for the interview preparation, 3-6 words]
GUIDANCE: [The full interview preparation content]

Do not include any additional formatting, headers, extra text, or appendices beyond these two sections."""
                }
            ]
            
            for prompt_data in prompts_data:
                service = AIService.objects.get(slug=prompt_data['service_slug'])
                
                # Check if prompt already exists
                existing_prompt = AIPromptConfiguration.objects.filter(
                    service=service,
                    slug=prompt_data['slug']
                ).first()
                
                if existing_prompt and not force_update:
                    self.stdout.write(f"  - Prompt already exists: {service.name} - {prompt_data['name']}")
                    continue
                
                if existing_prompt and force_update:
                    # Update existing prompt
                    existing_prompt.name = prompt_data['name']
                    existing_prompt.system_prompt = prompt_data['system_prompt']
                    existing_prompt.is_default = prompt_data['is_default']
                    existing_prompt.save()
                    self.stdout.write(f"  ✓ Updated prompt: {service.name} - {prompt_data['name']}")
                else:
                    # Create new prompt
                    prompt = AIPromptConfiguration.objects.create(
                        service=service,
                        name=prompt_data['name'],
                        slug=prompt_data['slug'],
                        system_prompt=prompt_data['system_prompt'],
                        is_default=prompt_data['is_default']
                    )
                    self.stdout.write(f"  ✓ Created prompt: {service.name} - {prompt_data['name']}")
        
        self.stdout.write(self.style.SUCCESS('\n✓ AI services and prompts setup completed successfully!'))
        self.stdout.write('\nYou can now manage these prompts through the Django admin interface:')
        self.stdout.write('  - AI Services: /admin/ai_service/aiservice/')
        self.stdout.write('  - AI Prompt Configurations: /admin/ai_service/aipromptconfiguration/')
