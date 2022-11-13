from django.core.management.base import BaseCommand
from django.db.migrations.recorder import MigrationRecorder

class Command(BaseCommand):
    help = 'usage: python manage.py activity_prune <id> --range <start> <finish>'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('act_id', type=int)

        # Named (optional) arguments
        parser.add_argument(
            '--range',
            nargs='+',
            type=int
        )

    def handle(self, *args, **options):
        from apps.tracking.utils import activity_prune
        from apps.tracking.models import Activity, ActivityData

        act_id = options['act_id']
        if not act_id:
            return

        prune_range = options.get('range', None)
        if prune_range and len(prune_range) is 2:
            print(prune_range[0], prune_range[1])

        activity_data = ActivityData.objects.get(activity__pk=act_id)
        activity_prune(activity_data, prune_range[0], prune_range[1])