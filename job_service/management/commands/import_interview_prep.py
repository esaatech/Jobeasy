import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from question_answer.models import Category, QuestionType, Question


class Command(BaseCommand):
    help = 'Import interview prep questions from JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='job_service/static/job_service/interview_prep.json',
            help='Path to the JSON file containing interview prep questions'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing interview prep questions before importing'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']

        # Check if file exists
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Invalid JSON file: {e}')
            )
            return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading file: {e}')
            )
            return

        # Get or create the essay question type
        essay_type, created = QuestionType.objects.get_or_create(
            name='Essay',
            defaults={
                'description': 'Essay questions requiring detailed written responses',
                'template_name': 'question_answer/question_types/essay.html'
            }
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created question type: {essay_type.name}')
            )

        # Clear existing questions if requested
        if clear_existing:
            deleted_count = Question.objects.filter(type=essay_type).delete()[0]
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing interview prep questions')
            )

        # Track statistics
        categories_created = 0
        questions_created = 0
        questions_skipped = 0

        for i, item in enumerate(data, 1):
            try:
                # Get or create category
                category_name = item.get('category', 'General')
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'description': f'Interview prep questions about {category_name.lower()}'}
                )
                if created:
                    categories_created += 1

                # Check if question already exists (to avoid duplicates)
                existing_question = Question.objects.filter(
                    text=item['question'],
                    type=essay_type
                ).first()

                if existing_question:
                    questions_skipped += 1
                    self.stdout.write(
                        f'Skipped duplicate question: {item["question"][:50]}...'
                    )
                    continue

                # Create the question
                question = Question.objects.create(
                    text=item['question'],
                    type=essay_type,
                    category=category,
                    order=i,
                    options={
                        'sample_answer': item.get('answer', ''),
                        'question_type': 'interview_prep'
                    }
                )
                questions_created += 1

                self.stdout.write(
                    f'Created question {i}: {item["question"][:50]}... (Category: {category_name})'
                )

            except KeyError as e:
                self.stdout.write(
                    self.style.ERROR(f'Missing required field {e} in item {i}')
                )
                questions_skipped += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing item {i}: {e}')
                )
                questions_skipped += 1

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('IMPORT SUMMARY'))
        self.stdout.write('='*50)
        self.stdout.write(f'Categories created: {categories_created}')
        self.stdout.write(f'Questions created: {questions_created}')
        self.stdout.write(f'Questions skipped: {questions_skipped}')
        self.stdout.write(f'Total processed: {len(data)}')
        
        if questions_created > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully imported {questions_created} interview prep questions!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\nNo new questions were imported. Use --clear to replace existing questions.')
            ) 