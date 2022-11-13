import redis, time, datetime, json, base64
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

''' 
Core Redis classes
'''

#################################################
# REDIS SETUP ###################################
#################################################
class RedisObject(object):
    def __init__(self, redis=None):
        self.init_redis(redis)

    def init_redis(self, redis=None):
        if not redis: 
            self.redis = self.get_redis_connection()
            self.redis_slave = self.get_redis_connection(slave=True)
        else:
            self.redis = redis
            self.redis_slave = redis

    def get_redis_connection(self, slave=False):
        if slave:
            return redis.Redis(host=settings.REDIS_SLAVE_HOST, port=6379, db=0, socket_timeout=5, decode_responses=True)
        else:
            return redis.Redis(host=settings.REDIS_MASTER_HOST, port=6379, db=0, socket_timeout=5, decode_responses=True)

    def rename(self, new_name):
        self.redis.rename(self.key, new_name)

    def get_key(self):
        return self.key
        
    def exists(self):
        return self.redis.exists(self.key)

    def expire(self, timeout):
        self.redis.expire(self.key, timeout)

    def pipeline(self, transaction=True, shard_hint=None):
        self.pipeline(transaction, shard_hint)

    def execute(self):
        self.execute.pipeline()

        
class List(RedisObject):
    key_format = 'list:%s'

    def __init__(self, object_id, redis=None):
        self.key = self.key_format % object_id
        super(List, self).__init__(redis)

    def add_to_list(self, obj):
        self.redis.lpush(self.key, obj)

    def remove_from_list(self, obj):
        self.redis.lrem(self.key, obj, 0) # we assume we want to remove all occurrences

    def list_length(self):
        return self.redis_slave.llen(self.key)

    def rename(self, new_name):
        self.redis.rename(self.key, new_name)

    def get_random(self):
        return self.redis_slave.srandmember(self.key)

    def get_list(self):
        return self.redis_slave.lrange(self.key, 0, -1)

    def get_member(self, index):
        return self.redis_slave.lindex(self.key, index)

    def trim(self,range_max):
        self.redis.ltrim(self.key, 0, range_max)

    def delete(self):
        return self.redis.delete(self.key)
        
    def get_list_length(self):
        return self.redis.llen()

class RedisHash(RedisObject):
    page_length = settings.DEFAULT_PAGE_SIZE
    key_format = 'hash:%s'

    def __init__(self, object_id, redis=None):
        self.key = self.key_format % object_id
        super(RedisHash, self).__init__(redis)

    def set(self,value=None, hash_id=None):        
        hash_id = hash_id if hash_id else datetime.date.today()
        value = value if value else 0 # clear it if we've not provided a value here
        self.redis.hset(self.key,hash_id,value)

    def increment(self,increment=None,hash_id=None):
        hash_id = hash_id if hash_id else datetime.date.today()
        increment = increment if increment else 1
        return self.redis.hincrby(self.key,hash_id,increment)

    # Increment by float
    def flincrement(self,increment=None,hash_id=None):
        if not hash_id:
            hash_id = datetime.date.today()
        if not increment:
            increment = 1.0
        return self.redis.hincrbyfloat(self.key,hash_id,increment)
        
    def get(self,hash_id):
        return self.redis_slave.hget(self.key,hash_id)

    def get_values(self):
        return self.redis_slave.hvals(self.key)

    def remove_key(self):
        return self.redis.delete(self.key)

    def delete(self,hash_id):
        self.redis.hdel(self.key,hash_id)

    def get_all(self):
        return self.redis_slave.hgetall(self.key)


