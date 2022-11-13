import json
from datetime import datetime
from rest_framework_jwt.settings import api_settings
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from hashids import Hashids
from xps_cloud.redis import RedisObject
from django.contrib.auth import get_user_model

# constrained alphanumeric set for hashid/serial
hashids = Hashids(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')

def jwt_response_payload_handler(token, user=None, request=None):
    from apps.user.serializers import UserSerializer

    return {
        'token': token,
        'user': UserSerializer(user, context={'request': request}).data
    }

def create_jwt(user):
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

    payload = jwt_payload_handler(user)
    return jwt_encode_handler(payload)

def get_hashid(hash_tuple):
    return hashids.encode(*hash_tuple)

def get_model_serial(model=None):
    try:
        return hashids.encode(ContentType.objects.get_for_model(model).pk, model.pk, int(datetime.timestamp(model.created)*1000))
    except Exception as e:
        pass
    return None

def decode_model_serial(hashid):
    return hashids.decode(hashid)

def api_serialize(serializer, to_fetch, options_arr=None):   
    ''' 
    utility to fetch one or many items from cache.
    assumptions: 
        1) single serializer per request
        2) len(options_arr) == len(to_fetch) if options_arr is present
        3) to_fetch is an array of primary keys to an object appropriate to the serializer

    '''
    User = get_user_model()
    redis = RedisObject().get_redis_connection(slave=True)
    pipe = redis.pipeline()

    single_fetch = True if not isinstance(to_fetch, (list, QuerySet)) else False
    # normalize all to_fetch objects as arrays
    to_fetch = to_fetch if isinstance(to_fetch, (list, QuerySet)) else [to_fetch]
    content_type_pk = ContentType.objects.get_for_model(serializer.Meta.model).pk

    for pk in to_fetch:
        cache_key = 'm:%s:%s' % (content_type_pk, int(pk))

        # # TESTING
        # redis.delete(cache_key)
        # # *******

        cache_class = serializer.cache_class
        pipe.hget(cache_key, cache_class)
    fetch_from_cache = pipe.execute()
            
    json_objs = [] # serialized objects
    
    # loop over the pks again, looking for matching fetch_from_cache objects
    # items that are missing cached json will need to be serialized
    # once serialized, updatee the dict with any additional (indexed) options, then 
    # add to json_objs response array
    for i, pk in enumerate(to_fetch):
        if fetch_from_cache[i]:
            serialized_obj = json.loads(fetch_from_cache[i])           
        else:
            serialized_obj = _api_serialize_object(serializer, pk)

        if serialized_obj:
            try:
                serialized_obj.update(options_arr[i])
            except Exception as e:
                pass
            json_objs.append(serialized_obj)

    if not json_objs:
        return []

    if single_fetch: # pass back just the single element if that's all we want
        return json_objs[0]
    return json_objs


def _api_serialize_object(serializer, pk):
    DEFAULT_CACHE_TIMEOUT = 86400
    redis = RedisObject().get_redis_connection()
    pipe = redis.pipeline()

    try:
        model_object = serializer.Meta.model.objects.get(pk=pk)
        serialized = serializer(model_object).data
        do_cache = serializer.do_cache

        if serialized:
            if do_cache:
                cache_key = 'm:%s:%s' % (ContentType.objects.get_for_model(serializer.Meta.model).pk, model_object.pk)
                cache_class = serializer.cache_class

                pipe.hset(cache_key, cache_class, json.dumps(serialized))
                pipe.expire(cache_key, DEFAULT_CACHE_TIMEOUT)
                pipe.execute()
            return serialized
    except Exception as e:
        print('oops - _api_serialize_object failed: %s' % e)
    return None

def invalidate(model):
    from apps.org.models import Feature, OrgFeature
    from apps.tracking.models import Activity, ActivityFav
    from apps.tracking.cache import ActivityFavSortedSet
    redis = RedisObject().get_redis_connection(slave=False)
    pipe = redis.pipeline()


    if isinstance(model, get_user_model()):
        # clear user's org member caches
        # TODO: ensure we can clear caches by org (not just deeply encoded get hash)

        # clear all OrgMember stats objects to which this activity may pertain
        org_member_objs = model.orgs.all()
        if org_member_objs:
            for om in org_member_objs:

                # org member sorted set (sorted on summary stats values)
                for key in redis.scan_iter('l:orgmember:%s:*' % om.org.pk):
                    redis.pipeline(redis.delete(key))
                # summary stats 
                redis.pipeline(redis.delete('stats:om:summary:%s' % om.pk))
                # dated stats sorted sets
                for key in redis.scan_iter('stats:om:dated:%s:*' % om.pk):
                    redis.pipeline(redis.delete(key))

    if isinstance(model, Feature):
        for key in redis.scan_iter('m:sorted:%s:*' % ContentType.objects.get_for_model(OrgFeature).pk):
            redis.pipeline(redis.delete(key))    

    if isinstance(model, Activity):
        redis.pipeline(ActivityFavSortedSet(model.user.pk).delete())
        # clear all activity sorted sets
        for key in redis.scan_iter('l:activity:*'):
            redis.pipeline(redis.delete(key))

        # clear all OrgMember stats objects to which this activity may pertain
        org_member_objs = model.user.orgs.all()
        if org_member_objs:
            for om in org_member_objs:

                # clear the OrgMember serialized model cache                
                redis.pipeline(redis.delete('m:%s:%s' % (ContentType.objects.get_for_model(om).pk, om.pk)))                

                # org member sorted set (sorted on summary stats values)
                for key in redis.scan_iter('l:orgmember:%s:*' % om.org.pk):
                    redis.pipeline(redis.delete(key))
                # summary stats 
                redis.pipeline(redis.delete('stats:om:summary:%s' % om.pk))
                # dated stats sorted sets
                for key in redis.scan_iter('stats:om:dated:%s:*' % om.pk):
                    redis.pipeline(redis.delete(key))
                # NOTE: regenerate stats caches?


    if isinstance(model, ActivityFav):
        redis.pipeline(ActivityFavSortedSet(model.user.pk).delete())
        # TODO: less heavy handed here
        for key in redis.scan_iter('m:sorted:%s:*' % ContentType.objects.get_for_model(Activity).pk):
            redis.pipeline(redis.delete(key))    

    content_type_pk = ContentType.objects.get_for_model(model).pk
    
    redis.delete('m:%s:%s' % (content_type_pk, model.pk))
    for key in redis.scan_iter('m:sorted:%s:*' % content_type_pk):
        redis.pipeline(redis.delete(key))    

    pipe.execute() 
