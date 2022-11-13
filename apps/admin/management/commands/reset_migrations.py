from django.core.management.base import BaseCommand
from django.db.migrations.recorder import MigrationRecorder

class Command(BaseCommand):
    help = 'usage: python manage.py reset_migrations'

    def handle(self, *args, **options):

        print('-- deleting Migration objects')
        MigrationRecorder.Migration.objects.all().delete()