import json
from datetime import datetime
import numpy as np
import copy
from django.conf import settings
from django.db.models import Q
from xps_cloud.utils import api_serialize
from xps_cloud.redis import RedisObject

def get_user_activity_favs(user):
    from apps.tracking.models import ActivityFav
    from apps.tracking.cache import ActivityFavSortedSet
    
    cache_set = ActivityFavSortedSet(user.pk)
    redis = RedisObject().get_redis_connection(slave=False)
    pipe = redis.pipeline()

    def rebuild_fav_list():
        act_favs = ActivityFav.objects.filter(user=user).values_list('pk', 'activity__pk', 'created')
        if act_favs:
            for af in act_favs:
                redis.pipeline(cache_set.add_to_set('%s:%s' % (af[0], af[1]), af[2].timestamp()))
            pipe.expire(cache_set.key, settings.DEFAULT_CACHE_TIMEOUT)                
            pipe.execute()

    fetched_favs = cache_set.get_full_set()
    if not fetched_favs:
        rebuild_fav_list()
        fetched_favs = cache_set.get_full_set()
    # return decoded (pk, activity_pk) tuples
    return [(int(x[0]),int(x[1])) for x in (x.split(':') for x in fetched_favs)]
    

def get_metric_split_data(activity):
    meters_per_yard = 0.9144
    activity_in_yards = True if 'units' in activity.type_definition.type_obj and activity.type_definition.type_obj['units'] == 'yards' else False    
    to_metric = meters_per_yard if activity_in_yards else 1

    if not 'events' in activity.data_summary:
        return None

    # note: start event's 'time' attribute is in seconds, need ms
    start_time = next((item['time']*1000 for item in activity.data_summary['events'] if item['type'] == 'start'), {})
    splits = [e for e in activity.data_summary['events'] if e['type'] =='split']   

    if not splits:
        return None    

    return {
        'metric_distances': [s['cumulative_distance']*to_metric for s in splits],
        'cumulative_times': [s['time']-start_time for s in splits],
        'split_velocities': [s['velocity'] for s in splits]
    }

def get_target_time(activity, target_metric_distance):
    metric_split_data = get_metric_split_data(activity)
    if not metric_split_data:
        return None     
    # return interpolated time (in seconds) based on the target distance and metric distances array
    return np.interp(target_metric_distance, metric_split_data['metric_distances'], metric_split_data['cumulative_times'])/1000

def get_target_velocity(activity, target_metric_distance):
    # get max velocity in array up to target distance
    # note, setting a healthy max value here
    metric_split_data = get_metric_split_data(activity)
    if not metric_split_data:
        return None
    # return max value from velocities array, up to the target distance    
    return np.amax([d for i, d in enumerate(metric_split_data['split_velocities']) if metric_split_data['metric_distances'][i] <= target_metric_distance])

