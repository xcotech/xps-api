from django.core.management.base import BaseCommand
from django.db.migrations.recorder import MigrationRecorder

class Command(BaseCommand):
    help = 'usage: python manage.py activity_extrapolate <id> <num_points>'

    def add_arguments(self, parser):
        parser.add_argument('act_id', type=int)
        parser.add_argument('num_points', type=int)

    def handle(self, *args, **options):
        from apps.tracking.utils import activity_extrapolate
        from apps.tracking.models import Activity, ActivityData

        act_id = options['act_id']
        num_points = options['num_points'] or 10
        if not act_id:
            return        

        activity_data = ActivityData.objects.get(activity__pk=act_id)
        activity_extrapolate(activity_data, num_points)
        print('--- we are done')
