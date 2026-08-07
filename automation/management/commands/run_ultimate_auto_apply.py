from django.core.management.base import BaseCommand

from automation.services.job_matcher import run_match_cycle


class Command(BaseCommand):
    help = (
        'Match active scraped jobs to Ultimate/Test users with auto-apply enabled '
        'and create queued ApplyTask rows.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Only match for a single user primary key.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Count matches without creating ApplyTask rows.',
        )

    def handle(self, *args, **options):
        result = run_match_cycle(
            user_id=options.get('user_id'),
            dry_run=options['dry_run'],
        )

        prefix = 'Dry-run match' if options['dry_run'] else 'Match'
        self.stdout.write(
            self.style.SUCCESS(
                f'{prefix} complete: '
                f'users_considered={result.users_considered}, '
                f'users_matched={result.users_matched}, '
                f'tasks_created={result.tasks_created}'
            )
        )

        for user_result in result.per_user:
            if user_result.skipped_ineligible:
                self.stdout.write(
                    f'  skip user={user_result.username} reason={user_result.reason}'
                )
            elif user_result.skipped_cap:
                self.stdout.write(
                    f'  cap user={user_result.username} reason={user_result.reason}'
                )
            elif user_result.created:
                self.stdout.write(
                    f'  ok user={user_result.username} created={user_result.created}'
                )
