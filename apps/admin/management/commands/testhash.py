from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'usage: python manage.py testhash'

    def handle(self, *args, **options):

        # def generate_model_hashid(model=None):
        from django.contrib.contenttypes.models import ContentType
        from hashids import Hashids

        from apps.org.models import Org
        model = Org.objects.get(pk=1)
        
        hashids = Hashids(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')
        print('hashid is %s' % hashids.encode(ContentType.objects.get_for_model(model).pk, model.pk, model.created.strftime('%a %b %d %H:%M:%S +0000 %Y')))



