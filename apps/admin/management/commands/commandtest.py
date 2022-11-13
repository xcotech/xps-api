from django.core.management.base import BaseCommand
from apps.tracking.models import *
import json

class Command(BaseCommand):
    help = 'usage: python manage.py commandtest'

    def handle(self, *args, **options):
        # acts_without_ests = ActivityData.objects.filter(est__isnull=True)
        sprints_with_ests = ActivityData.objects.filter(activity__type_definition__type_obj__activity_type='sprint', est__isnull=False).values_list('activity__pk', flat=True)

        to_reprocess = {"activities": []}
        for actid in sprints_with_ests:
            activity = Activity.objects.get(pk=actid)
            algo_attrs = {}
            
            try:
                type_obj = activity.type_definition.type_obj
                algo_attrs['id'] = actid
                algo_attrs['detect_type'] = 'Sprint'
                algo_attrs['sprint_dist'] = type_obj['distance']
                if type_obj['start_type'] == 'fly':
                    algo_attrs['flying_offset'] = 10 if algo_attrs['sprint_dist'] > 20 else 3 # as close to the truth as we're going to get
                to_reprocess['activities'].append(algo_attrs)            
            except Exception as e:
                print('--- failed to build sprint detail: %s' % e)


        print('--- to to_reprocess: ', json.dumps(to_reprocess))
