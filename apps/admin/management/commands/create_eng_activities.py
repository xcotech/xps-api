from django.core.management.base import BaseCommand
import requests

class Command(BaseCommand):
    help = 'usage: python manage.py create_eng_activities'

    def handle(self, *args, **options):

    	from admin.utils imort create_eng_activities()