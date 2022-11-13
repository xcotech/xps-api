from xps_cloud.redis import SortedSet, RedisHash

class ModelSortedSet(SortedSet):
    key_format = 'm:sorted:%s:%s'

    def __init__(self, content_type, encoded_key, redis=None):
        self.key = self.key_format % (content_type, encoded_key)
        self.init_redis(redis)