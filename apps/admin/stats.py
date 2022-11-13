import datetime
import json
from django.db.models import Sum, Count
from django.db.models import Q
from django.db.models.functions import TruncDate
from apps.tracking.models import Activity
from xps_cloud.redis import RedisObject
from .models import *

STATS_CACHE_TIMEOUT = 86400

def get_stats(request):
    ''' 

        This method is reponsible for fetching and caching (and returning) 
        global, or org-for-org stats.

        Initially, these stats are focused on captured activity data and membership growth.

    '''

    # required parameters
    org = request.query_params.get('org', 0)    

    try:
        org = int(org)
    except Exception as e:
        return None

    if not org and not request.user.is_staff:
        return None

    stats_set = OrgStatsSortedSet(org)
    stats_set.delete()

    def _fetch_from_cache():
        return [json.loads(i) for i in stats_set.get_set()]

    def _rebuild_cache():
        redis = RedisObject().get_redis_connection(slave=False)
        pipe = redis.pipeline()

        # set up empty response array
        response_arr = []

        # setup a filter by session.org if necessary
        org_filter = Q(session__org__id=org) if org else Q()
        
        # query, giving annotated count results for each activity type, plus full aggregation
        acts = Activity.objects.exclude(session__org__pk=6).filter(org_filter).annotate(day=TruncDate('created'),).values('day').annotate(sprint_count=Count('pk', filter=Q(type_definition__type_obj__activity_type='sprint'))).annotate(jump_count=Count('pk', filter=Q(type_definition__type_obj__activity_type='jump'))).annotate(agility_count=Count('pk', filter=Q(type_definition__type_obj__activity_type='agility'))).annotate(freeform_count=Count('pk', filter=Q(type_definition__type_obj__activity_type='freeform'))).annotate(eng_count=Count('pk', filter=Q(type_definition__type_obj__activity_type='eng'))).annotate(all_count=Count('pk')).order_by('day')

        if acts:
            for a in acts:
                # convert the date from our aggregation into a datetime object >> into a timestamp int (midnight)
                time_score = int(datetime.datetime.timestamp(datetime.datetime.combine(a['day'], datetime.time())))
                a['all_count'],a['sprint_count'],a['jump_count'],a['agility_count'],a['freeform_count'],a['eng_count']

                stats_obj = {
                    "date": time_score,
                    "activity_counts": {
                        "all": a['all_count'],
                        "sprint": a['sprint_count'],
                        "jump": a['jump_count'],
                        "agility": a['agility_count'],
                        "freeform": a['freeform_count'],
                        "eng": a['eng_count'],
                    }
                }                

                redis.pipeline(stats_set.add_to_set(json.dumps(stats_obj), time_score))            
            
            pipe.expire(stats_set.key, STATS_CACHE_TIMEOUT)
            pipe.execute()

    stats_response = _fetch_from_cache()
    if not len(stats_response):
        _rebuild_cache()
        stats_response = _fetch_from_cache()        
    return stats_response