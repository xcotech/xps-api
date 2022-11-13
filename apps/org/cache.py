from xps_cloud.redis import SortedSet, RedisHash

class OrgMemberSortedSet(SortedSet):
    key_format = 'l:orgmember:%s:%s'

    def __init__(self, org_id, encoded_key, redis=None):
        self.key = self.key_format % (org_id, encoded_key)
        self.init_redis(redis)

class OrgMemberDatedStats(SortedSet):
    key_format = 'stats:om:dated:%s:%s'
    # sort_attr is the stat value (eg):
    # velocity, height, length
    def __init__(self, org_member_id, sort_attr, redis=None):
        self.key = self.key_format % (org_member_id, sort_attr)
        self.init_redis(redis)

class OrgMemberStatsSummary(RedisHash):
    key_format = 'stats:om:summary:%s'
    
    def __init__(self, org_member_id, redis=None):
        self.key = self.key_format % org_member_id
        self.init_redis(redis)