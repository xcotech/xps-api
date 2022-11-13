import json
from datetime import datetime
import numpy as np
import copy
from django.conf import settings
from django.db.models import Q
from xps_cloud.redis import RedisObject

def get_summary_stats(org_member):
    from apps.tracking.models import Activity
    from apps.org.models import OrgMember
    from apps.org.cache import OrgMemberStatsSummary
        
    summary_dict = {}
    # base query
    activities = Activity.objects.filter(user=org_member.user).exclude(labels__contains=['incomplete']).exclude(data_summary__isnull=True)  
    if activities:
        # get max values

        filtered_max_vels = activities.filter(type_definition__type_obj__activity_type="sprint") \
            .filter(data_summary__max_velocity__gte=0) \
            .order_by('-data_summary__max_velocity') \
            .values_list('data_summary__max_velocity', flat=True)

        filtered_peak_accels = activities.filter(type_definition__type_obj__activity_type="sprint") \
            .filter(data_summary__max_acceleration__gte=0) \
            .order_by('-data_summary__max_acceleration') \
            .values_list('data_summary__max_acceleration', flat=True)                

        filtered_heights = activities.filter(type_definition__type_obj__activity_type="jump") \
            .filter(type_definition__type_obj__orientation="vertical") \
            .filter(data_summary__height__gte=0) \
            .order_by('-data_summary__height') \
            .values_list('data_summary__height', flat=True)    

        filtered_distances = activities.filter(type_definition__type_obj__activity_type="jump") \
            .filter(type_definition__type_obj__orientation="horizontal") \
            .filter(data_summary__distance__gte=0) \
            .order_by('-data_summary__distance') \
            .values_list('data_summary__distance', flat=True)         

        summary_dict['max_velocity'] = filtered_max_vels[0] if len(filtered_max_vels) else 0
        summary_dict['max_acceleration'] = filtered_peak_accels[0] if len(filtered_peak_accels) else 0
        summary_dict['height'] = filtered_heights[0] if len(filtered_heights) else 0
        summary_dict['distance'] = filtered_distances[0] if len(filtered_distances) else 0
        summary_dict['num_activities'] = activities.count()

        def member_stats_fields(type):
            # each field tuple provides the data summary key and whether the retrieval should use descending (True) sort
            stats_fields = {
                'sprint': [('max_velocity',True), ('max_acceleration',True), ('total_time',False), ('reaction_time',False)],
                'jump': [('height',True), ('distance',True)],
                'agility': [('total_time',False)], 
            }
            return stats_fields.get(type, None)

        stats_types = activities.filter(stats_type__isnull=False).order_by('stats_type').distinct('stats_type').values_list('stats_type', flat=True)
        if stats_types:
            bests_array = []
            for s in stats_types:
                if not s:
                    continue

                stats_activities = activities.filter(stats_type=s)
                if stats_activities:
                    best_dict = { 'type': s, 'metrics': [] }
                    stats_fields = member_stats_fields(stats_activities[0].type_definition.type_obj['activity_type'])
                    if stats_fields:                        
                        for sf in stats_fields:
                            try:
                                stat_array = [float(sa.data_summary[sf[0]]) for sa in stats_activities]
                                stat_value = max(stat_array) if sf[1] else min(stat_array)
                                if not stat_value > 0:
                                    continue
                                stat_dict = { 'name': sf[0], 'value': stat_value }
                                best_dict['metrics'].append(stat_dict)
                            except Exception as e:
                                pass
                    bests_array.append(best_dict)
            summary_dict['bests'] = bests_array

    return summary_dict