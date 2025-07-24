from django.core.management.base import BaseCommand
from django.db import transaction
from subscriptions.models import SubscriptionPlan, PlanDuration, FeatureCatalog
from decimal import Decimal


class Command(BaseCommand):
    help = 'Set up subscription plans: Free, Plus, and Ultimate'

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

            # Create plan durations
            self.create_plan_durations(free_plan, plus_plan, ultimate_plan)
            
            # Assign features to plans
            self.assign_features_to_plans(free_plan, plus_plan, ultimate_plan)
            
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

    def create_plan_durations(self, free_plan, plus_plan, ultimate_plan):
        """Create plan durations for each plan"""
        
        # Free plan - no durations needed (always free)
        
        # Plus plan durations
        monthly_plus, created = PlanDuration.objects.get_or_create(
            plan=plus_plan,
            duration_type='MONTHLY',
            defaults={
                'price': Decimal('9.99'),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write('Created Plus Monthly duration')
        else:
            # Update existing price if different
            if monthly_plus.price != Decimal('9.99'):
                monthly_plus.price = Decimal('9.99')
                monthly_plus.save()
                self.stdout.write('Updated Plus Monthly duration price')
            
        yearly_plus, created = PlanDuration.objects.get_or_create(
            plan=plus_plan,
            duration_type='YEARLY',
            defaults={
                'price': Decimal('99.99'),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write('Created Plus Yearly duration')
        else:
            # Update existing price if different
            if yearly_plus.price != Decimal('99.99'):
                yearly_plus.price = Decimal('99.99')
                yearly_plus.save()
                self.stdout.write('Updated Plus Yearly duration price')

        # Ultimate plan durations
        monthly_ultimate, created = PlanDuration.objects.get_or_create(
            plan=ultimate_plan,
            duration_type='MONTHLY',
            defaults={
                'price': Decimal('40.00'),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write('Created Ultimate Monthly duration')
        else:
            # Update existing price if different
            if monthly_ultimate.price != Decimal('40.00'):
                monthly_ultimate.price = Decimal('40.00')
                monthly_ultimate.save()
                self.stdout.write('Updated Ultimate Monthly duration price')
            
        yearly_ultimate, created = PlanDuration.objects.get_or_create(
            plan=ultimate_plan,
            duration_type='YEARLY',
            defaults={
                'price': Decimal('400.00'),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write('Created Ultimate Yearly duration')
        else:
            # Update existing price if different
            if yearly_ultimate.price != Decimal('400.00'):
                yearly_ultimate.price = Decimal('400.00')
                yearly_ultimate.save()
                self.stdout.write('Updated Ultimate Yearly duration price')

    def assign_features_to_plans(self, free_plan, plus_plan, ultimate_plan):
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
        
        # Assign features to plans
        self.assign_features_to_plan(free_plan, free_features, 'Free')
        self.assign_features_to_plan(plus_plan, plus_features, 'Plus')
        self.assign_features_to_plan(ultimate_plan, ultimate_features, 'Ultimate')

    def assign_features_to_plan(self, plan, feature_identifiers, plan_name):
        """Assign features to a specific plan"""
        features = FeatureCatalog.objects.filter(identifier__in=feature_identifiers)
        plan.features.set(features)
        self.stdout.write(f'Assigned {features.count()} features to {plan_name} plan') 