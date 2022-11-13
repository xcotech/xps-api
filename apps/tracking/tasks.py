from apps.tracking.models import *

def aggregate_user_activity_data(user):
    import statistics
    import bisect 

    split_keys = ['velocities', 'times', 'accelerations']
    aggs = {}
    results = {}

    def get_splits(record):
        if record.meta and 'split_data_metres' in record.meta:
            splits = record.meta['split_data_metres']

            for key in split_keys:        
                if key in splits:
                    for i, val in enumerate(splits[key]):
                        try:
                            aggs[key][i].append(val)
                        except:
                            aggs[key].append([val])

    personal_bests = {}

    best_vj = ActivityRecord.objects.filter(user=user, activity__activity_type="jump", activity__orientation_type="vertical").order_by('-meta__height').first()
    if best_vj:
        personal_bests['vertical_jump_m'] = best_vj.meta['height']

    best_broad_jump = ActivityRecord.objects.filter(user=user, activity__activity_type="jump", activity__orientation_type="horizontal").order_by('-meta__length').first()
    if best_broad_jump:
        personal_bests['broad_jump_m'] = best_broad_jump.meta['length']

    best_rx_time = ActivityRecord.objects.filter(user=user, activity__activity_type="sprint", activity__start_type="beep", meta__reaction_time__gte=0.05).order_by('meta__reaction_time').first()
    if best_rx_time:
        personal_bests['reaction_time_s'] = best_rx_time.meta['reaction_time']

    sprints = ActivityRecord.objects.filter(user=user, activity__activity_type="sprint")

    all_splits = []
    
    if sprints:
        for s in sprints:
            try:
                splits = s.meta['split_data_metres']
                if 'velocities' in splits:
                    all_splits += splits['velocities']
            except Exception as e:
                print(e)
                pass
        
        if all_splits:
            sorted_splits = sorted(all_splits, reverse=True)
            split_index = bisect.bisect(sorted_splits, 1)
            personal_bests['max_velocity_mps'] = sorted_splits[split_index]

        for key in split_keys:
            aggs[key] = []
            results[key] = []

        for r in sprints:
            # print(r.meta)
            get_splits(r)

        for key, val in aggs.items():
            for i, el in enumerate(val):
                split_data = {}                
                try:
                    split_data['std_dev'] = statistics.stdev(el)
                    split_data['mean'] = statistics.mean(el)                
                    results[key].append(split_data)                

                except Exception as e:
                    pass

    user.summary_data = { "splits": results, "personal_bests": personal_bests }
    user.save()