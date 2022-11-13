from xps_cloud.redis import SortedSet, RedisHash

class ActivityFavSortedSet(SortedSet):
    key_format = 'l:favs:%s'

    def __init__(self, user_id, redis=None):
        self.key = self.key_format % user_id
        self.init_redis(redis)

class ActivityList(SortedSet):
    key_format = 'l:act:%s'

    def __init__(self, org_id, redis=None):
        self.key = self.key_format % org_id
        self.init_redis(redis)

class ActivityModels(RedisHash):
    key_format = 'm:acts'

class ActivityModelsAlt(RedisHash):
    key_format = 'm:acts:alt'    