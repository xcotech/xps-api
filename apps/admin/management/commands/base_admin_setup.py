from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'usage: python manage.py base_admin_setup'

    def handle(self, *args, **options):
        from apps.org.models import Org, OrgTag, OrgSystem
        from apps.system.models import System, Tag

        new_user = None
        full_name = input('Enter the user\'s full name: ')
        split_full_name = full_name.split(' ')
        first_name = split_full_name[0]
        last_name = full_name[len(first_name):].strip() if len(full_name) > len(first_name) else ''

        username = input('Username: ')
        username = username if username else slugify(full_name)

        try:
            new_user = get_user_model().objects.get(username=username)
        except Exception as e:
            pass

        if not new_user:
            new_user = get_user_model().objects.create(first_name=full_name, last_name=last_name, username=username, is_staff=True)
                
        password = input('Password: ')
        new_user.set_password(password)
        new_user.save()

        org = Org.objects.create(name="Local XCO Org", owner=new_user)

        tag_range = (1,100)

        t = tag_range[0]
        while t < tag_range[1]:
            tag = Tag.objects.create(name=str(t))
            org_tag = OrgTag.objects.create(tag=tag, org=org)
            t += 1

        print('Setup complete --------------------')