class SortedSet(RedisObject):
    page_length = settings.DEFAULT_PAGE_SIZE
    key_format = 'sortedset:%s'
    key = None

    def __init__(self, object_id, redis=None):
        self.key = self.key_format % object_id
        super(SortedSet, self).__init__(redis)

    def add_to_set(self, obj, score=None):
        if not score:
            score = 0
        self.redis.zadd(self.key, {obj: score})

    def init_set(self):
        # clear the set and add an '__init' placeholder; used as a caching rebuild semaphore
        self.redis.delete(self.key)
        self.add_to_set('__init')

    def exists_multiple(self, candidates):
        # Note: we pass back a trailing cache status to trigger a recache operation if necessary
        # (eg if results[-1], zcard for the set, is less than 1)
        pipe = self.redis_slave.pipeline()
        for key in candidates:
            pipe.zrank(self.key, key)
        pipe.zcard(self.key)
        results = pipe.execute()
        
        exists = [True if not res is None else False for res in results[:-1]]
        exists.append('no_keys' if not results[-1] else 'keys')
        return exists

    def exists_query(self, key_queries):
        # Note: we pass back a trailing cache status to trigger a recache operation if necessary
        pipe = self.redis_slave.pipeline()
        for key in key_queries:
            pipe.zscan(self.key, 0, match=key)
        pipe.zcard(self.key)
        keys_by_score = pipe.execute()

        exists = [True if match else False for cursor, match in keys_by_score[:-1]]
        exists.append('no_keys' if not keys_by_score[-1] else 'keys')
        return exists

    def rename(self, new_name):
        self.redis.rename(self.key, new_name)

    def increment(self,value,obj):
        self.redis.zincrby(self.key,obj,value)

    def count_members(self,obj):
        return self.redis.zcard(self.key,obj)

    def get_member_score(self,obj):
        return self.redis.zscore(self.key,obj)

    def get_member_rank(self,obj):
        return self.redis.zrank(self.key,obj)

    def get_set_count(self):
        return self.redis_slave.zcard(self.key)

    def remove_from_set(self, obj):
        return self.redis.zrem(self.key, obj)

    def truncate_set(self, limit):
        self.redis.zremrangebyrank(self.key, 0, -limit)

    def get(self, number):
        return self.redis_slave.zrange(self.key, number, number)
    
    def get_set_with_scores(self, start=0, stop=-1, ascending=False):
        if ascending:
            return self.redis_slave.zrange(self.key, start, stop, withscores=True)
        return self.redis_slave.zrevrange(self.key, start, stop, withscores=True)

    def get_set(self, start=0, stop=-1):
        return self.redis_slave.zrevrange(self.key, start, stop, withscores=False)

    def get_matching(self, query, page=None):
        if not page:
            start = 0
            num = -1
        else:
            start = self.page_length * (int(page) - 1)
            num = self.page_length

        query_range_min = '[%s|' % query
        query_range_max = '[%s|\xff' % query
        # name, min, max, start=None, num=None
        return self.redis_slave.zrevrangebylex(self.key, query_range_max, query_range_min, start, num)

    def fetch_keys(self, keys):
        return self.redis_slave.mget(str(keys))

    def delete(self):
        self.redis.delete(self.key)

    def trim_set(self,range_max):
        self.redis.zremrangebyscore(self.key, '-inf', range_max)

    def get_latest(self, withscores=False):
        return self.redis_slave.zrevrange(self.key, 0, 0, withscores=withscores)

    def get_by_rank(self, rank):
        return self.redis_slave.zrange(self.key, rank, rank)

    def get(self, obj, number):
        return self.redis_slave.zrange(self.key, number, -1)
    
    def get_full_set_asc(self, withscores=False):
        return self.redis_slave.zrange(self.key, 0, -1, withscores)

    def get_full_set(self, withscores=False):
        return self.redis_slave.zrevrange(self.key, 0, -1, withscores)

    def get_set_asc(self, min='-inf', max='+inf', start=None, num=None, withscores=True):     
        return self.redis_slave.zrangebyscore(self.key, min, max, start, num, withscores)

    def get_range_above(self, min, max='+inf', start=None, num=None, withscores=True):
        return self.redis_slave.zrangebyscore(self.key, min, max, start, num, withscores)

    def get_range_below(self, max, min='-inf', start=None, num=None, withscores=False):
        return self.redis_slave.zrangebyscore(self.key, min, max, start, num, withscores)

    def clear_set(self):
        return self.redis.delete(self.key)


class TimeBasedSortedSet(SortedSet):
    def add_to_set(self, obj, score=None):
        # leave integer scores alone; they are intentional
        if score and not isinstance(score, int):
            if not isinstance(score, float):
                score = time.mktime(score.timetuple())        
        elif not score:
            score = time.time()
        self.redis.zadd(self.key, obj, score)

class NormalSet(RedisObject):
    key_format = 'normalset:%s'

    def __init__(self, object_id, redis=None):
        self.key = self.key_format % object_id
        super(NormalSet, self).__init__(redis)

    def set_key(self,obj):
        self.redis.set(self.key, obj)

    def add_to_set(self, obj):
        self.redis.sadd(self.key, obj)

    def remove_from_set(self, obj):
        self.redis.srem(self.key, obj)

    def get_random_member(self):
        return self.redis_slave.srandmember(self.key)
        
    def exists_in_set(self, obj):
        return self.redis_slave.sismember(self.key, obj)

    def get_set_count(self):
        return self.redis_slave.scard(self.key)

    def get_full_set(self):
        return self.redis_slave.smembers(self.key)

    def increment(self,increment=None):
        if not increment:
            increment = 1
        return self.redis.incrby(self.key,increment)

    def mget(self):
        return self.redis_slave.mget(self.key)

    def get(self, obj):
        return self.redis_slave.get(self.key, obj)

    def clear(self):
        self.redis.delete(self.key)