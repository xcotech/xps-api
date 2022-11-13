from django.core.management.base import BaseCommand
from apps.tracking.models import *
import json

class Command(BaseCommand):
    help = 'usage: python manage.py flush_cache'

    def handle(self, *args, **options):

        from xps_cloud.redis import RedisObject
        redis = RedisObject().get_redis_connection(slave=False)    
        redis.flushdb()
        print('---------------------------\n')
        print('Redis cache flushed')
        print('---------------------------')