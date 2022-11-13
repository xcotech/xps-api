import json
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.contrib.auth import get_user_model
import numpy

class Command(BaseCommand):
    help = 'usage: python manage.py user_aggregate_stats'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)

    def handle(self, *args, **options):
        user_id = options['user_id']
        print('user?? %s' % user_id)
        if not user_id:
            return