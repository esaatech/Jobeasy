from django.core.management.base import BaseCommand
from django.db import transaction
from subscriptions.models import SubscriptionPlan, PlanDuration, FeatureCatalog
from decimal import Decimal
import os


class Command(BaseCommand):
    help = 'Set up subscription plans: Free, Plus, and Ultimate with Stripe Price IDs'

    def add_arguments(self, parser):
        parser.add_argument('--plus-monthly-id', type=str, help='Stripe Price ID for Plus Monthly')
        parser.add_argument('--plus-weekly-id', type=str, help='Stripe Price ID for Plus Weekly')
        parser.add_argument('--ultimate-monthly-id', type=str, help='Stripe Price ID for Ultimate Monthly')
        parser.add_argument('--ultimate-weekly-id', type=str, help='Stripe Price ID for Ultimate Weekly')
        parser.add_argument('--test-monthly-id', type=str, help='Stripe Price ID for Test Monthly')
        parser.add_argument('--test-weekly-id', type=str, help='Stripe Price ID for Test Weekly')

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write('Setting up subscription plans...')
            
            # Create features first
            self.create_features()
            
            # Create Free Plan
            free_plan, created = SubscriptionPlan.objects.get_or_create(
                name='Free',
                defaults={
                    'description': 'Basic resume creation with limited features',
                    'is_active': True,
                    'has_full_access': False,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('Created Free plan'))
            else:
                self.stdout.write('Free plan already exists')

            # Create Plus Plan
            plus_plan, created = SubscriptionPlan.objects.get_or_create(
                name='Plus',
                defaults={
                    'description': 'Enhanced features with resume saving and optimization',
                    'is_active': True,
                    'has_full_access': False,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('Created Plus plan'))
            else:
                self.stdout.write('Plus plan already exists')

            # Create Ultimate Plan
            ultimate_plan, created = SubscriptionPlan.objects.get_or_create(
                name='Ultimate',
                defaults={
                    'description': 'Complete feature set with interview preparation',
                    'is_active': True,
                    'has_full_access': False,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('Created Ultimate plan'))
            else:
                self.stdout.write('Ultimate plan already exists')

            # Create Test Plan (for development only)
            test_plan = None
            from django.conf import settings
            if settings.DEBUG:
                test_plan, created = SubscriptionPlan.objects.get_or_create(
                    name='Test',
                    defaults={
                        'description': 'Test plan for development - $0.10 for testing real payments',
                        'is_active': True,
                        'has_full_access': False,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS('Created Test plan'))
                else:
                    self.stdout.write('Test plan already exists')
            else:
                self.stdout.write('Skipping Test plan creation (production mode)')

            # Create plan durations
            self.create_plan_durations(free_plan, plus_plan, ultimate_plan, test_plan)
            
            # Assign features to plans
            self.assign_features_to_plans(free_plan, plus_plan, ultimate_plan, test_plan)
            
            # Update Stripe Price IDs if provided
            self.update_stripe_price_ids(plus_plan, ultimate_plan, test_plan, options)
            
            self.stdout.write(self.style.SUCCESS('Successfully set up all subscription plans!'))

    def create_features(self):
        """Create all available features in the catalog"""
        features_data = [
            # Free features
            {
                'name': 'Basic Resume Creation',
                'identifier': 'basic_resume_creation',
                'description': 'Create resumes using professional templates only',
                'type': 'TOOL',
            },
            {
                'name': 'Cover Letter Generation',
                'identifier': 'cover_letter_generation',
                'description': 'Generate cover letters from job descriptions only',
                'type': 'TOOL',
            },
            {
                'name': 'Professional Templates',
                'identifier': 'professional_templates',
                'description': 'Access to professional resume templates',
                'type': 'SERVICE',
            },
            
            # Plus features
            {
                'name': 'Resume Saving',
                'identifier': 'resume_saving',
                'description': 'Save and manage your generated resumes',
                'type': 'TOOL',
            },
            {
                'name': 'Resume Upload',
                'identifier': 'resume_upload',
                'description': 'Upload existing resumes for ATS optimization',
                'type': 'TOOL',
            },
            {
                'name': 'ATS Optimization',
                'identifier': 'ats_optimization',
                'description': 'Optimize resumes for Applicant Tracking Systems',
                'type': 'TOOL',
            },
            {
                'name': 'All Resume Templates',
                'identifier': 'all_resume_templates',
                'description': 'Access to all resume templates including premium ones',
                'type': 'SERVICE',
            },
            {
                'name': 'Enhanced Cover Letters',
                'identifier': 'enhanced_cover_letters',
                'description': 'Generate optimized cover letters with AI',
                'type': 'TOOL',
            },
            {
                'name': 'AI Writing Assistant',
                'identifier': 'ai_writing_assistant',
                'description': 'Access to AI-powered resume writing assistant with natural language interface',
                'type': 'TOOL',
            },
            
            # Ultimate features
            {
                'name': 'Interview Preparation',
                'identifier': 'interview_preparation',
                'description': 'Generate interview questions and preparation materials',
                'type': 'TOOL',
            },
            {
                'name': 'Priority Support',
                'identifier': 'priority_support',
                'description': 'Priority customer support and assistance',
                'type': 'SERVICE',
            },
            {
                'name': 'Advanced Analytics',
                'identifier': 'advanced_analytics',
                'description': 'Detailed analytics on resume performance',
                'type': 'SERVICE',
            },
        ]
        
        for feature_data in features_data:
            feature, created = FeatureCatalog.objects.get_or_create(
                identifier=feature_data['identifier'],
                defaults={
                    'name': feature_data['name'],
                    'description': feature_data['description'],
                    'type': feature_data['type'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'Created feature: {feature.name}')
            else:
                self.stdout.write(f'Feature already exists: {feature.name}')

    def create_plan_durations(self, free_plan, plus_plan, ultimate_plan, test_plan):
        """Create plan durations for each plan"""
        
        # Free plan - no durations needed (always free)
        
        # Plus plan durations (USD catalog; push to Stripe via provision_stripe_catalog --currency usd --apply)
        weekly_plus, created = PlanDuration.objects.get_or_create(
            plan=plus_plan,
            duration_type='WEEKLY',
            defaults={
                'price': Decimal('5.00'),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write('Created Plus Weekly duration')
        else:
            if weekly_plus.price != Decimal('5.00'):
                weekly_plus.price = Decimal('5.00')
                weekly_plus.save()
                self.stdout.write('Updated Plus Weekly duration price')
        weekly_plus.is_active = True
        weekly_plus.save(update_fields=['is_active', 'updated_at'])

        monthly_plus, created = PlanDuration.objects.get_or_create(
            plan=plus_plan,
            duration_type='MONTHLY',
            defaults={
                'price': Decimal('15.00'),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write('Created Plus Monthly duration')
        else:
            if monthly_plus.price != Decimal('15.00'):
                monthly_plus.price = Decimal('15.00')
                monthly_plus.save()
                self.stdout.write('Updated Plus Monthly duration price')
        monthly_plus.is_active = True
        monthly_plus.save(update_fields=['is_active', 'updated_at'])

        PlanDuration.objects.filter(plan=plus_plan, duration_type='YEARLY').update(is_active=False)

        # Ultimate plan durations
        weekly_ultimate, created = PlanDuration.objects.get_or_create(
            plan=ultimate_plan,
            duration_type='WEEKLY',
            defaults={
                'price': Decimal('10.00'),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write('Created Ultimate Weekly duration')
        else:
            if weekly_ultimate.price != Decimal('10.00'):
                weekly_ultimate.price = Decimal('10.00')
                weekly_ultimate.save()
                self.stdout.write('Updated Ultimate Weekly duration price')
        weekly_ultimate.is_active = True
        weekly_ultimate.save(update_fields=['is_active', 'updated_at'])

        monthly_ultimate, created = PlanDuration.objects.get_or_create(
            plan=ultimate_plan,
            duration_type='MONTHLY',
            defaults={
                'price': Decimal('39.90'),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write('Created Ultimate Monthly duration')
        else:
            if monthly_ultimate.price != Decimal('39.90'):
                monthly_ultimate.price = Decimal('39.90')
                monthly_ultimate.save()
                self.stdout.write('Updated Ultimate Monthly duration price')
        monthly_ultimate.is_active = True
        monthly_ultimate.save(update_fields=['is_active', 'updated_at'])

        PlanDuration.objects.filter(plan=ultimate_plan, duration_type='YEARLY').update(is_active=False)

        # Test plan durations
        if test_plan:
            weekly_test, created = PlanDuration.objects.get_or_create(
                plan=test_plan,
                duration_type='WEEKLY',
                defaults={
                    'price': Decimal('0.05'),
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write('Created Test Weekly duration')
            else:
                if weekly_test.price != Decimal('0.05'):
                    weekly_test.price = Decimal('0.05')
                    weekly_test.save()
                    self.stdout.write('Updated Test Weekly duration price')
            weekly_test.is_active = True
            weekly_test.save(update_fields=['is_active', 'updated_at'])

            monthly_test, created = PlanDuration.objects.get_or_create(
                plan=test_plan,
                duration_type='MONTHLY',
                defaults={
                    'price': Decimal('0.10'),
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write('Created Test Monthly duration')
            else:
                if monthly_test.price != Decimal('0.10'):
                    monthly_test.price = Decimal('0.10')
                    monthly_test.save()
                    self.stdout.write('Updated Test Monthly duration price')
            monthly_test.is_active = True
            monthly_test.save(update_fields=['is_active', 'updated_at'])

            PlanDuration.objects.filter(plan=test_plan, duration_type='YEARLY').update(is_active=False)
        else:
            self.stdout.write('Skipping Test plan durations (production mode)')

    def assign_features_to_plans(self, free_plan, plus_plan, ultimate_plan, test_plan):
        """Assign features to each plan"""
        
        # Free Plan Features
        free_features = [
            'basic_resume_creation',
            'professional_templates',
            'interview_preparation',
        ]
        
        # Plus Plan Features (includes all Free features plus:)
        plus_features = [
            'basic_resume_creation',
            'cover_letter_generation',
            'professional_templates',
            'resume_saving',
            'resume_upload',
            'ats_optimization',
            'all_resume_templates',
            'enhanced_cover_letters',
            'ai_writing_assistant',
        ]
        
        # Ultimate Plan Features (includes all Plus features plus:)
        ultimate_features = [
            'basic_resume_creation',
            'cover_letter_generation',
            'professional_templates',
            'resume_saving',
            'resume_upload',
            'ats_optimization',
            'all_resume_templates',
            'enhanced_cover_letters',
            'interview_preparation',
            'priority_support',
            'advanced_analytics',
            'ai_writing_assistant',
        ]

        # Test Plan Features (specific to test plan)
        test_features = [
            'basic_resume_creation',
            'cover_letter_generation',
            'professional_templates',
            'resume_saving',
            'resume_upload',
            'ats_optimization',
            'all_resume_templates',
            'enhanced_cover_letters',
            'interview_preparation',
            'priority_support',
            'advanced_analytics',
            'ai_writing_assistant',
        ]
        
        # Assign features to plans
        self.assign_features_to_plan(free_plan, free_features, 'Free')
        self.assign_features_to_plan(plus_plan, plus_features, 'Plus')
        self.assign_features_to_plan(ultimate_plan, ultimate_features, 'Ultimate')
        if test_plan:
            self.assign_features_to_plan(test_plan, test_features, 'Test')
        else:
            self.stdout.write('Skipping Test plan features (production mode)')

    def assign_features_to_plan(self, plan, feature_identifiers, plan_name):
        """Assign features to a specific plan"""
        features = FeatureCatalog.objects.filter(identifier__in=feature_identifiers)
        plan.features.set(features)
        self.stdout.write(f'Assigned {features.count()} features to {plan_name} plan') 

    def update_stripe_price_ids(self, plus_plan, ultimate_plan, test_plan, options):
        """Update Stripe Price IDs for plan durations"""
        self.stdout.write('Updating Stripe Price IDs...')
        
        # Update Plus plan durations
        if plus_plan:
            plus_monthly = PlanDuration.objects.filter(
                plan=plus_plan, 
                duration_type='MONTHLY'
            ).first()
            
            plus_weekly = PlanDuration.objects.filter(
                plan=plus_plan, 
                duration_type='WEEKLY'
            ).first()

            if plus_monthly and options['plus_monthly_id']:
                plus_monthly.stripe_price_id = options['plus_monthly_id']
                plus_monthly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Plus Monthly: {options["plus_monthly_id"]}')
                )

            if plus_weekly and options['plus_weekly_id']:
                plus_weekly.stripe_price_id = options['plus_weekly_id']
                plus_weekly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Plus Weekly: {options["plus_weekly_id"]}')
                )

        # Update Ultimate plan durations
        if ultimate_plan:
            ultimate_monthly = PlanDuration.objects.filter(
                plan=ultimate_plan, 
                duration_type='MONTHLY'
            ).first()
            
            ultimate_weekly = PlanDuration.objects.filter(
                plan=ultimate_plan, 
                duration_type='WEEKLY'
            ).first()

            if ultimate_monthly and options['ultimate_monthly_id']:
                ultimate_monthly.stripe_price_id = options['ultimate_monthly_id']
                ultimate_monthly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Ultimate Monthly: {options["ultimate_monthly_id"]}')
                )

            if ultimate_weekly and options['ultimate_weekly_id']:
                ultimate_weekly.stripe_price_id = options['ultimate_weekly_id']
                ultimate_weekly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Ultimate Weekly: {options["ultimate_weekly_id"]}')
                )

        # Update Test plan durations
        if test_plan:
            test_monthly = PlanDuration.objects.filter(
                plan=test_plan, 
                duration_type='MONTHLY'
            ).first()
            test_weekly = PlanDuration.objects.filter(
                plan=test_plan,
                duration_type='WEEKLY',
            ).first()

            if test_monthly and options['test_monthly_id']:
                test_monthly.stripe_price_id = options['test_monthly_id']
                test_monthly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Test Monthly: {options["test_monthly_id"]}')
                )
            if test_weekly and options.get('test_weekly_id'):
                test_weekly.stripe_price_id = options['test_weekly_id']
                test_weekly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Test Weekly: {options["test_weekly_id"]}')
                )
        else:
            self.stdout.write('Skipping Test plan Price ID updates (production mode)')

        # Also check environment variables for Price IDs
        env_price_ids = {
            'plus_monthly_id': os.getenv('STRIPE_PLUS_MONTHLY_PRICE_ID'),
            'plus_weekly_id': os.getenv('STRIPE_PLUS_WEEKLY_PRICE_ID'),
            'ultimate_monthly_id': os.getenv('STRIPE_ULTIMATE_MONTHLY_PRICE_ID'),
            'ultimate_weekly_id': os.getenv('STRIPE_ULTIMATE_WEEKLY_PRICE_ID'),
            'test_monthly_id': os.getenv('STRIPE_TEST_MONTHLY_PRICE_ID'),
            'test_weekly_id': os.getenv('STRIPE_TEST_WEEKLY_PRICE_ID'),
        }
        
        # Update from environment variables if not provided as arguments
        if plus_plan:
            plus_monthly = PlanDuration.objects.filter(
                plan=plus_plan, 
                duration_type='MONTHLY'
            ).first()
            
            plus_weekly = PlanDuration.objects.filter(
                plan=plus_plan, 
                duration_type='WEEKLY'
            ).first()

            if plus_monthly and env_price_ids['plus_monthly_id'] and not options['plus_monthly_id']:
                plus_monthly.stripe_price_id = env_price_ids['plus_monthly_id']
                plus_monthly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Plus Monthly from env: {env_price_ids["plus_monthly_id"]}')
                )

            if plus_weekly and env_price_ids['plus_weekly_id'] and not options['plus_weekly_id']:
                plus_weekly.stripe_price_id = env_price_ids['plus_weekly_id']
                plus_weekly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Plus Weekly from env: {env_price_ids["plus_weekly_id"]}')
                )

        if ultimate_plan:
            ultimate_monthly = PlanDuration.objects.filter(
                plan=ultimate_plan, 
                duration_type='MONTHLY'
            ).first()
            
            ultimate_weekly = PlanDuration.objects.filter(
                plan=ultimate_plan, 
                duration_type='WEEKLY'
            ).first()

            if ultimate_monthly and env_price_ids['ultimate_monthly_id'] and not options['ultimate_monthly_id']:
                ultimate_monthly.stripe_price_id = env_price_ids['ultimate_monthly_id']
                ultimate_monthly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Ultimate Monthly from env: {env_price_ids["ultimate_monthly_id"]}')
                )

            if ultimate_weekly and env_price_ids['ultimate_weekly_id'] and not options['ultimate_weekly_id']:
                ultimate_weekly.stripe_price_id = env_price_ids['ultimate_weekly_id']
                ultimate_weekly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Ultimate Weekly from env: {env_price_ids["ultimate_weekly_id"]}')
                ) 

        if test_plan:
            test_monthly = PlanDuration.objects.filter(
                plan=test_plan, 
                duration_type='MONTHLY'
            ).first()
            test_weekly = PlanDuration.objects.filter(
                plan=test_plan,
                duration_type='WEEKLY',
            ).first()

            if test_monthly and env_price_ids['test_monthly_id'] and not options['test_monthly_id']:
                test_monthly.stripe_price_id = env_price_ids['test_monthly_id']
                test_monthly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Test Monthly from env: {env_price_ids["test_monthly_id"]}')
                )
            if (
                test_weekly
                and env_price_ids.get('test_weekly_id')
                and not options.get('test_weekly_id')
            ):
                test_weekly.stripe_price_id = env_price_ids['test_weekly_id']
                test_weekly.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated Test Weekly from env: {env_price_ids["test_weekly_id"]}'
                    )
                )
        else:
            self.stdout.write('Skipping Test plan environment variable updates (production mode)') 