from xps_cloud.redis import SortedSet

class OrgStatsSortedSet(SortedSet):
    key_format = 'stats:org:%s'
    obj_id = -1

    def __init__(self, org_id, redis=None):
        self.key = self.key_format % org_id
        self.init_redis(redis)